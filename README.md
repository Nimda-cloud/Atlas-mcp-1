# 🚀 Atlas MCP - Advanced Automation System

**Atlas MCP** - це потужна система автоматизації з підтримкою Model Context Protocol (MCP).

**Інструменти:**

- **92 активних** у поточному direct режимі (без повного proxy агрегування)
- **107 доступних всього** при ввімкненому MCP Proxy (повний реєстр див. `LOGIC.md`)

Детальна інтелектуальна логіка та архітектурні оновлення: див. **[`LOGIC.md`](./LOGIC.md)** (канонічний документ).

Архівні історичні файли логіки переміщено до `docs/archive/` (файли `LOGIC_old`, `LOGIC2`, `LOGIC_NEW`).

## ⚡ Quick Start

### 🆕 Нова установка (One Command Deploy)

```bash
# Клонування і повне розгортання
git clone https://github.com/Nimda-cloud/Atlas-mcp-1.git
cd Atlas-mcp-1

# Повна автоматична установка всіх компонентів
./deploy_atlas.sh

# Запуск Atlas
./start_atlas.sh
```

### 🔄 Існуюча установка

```bash
# Швидке оновлення всіх компонентів
./update_atlas.sh

# Запуск системи
./start_atlas.sh

# Зупинка всіх сервісів
./stop_atlas.sh
```

### 🛠️ Makefile Commands (Рекомендовано)

```bash
make deploy          # Повне розгортання
make update          # Оновлення компонентів
make start           # Запуск системи
make stop            # Зупинка системи
make status          # Статус сервісів
make validate-mcp    # Валідація MCP серверів
make tools-count     # Кількість інструментів
make help            # Всі доступні команди
```

## 🎯 Поточний стан: 92 інструменти активні

| Сервіс | Інструменти | Опис | Статус |
|--------|-------------|------|---------|
| **AppleScript MCP** | 32 | macOS автоматизація (Calendar, Finder, Messages, etc.) | ✅ Active |
| **Better Playwright** | 29 | Веб-автоматизація, скріншоти, браузер | ✅ Active |
| **Task Orchestrator** | 15 | Планування завдань, виконання | ✅ Active |
| **Automation** | 8 | Миша, клавіатура, файлові операції | ✅ Active |
| **Web Fetch** | 5 | HTTP запити, парсинг веб-сторінок | ✅ Active |
| **TTS Ukrainian** | 3 | Українське озвучування тексту | ✅ Active |
| **ЗАГАЛОМ** | **92** | **Full automation suite** | ✅ **184% від початкової мети!** |

## 🌐 API Endpoints

### Core Atlas API (Port 8000)

| Призначення | URL | Метод |
|-------------|-----|-------|
| Статус системи | `http://localhost:8000/` | GET |
| Список інструментів | `http://localhost:8000/tools` | GET |
| Чат API | `http://localhost:8000/chat` | POST |
| Виконання дій | `http://localhost:8000/action` | POST |
| Prometheus метрики | `http://localhost:8000/metrics` | GET |
| Оновлення інструментів | `http://localhost:8000/tools/refresh` | POST |

### MCP Proxy (Port 9090)

| Сервіс | URL | Опис |
|--------|-----|------|
| Health Check | `http://localhost:9090/health` | Статус MCP Proxy |
| Task Orchestrator | `http://localhost:4006/tools` | Управління завданнями |

## 📦 Автоматично встановлювані компоненти

### � Python Environment

- **Core Dependencies**: fastapi, uvicorn, aiohttp, ollama, **prometheus-client**
- **MCP Libraries**: mcp, anthropic, openai
- **TTS & Audio**: ukrainian-tts, gTTS, pygame  
- **Automation**: pyautogui, pynput, pyobjc (macOS)
- **AI/ML**: torch, transformers, numpy, scipy
- **Development**: black, flake8, pytest

### � NPM Global Packages  

- **@modelcontextprotocol/inspector** - MCP debugging
- **@modelcontextprotocol/server-github** - GitHub integration
- **better-playwright-mcp** - Advanced web automation (29 tools)
- **@playwright/mcp** - Official Playwright MCP
- **playwright-mcp-chromium** - Chromium browser support

### � AppleScript MCP Server

- **TypeScript-based enterprise architecture**
- **32 native macOS tools**: Calendar, Clipboard, Finder, Notifications, System controls, iTerm, Mail, Messages, Notes, Pages, Shortcuts
- **Modular component system**

### 🔧 Go Components

- **atlas-mcp-proxy** - MCP services aggregation server

