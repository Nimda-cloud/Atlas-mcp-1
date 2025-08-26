Ок, формую реалістичний покроковий план повністю нативної (macOS) інсталяції всіх зовнішніх MCP + об’єднання через потужний mcp-proxy в один endpoint для Atlas (3 LLM).  

## 0. Архітектурна модель

```
( macOS Host )
 ├─ applescript-mcp (peakmojo)         -> низькорівневий AppleScript / SSH / dual
 ├─ macos-automator-mcp (steipete)     -> високорівневі дії (Finder, Shortcuts)
 ├─ automation-mcp (ashwwwin)          -> файлові / системні / shell
 ├─ tts-mcp (blacktop) + ukrainian-tts -> озвучка (EN/UK)
 ├─ playwright-mcp (official)          -> browser automation
 ├─ (опц.) vnc mcp або fallback пізніше
 └─ mcp-proxy (TBXark full)            -> агрегує всі tools у єдиний MCP endpoint
             |
        Atlas (Docker або теж нативно)
```

Все встановлюється локально на macOS у власні каталоги /venv /node_modules, без модифікацій чужих репо (тільки конфіг). Atlas бачить лише один endpoint: `PROXY_MCP_URL`.

## 1. Каталоги та структура

```
~/mcp-stack/
  applescript-mcp/
  macos-automator-mcp/
  automation-mcp/
  tts-mcp/
  playwright-mcp/
  ukrainian-tts-test/ (опц. для перевірки моделей)
  proxy/
    config/mcp-proxy.json
    logs/
    keys/
  venvs/
    py-automator
    py-tts
    py-extra
```

## 2. Системні передумови

1. Увімкнути SSH: System Settings → General → Sharing → Remote Login (лише ваш користувач).
2. Надати Accessibility & Automation доступ (System Settings → Privacy & Security):
   - Terminal / iTerm / Runner (якщо через launchd)
   - (Опц.) Дозволити “Screen Recording” для VNC fallback у майбутньому.
3. Інсталювати:
   - Xcode CLT: `xcode-select --install`
   - Homebrew (якщо нема)
   - Node LTS: `brew install node`
   - Python 3.11+: `brew install python@3.11`
   - FFmpeg (для TTS іноді): `brew install ffmpeg`
4. SSH ключ для внутрішнього використання (якщо applescript-mcp буде в режимі remote/SSH):
   ```
   ssh-keygen -t ed25519 -f ~/mcp-stack/proxy/keys/macos_ed25519 -N ''
   cat ~/mcp-stack/proxy/keys/macos_ed25519.pub >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

## 3. Установка серверів

### 3.1 AppleScript MCP (peakmojo)
```
mkdir -p ~/mcp-stack/applescript-mcp
cd ~/mcp-stack/applescript-mcp
npm init -y
npm install @peakmojo/applescript-mcp
```
Тест:
```
npx @peakmojo/applescript-mcp --help
```

### 3.2 macos-automator-mcp (steipete)
```
cd ~/mcp-stack
git clone https://github.com/steipete/macos-automator-mcp.git
python3 -m venv ~/mcp-stack/venvs/py-automator
source ~/mcp-stack/venvs/py-automator/bin/activate
pip install -r macos-automator-mcp/requirements.txt  (або pip install .)
```
Тест (скрипт запуску з репо):
```
python macos-automator-mcp/main.py --port 4013
```

### 3.3 automation-mcp (ashwwwin)
```
cd ~/mcp-stack
git clone https://github.com/ashwwwin/automation-mcp.git
cd automation-mcp
npm install
# Перевірити команду запуску (з README), напр.:
npm run start -- --port 4014
```

### 3.4 tts-mcp (blacktop) + український TTS
```
cd ~/mcp-stack
git clone https://github.com/blacktop/mcp-tts.git tts-mcp
python3 -m venv ~/mcp-stack/venvs/py-tts
source ~/mcp-stack/venvs/py-tts/bin/activate
pip install -r tts-mcp/requirements.txt
pip install ukrainian-tts
```
Додати кастомний wrapper (напр. `tts_uk_adapter.py`) що:
- Реєструє додатковий tool `tts_uk` → використовує `ukrainian_tts` для синтезу у WAV → повертає base64.

(Можна реалізувати окремо після запуску базової версії.)

### 3.5 Official Playwright MCP
Офіційний репозиторій:
```
cd ~/mcp-stack
git clone https://github.com/microsoft/playwright-mcp.git
cd playwright-mcp
npm install
# Якщо передбачено старт:
npx playwright-mcp --port 4015
```
Якщо немає готового CLI — зробити маленький `index.js` що імпортує і стартує сервер (по README).

## 4. mcp-proxy (TBXark)

```
cd ~/mcp-stack
git clone https://github.com/TBXark/mcp-proxy.git proxy-src
cd proxy-src
npm install
```

Конфіг зібраний (використаємо ваш mcp-proxy.full.json, але адаптуємо під нативні порти):

`~/mcp-stack/proxy/config/mcp-proxy.json`:
```json
{
  "servers": [
    {
      "name": "applescript",
      "type": "process",
      "command": "npx",
      "args": [
        "@peakmojo/applescript-mcp",
        "--remoteHost", "127.0.0.1",
        "--remoteUser", "YOUR_USER",
        "--identityFile", "/absolute/path/to/mcp-stack/proxy/keys/macos_ed25519",
        "--strict"
      ],
      "restart": true
    },
    {
      "name": "automator",
      "type": "http",
      "endpoint": "http://127.0.0.1:4013/mcp",
      "namespace": "macos"
    },
    {
      "name": "automation",
      "type": "http",
      "endpoint": "http://127.0.0.1:4014/mcp",
      "namespace": "sys"
    },
    {
      "name": "tts",
      "type": "http",
      "endpoint": "http://127.0.0.1:4016/mcp",
      "namespace": "tts",
      "optional": true
    },
    {
      "name": "playwright",
      "type": "http",
      "endpoint": "http://127.0.0.1:4015/mcp",
      "namespace": "browser"
    }
  ],
  "proxy": {
    "port": 4010,
    "host": "127.0.0.1",
    "logLevel": "info",
    "cacheListToolsMs": 60000,
    "maxConcurrentCalls": 8,
    "requestTimeoutMs": 45000
  },
  "features": {
    "auditLog": {
      "enabled": true,
      "path": "/absolute/path/to/mcp-stack/proxy/logs/mcp-proxy-audit.log"
    },
    "namespacing": true,
    "fallback": {
      "enabled": true,
      "order": ["applescript", "automator", "browser"]
    }
  }
}
```

Запуск:
```
mkdir -p ~/mcp-stack/proxy/logs
node dist/index.js --config ~/mcp-stack/proxy/config/mcp-proxy.json
# або якщо є npm script:
npm run start -- --config ...
```

## 5. Інтеграція з Atlas

В Atlas .env:
```
ATLAS_MCP_SERVERS=proxy
ATLAS_MCP_PROXY_URL=http://host.docker.internal:4010/mcp
```
(Якщо Atlas теж нативно — можна прямо `http://127.0.0.1:4010/mcp`.)