## 📊 Моніторинг та продуктивність

### Prometheus Integration
Atlas включає професійний моніторинг через Prometheus:

```bash
# Перевірка метрик системи
curl http://localhost:8000/metrics

# Основні метрики:
# atlas_requests_total - кількість HTTP запитів
# atlas_request_latency_seconds - час відгуку
```

### Порти сервісів
- **8000** - Atlas Core API + Prometheus metrics
- **9090** - MCP Proxy (агрегація сервісів)  
- **4006** - Task Orchestrator
- **8080** - 3D Helmet Viewer (опційно)
- **3001** - Better Playwright HTTP API

## 🚀 Архітектура системи

Atlas MCP працює в **MCP Proxy режимі** для оптимальної продуктивності:

1. **Atlas Core** - центральний API і 3-агентна система
2. **MCP Proxy** - агрегує всі MCP сервіси в єдиний endpoint
3. **Спеціалізовані MCP сервери** - кожен надає специфічні інструменти
4. **Автодетекція інструментів** - динамічне виявлення доступних можливостей

## 🔄 Lifecycle Management

### Deploy & Update Automation

```bash
# Повне розгортання з нуля (створює всі компоненти)
./deploy_atlas.sh

# Швидке оновлення (оновлює існуючі компоненти)  
./update_atlas.sh

# Валідація системи
make validate-mcp
```

### Environment Configuration
Atlas автоматично конфігурує:
- Python віртуальне середовище (`atlas_venv/`)
- NPM глобальні пакети
- Go executable компіляція
- MCP сервіси конфігурація
- Prometheus моніторинг

## 📚 Документація

Повна документація знаходиться в папці **`docs/`**:

- **[📖 Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Детальні інструкції розгортання
- **[📋 Components Checklist](docs/DEPLOYMENT_COMPONENTS_CHECKLIST.md)** - Перевірочний список компонентів
- **[🎯 Status Report](docs/DEPLOYMENT_STATUS_REPORT.md)** - Поточний статус системи
- **[📊 MCP Tools Discovery](docs/MCP_TOOLS_DISCOVERY_REPORT.md)** - Аналіз виявлення інструментів
- **[🎉 Playwright Integration](docs/PLAYWRIGHT_MCP_SUCCESS_REPORT.md)** - Успішна інтеграція Playwright
- **[📊 Prometheus Integration](docs/PROMETHEUS_INTEGRATION_SUMMARY.md)** - Інтеграція моніторингу
- **[📋 Installation Summary](docs/INSTALLATION_SUMMARY.md)** - Підсумок установки
- **[🧠 System Logic (Canonical)](LOGIC.md)** - Актуальна інтелектуальна архітектура
- **[🗂 Архів логічних версій](docs/archive/)** - Історичні файли (`LOGIC_old`, `LOGIC2`, `LOGIC_NEW`)

## 🧪 Тестування після установки

```bash
# Перевірка статусу системи
curl http://localhost:8000/ | jq

# Перевірка кількості інструментів (має бути 92)
curl http://localhost:8000/tools | jq '.total_tools'

# Валідація MCP серверів
make validate-mcp

# Перевірка Prometheus метрик  
curl http://localhost:8000/metrics | grep atlas_requests_total
```

## 🆘 Вирішення проблем

### Проблема: Python imports не працюють

```bash
source atlas_venv/bin/activate
pip install -r requirements.txt
```

### Проблема: NPM пакети не знайдено

```bash
npm install -g better-playwright-mcp --force
npm cache clean --force
```

### Проблема: MCP сервери не запускаються

```bash
make validate-mcp
./stop_atlas.sh && ./start_atlas.sh
```

### Проблема: Порти зайняті

```bash
# Перевірити зайняті порти
lsof -i :8000,:9090,:4006

# Повна зупинка Atlas
./stop_atlas.sh
```

## 📈 Результати розгортання

✅ **92 інструменти** доступні через MCP Protocol  
✅ **6 активних сервісів** з автодетекцією  
✅ **Prometheus моніторинг** HTTP API  
✅ **AppleScript MCP** - 32 native macOS tools  
✅ **Better Playwright** - 29 веб-автоматизація tools  
✅ **One-command deployment** з повною автоматизацією  
✅ **Професійна архітектура** з enterprise-ready компонентами  

## 🤝 Contributing

Atlas MCP використовує модульну архітектуру - додавання нових MCP серверів простіше за додаванням до:
1. **deploy_atlas.sh** - автоматична установка
2. **atlas-global-config.json** - конфігурація MCP Proxy  
3. **atlas_core.py** - автодетекція інструментів

## 📄 License

[MIT License](LICENSE) - Використовуйте вільно в комерційних та особистих проектах.

---

**Atlas MCP v2.0** - Ready for Production! 🚀

*Automated deployment • 92 tools • 6 services • Enterprise monitoring • macOS native automation*

### Active Components (Minimal Mode)

- **Atlas Core**: multi-agent orchestration, Ukrainian TTS
- **Task Orchestrator**: planning + tool execution (port 4006)
- **3D Helmet Viewer** (optional): static HTML/JS, runs via simple HTTP server

MCP Proxy режим зараз вимкнений (прямий режим). Увімкнути можна через `ATLAS_MCP_PROXY_MODE=true` та відповідні URL.

### CORS Configuration (для браузерного viewer)

```bash
export ATLAS_ENABLE_CORS=1
export ATLAS_ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
./start_atlas.sh --viewer
```

Якщо CORS не ввімкнено, браузерні fetch запити можуть бути заблоковані.

### Manual Start (Advanced)

```bash
# (optional) activate venv
source atlas_venv/bin/activate

# Task Orchestrator
python3 task_orchestrator_http_server.py &

# Atlas Core (direct MCP mode)
python3 atlas_core.py &

# Viewer static server (port 8080)
cd 3d_helmet_viewer && python3 -m http.server 8080 &
```

### Stopping Services

```bash
./stop_atlas.sh
```


### Log Files

| Component          | Log file                   |
| ------------------ | -------------------------- |
| Atlas Core         | /tmp/atlas_core.log        |
| Task Orchestrator  | /tmp/task_orchestrator.log |
| Viewer (optional)  | /tmp/atlas_viewer.log      |
| MCP Proxy          | /tmp/mcp_proxy.log         |

## MCP Proxy (Variant B)

Atlas включає вбудований MCP Proxy сервер для агрегації множини MCP клієнтів через єдиний HTTP endpoint.

### Увімкнення MCP Proxy

```bash
export ATLAS_MCP_PROXY_MODE=true
export ATLAS_MCP_PROXY_URL=http://localhost:9090
export ATLAS_MCP_PROXY_CLIENTS=tts:sse,automation:stdio,playwright:streamable-http,task-orchestrator:sse
./start_atlas.sh
```

### Конфігурація клієнтів

MCP Proxy підтримує:

- **stdio**: команди (npx, python)
- **sse**: Server-Sent Events HTTP endpoints
- **streamable-http**: HTTP streaming MCP endpoints

Конфіг файл: `mcp-proxy/atlas-config.json`

### Endpoints при увімкненому Proxy

- `http://localhost:9090/` - базовий proxy
- `http://localhost:9090/{service}/sse` - для sse клієнтів
- `http://localhost:9090/{service}/mcp` - для streamable-http клієнтів

### Прямий запуск Proxy

```bash
cd mcp-proxy
# Базова Atlas конфігурація
./start-atlas-proxy.sh

# Глобальна конфігурація всіх MCP сервісів
./start-atlas-proxy.sh --global
# або
export ATLAS_MCP_USE_GLOBAL_CONFIG=true
./start-atlas-proxy.sh
```

### Глобальна MCP Конфігурація

Файл `mcp-proxy/atlas-global-config.json` містить повну конфігурацію всіх Atlas MCP сервісів:

- **atlas-tts-ukrainian** - Ukrainian TTS сервіс
- **atlas-task-orchestrator** - SSE оркестратор
- **atlas-automation-mcp** - Stdio автоматизація
- **atlas-core-api** - Core API через HTTP
- **atlas-3d-viewer** - 3D Viewer HTTP endpoint
- **github-integration** - GitHub MCP сервіс
- **web-fetch** - Fetch MCP сервіс
- **atlas-playwright** - Browser automation

### Порт стандартизація

Всі компоненти тепер використовують стандартизовані порти:

- **9090** - MCP Proxy (раніше 4010)
- **8000** - Atlas Core API
- **4006** - Task Orchestrator
- **8080** - 3D Helmet Viewer
- **3000** - Playwright (якщо використовується)

### Additional Notes

- UI терміналний інтерфейс видалено; API-first архітектура.
- 3D Viewer ізольовано і може еволюціонувати незалежно.
- Додаткові MCP сервіси можна додати через `ATLAS_MCP_SERVERS` (direct mode) або `ATLAS_MCP_PROXY_CLIENTS` (proxy mode).
- Глобальна конфігурація підтримує tool filtering і auth tokens для кожного сервісу.
 