У atlas_core.py при виявленні `ATLAS_MCP_PROXY_URL`:
- Формуємо єдиний endpoint.
- Робимо `list_tools` один раз при старті → кеш.

(У разі потреби потім зможу додати кодову зміну.)

## 6. Оркестрація / Автозапуск

Для кожного сервісу створити launchd plist (приклад для playwright):
`~/Library/LaunchAgents/com.mcp.playwright.plist`
(аналогічно для інших; залежності — спочатку запустити базові, далі proxy.)

Мінімізація колізій:
- Використати `ulimit -n 8192`
- Лог ротація (logrotate або простий cron скрипт).

## 7. Безпека

| Пункт | Дія |
|-------|-----|
| SSH доступ | Тільки ключ, без пароля |
| Порти | Bind 127.0.0.1 (крім якщо Atlas у Docker — тоді host.docker.internal все одно працює) |
| Логи | Audit у proxy + окремі файли per service |
| Оновлення | Вказати git SHA в текстовому файлі VERSION.lock |
| Обмеження | Використати `sandbox-exec` (опц.) для деяких сервісів |

## 8. Ukrainian TTS інтеграція (мінімальний адаптер концепт)

Псевдо (в `tts-mcp/custom_uk.py`):
```python
from ukrainian_tts import TTS
import base64, io

tts = TTS()

def synth_uk(text: str, voice: str = "ukrainian", speed: float = 1.0):
    wav = tts.tts(text, rate=speed)
    buf = io.BytesIO()
    wav.export(buf, format="wav")
    return base64.b64encode(buf.getvalue()).decode()
```
І реєстрація як MCP tool залежно від оригінальної структури (пізніше можу впровадити конкретно).

## 9. Тестовий сценарій

1. Запустити всі (manual або launchd)
2. `curl -s http://127.0.0.1:4010/mcp -d '{ "jsonrpc":"2.0","id":"1","method":"list_tools"}'`
3. Переконатися, що в переліку є:
   - `applescript.*`
   - `macos.*`
   - `sys.*`
   - `tts.*`
   - `browser.*`
4. Виконати тест:
   - AppleScript: відкрити калькулятор → закрити.
   - Playwright: відкрити сторінку + title.
   - TTS: синтез `Привіт світе`.

## 10. Ризики та пом’якшення

| Ризик | Мітігація |
|-------|----------|
| Зависання AppleScript | Таймаут + fallback через automator |
| Розрив процесу (node) | `restart: true` у proxy config |
| Вибух кількості інструментів | Префікси + кешування + фільтрація в Atlas |
| Конфлікти версій npm/pip | Окремі каталоги + не глобально ставити |
| Витік пам’яті Playwright | Періодичний recycle (cron kill/respawn) |
| Повільний старт list_tools | Кеш 60s у proxy |

## 11. Етапи впровадження

| Етап | Ціль | Результат |
|------|-----|-----------|
| 1 | Базові сервіси (applescript, automator) | AppleScript OK |
| 2 | Додати automation, playwright | Системні + браузерні інструменти |
| 3 | Додати TTS + український | Голосові інструменти |
| 4 | mcp-proxy + audit | Єдиний endpoint |
| 5 | Інтеграція з Atlas | Atlas працює від одного MCP |
| 6 | Оптимізація (launchd, лог ротейт) | Продакшн стабільність |
| 7 (опц.) | VNC fallback | Pixel-level automation |

## 12. Що можу зробити наступним кроком
- Підготувати шаблон launchd plist для кожного.
- Скелет адаптера `tts_uk`.
- Невеликий health-check скрипт `scripts/check_mcp_stack.py`.
- Патч у README.md з розділом “Native macOS MCP stack”.

Напиши, що з цього генерувати першим: (1) launchd, (2) tts_uk адаптер, (3) README секція, (4) health checker — або всі разом.  

Що обираєш?