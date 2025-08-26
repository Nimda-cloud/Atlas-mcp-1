# Полностью Нативный MCP Стек - План Развертывания (Оригінальні Сервери)

## Архитектурная Цель

```
macOS Host (нативно) - ОРИГІНАЛЬНІ MCP СЕРВЕРИ
├── applescript-mcp (stdio/http) - peakmojo/applescript-mcp
├── macos-automator-mcp (stdio) - steipete/macos-automator-mcp 
├── automation-mcp (stdio/http) - ashwwwin/automation-mcp
├── playwright-mcp (stdio) - Microsoft/playwright-mcp
├── tts-mcp (http) - hmage/mcp-tts 
├── mcp-vnc (stdio/http) - hrrrsn/mcp-vnc
└── mcp-proxy (TBXark) → Flexible Configuration
    ├── stdio servers (для підтримуючих)
    ├── http servers (для тих що тільки http)
    ├── sse support
    └── streamable-http → единый HTTP endpoint :4010
                ↓
           Atlas (Docker або нативно)
```

**Ключевые принципы:**
- Оригінальні MCP сервери без модифікацій
- TBXark proxy з гнучкою конфігурацією (stdio/http/sse)
- Автоматичне визначення типу підключення
- Fallback chain для різних протоколів
- Простое управление через launchd

## Этап 1: Подготовка Системы

### 1.1 Системные зависимости
```bash
# Homebrew + базовые пакеты
brew install node@22 python@3.12 ffmpeg

# SSH для AppleScript (внутренний)
ssh-keygen -t ed25519 -f ~/.ssh/mcp_internal -N ''
cat ~/.ssh/mcp_internal.pub >> ~/.ssh/authorized_keys

# Права доступа для автоматизации
# System Settings → Privacy & Security → Automation
# System Settings → Privacy & Security → Accessibility
```

### 1.2 Структура каталогов
```bash
mkdir -p ~/mcp-stack/{applescript,automator,automation,playwright,tts,vnc,proxy}/{logs,config}
mkdir -p ~/mcp-stack/proxy/{keys,cache}
mkdir -p ~/mcp-stack/venvs
```

## Этап 2: Установка MCP Серверов

### 2.1 AppleScript MCP (peakmojo)
```bash
cd ~/mcp-stack/applescript
npm init -y
npm install @peakmojo/applescript-mcp

# Тест stdio режима
echo '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test"}}}' | npx @peakmojo/applescript-mcp
```

### 2.2 macOS Automator MCP (steipete)
```bash
cd ~/mcp-stack/automator
git clone https://github.com/steipete/macos-automator-mcp.git src
python3 -m venv ../venvs/automator
source ../venvs/automator/bin/activate
pip install -r src/requirements.txt

# Проверка stdio поддержки (может потребоваться адаптация)
python src/main.py --help
```

### 2.3 Automation MCP (ashwwwin)
```bash
cd ~/mcp-stack/automation
git clone https://github.com/ashwwwin/automation-mcp.git src
cd src && npm install

# Проверка stdio режима
node index.js --help
```

### 2.4 Playwright MCP (Microsoft Official)
```bash
cd ~/mcp-stack/playwright
git clone https://github.com/microsoft/playwright-mcp.git src
cd src && npm install
npx playwright install

# Адаптация для stdio (может потребоваться wrapper)
node dist/index.js --help
```

### 2.5 TTS MCP + Ukrainian Extension
```bash
cd ~/mcp-stack/tts
git clone https://github.com/blacktop/mcp-tts.git src
python3 -m venv ../venvs/tts
source ../venvs/tts/bin/activate
pip install -r src/requirements.txt
pip install ukrainian-tts

# Создание украинского адаптера
cat > src/ukrainian_adapter.py << 'EOF'
import json
from ukrainian_tts import TTS
import base64
import io

uk_tts = TTS()

def register_ukrainian_tool():
    return {
        "name": "tts_ukrainian",
        "description": "Synthesize Ukrainian speech from text",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Ukrainian text to synthesize"},
                "speed": {"type": "number", "default": 1.0, "minimum": 0.5, "maximum": 2.0}
            },
            "required": ["text"]
        }
    }

def execute_ukrainian_tts(text: str, speed: float = 1.0):
    try:
        wav = uk_tts.tts(text, rate=speed)
        buf = io.BytesIO()
        wav.export(buf, format="wav")
        return {
            "content": [
                {"type": "text", "text": f"Synthesized Ukrainian audio for: {text}"},
                {"type": "resource", "resource": {"uri": f"data:audio/wav;base64,{base64.b64encode(buf.getvalue()).decode()}"}}
            ]
        }
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}
EOF
```

### 2.6 VNC MCP (hrrrsn)
```bash
cd ~/mcp-stack/vnc
npm init -y
npm install @hrrrsn/mcp-vnc

# Тест локального VNC (Screen Sharing должен быть включен)
echo '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test"}}}' | VNC_HOST=127.0.0.1 VNC_PORT=5900 npx @hrrrsn/mcp-vnc
```

## Этап 3: MCP Proxy Setup

### 3.1 Установка TBXark mcp-proxy
```bash
cd ~/mcp-stack/proxy
git clone https://github.com/TBXark/mcp-proxy.git src
cd src && npm install && npm run build
```

### 3.2 Конфигурация полностью stdio
```bash
cat > ~/mcp-stack/proxy/config/native-stdio.json << 'EOF'
{
  "description": "Полностью нативный MCP стек - только stdio процессы",
  "servers": [
    {
      "name": "applescript",
      "type": "stdio",
      "command": "npx",
      "args": ["@peakmojo/applescript-mcp"],
      "cwd": "/Users/$USER/mcp-stack/applescript",
      "env": {
        "SSH_IDENTITY_FILE": "/Users/$USER/.ssh/mcp_internal",
        "REMOTE_HOST": "127.0.0.1",
        "REMOTE_USER": "$USER"
      },
      "namespace": "as",
      "restart": true,
      "timeout": 30000
    },
    {
      "name": "automator", 
      "type": "stdio",
      "command": "/Users/$USER/mcp-stack/venvs/automator/bin/python",
      "args": ["/Users/$USER/mcp-stack/automator/src/main.py"],
      "namespace": "macos",
      "restart": true
    },
    {
      "name": "automation",
      "type": "stdio", 
      "command": "node",
      "args": ["index.js"],
      "cwd": "/Users/$USER/mcp-stack/automation/src",
      "namespace": "sys",
      "restart": true
    },
    {
      "name": "playwright",
      "type": "stdio",
      "command": "node", 
      "args": ["dist/index.js"],
      "cwd": "/Users/$USER/mcp-stack/playwright/src",
      "namespace": "browser",
      "restart": true,
      "timeout": 45000
    },
    {
      "name": "tts",
      "type": "stdio",
      "command": "/Users/$USER/mcp-stack/venvs/tts/bin/python",
      "args": ["/Users/$USER/mcp-stack/tts/src/main.py"],
      "namespace": "voice",
      "restart": true,
      "optional": true
    },
    {
      "name": "vnc_local",
      "type": "stdio",
      "command": "npx",
      "args": ["@hrrrsn/mcp-vnc"],
      "cwd": "/Users/$USER/mcp-stack/vnc",
      "env": {
        "VNC_HOST": "127.0.0.1",
        "VNC_PORT": "5900"
      },
      "namespace": "vnc",
      "restart": true,
      "optional": true
    }
  ],
  "proxy": {
    "port": 4010,
    "host": "127.0.0.1",
    "logLevel": "info",
    "maxConcurrentCalls": 12,
    "requestTimeoutMs": 60000
  },
  "features": {
    "namespacing": true,
    "toolAlias": {
      "browser.screenshot": "page_screenshot",
      "vnc.vnc_screenshot": "desktop_screenshot",
      "voice.tts_ukrainian": "speak_ukrainian"
    },
    "fallback": {
      "enabled": true,
      "order": ["as", "macos", "browser", "vnc_local"]
    },
    "auditLog": {
      "enabled": true,
      "path": "/Users/$USER/mcp-stack/proxy/logs/audit.log",
      "rotation": {
        "maxSize": "10MB",
        "maxFiles": 5
      }
    }
  }
}
EOF
```

### 3.3 Запуск proxy
```bash
cd ~/mcp-stack/proxy/src
node dist/index.js --config ../config/native-stdio.json
```

## Этап 4: Интеграция с Atlas

### 4.1 Модификация atlas_core.py
```python
# В atlas_core.py добавить поддержку единого proxy endpoint
ATLAS_MCP_PROXY_MODE = os.getenv('ATLAS_MCP_PROXY_MODE', 'false').lower() == 'true'
ATLAS_MCP_PROXY_URL = os.getenv('ATLAS_MCP_PROXY_URL', 'http://127.0.0.1:4010')

async def load_mcp_config_proxy_mode():
    """Загрузка конфигурации в режиме единого proxy"""
    try:
        # Получаем полный список tools через proxy
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "id": "atlas_init",
                "method": "list_tools"
            }
            async with session.post(ATLAS_MCP_PROXY_URL, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    tools = result.get('result', {}).get('tools', [])
                    logger.info(f"Loaded {len(tools)} tools from MCP proxy")
                    return {"proxy": {"url": ATLAS_MCP_PROXY_URL, "tools": tools}}
    except Exception as e:
        logger.error(f"Failed to connect to MCP proxy: {e}")
        return {}
```

### 4.2 Environment настройки
```bash
# В .env Atlas
ATLAS_MCP_PROXY_MODE=true
ATLAS_MCP_PROXY_URL=http://127.0.0.1:4010

# Если Atlas в Docker
ATLAS_MCP_PROXY_URL=http://host.docker.internal:4010
```

## Этап 5: Автозапуск через launchd

### 5.1 MCP Proxy Service
```bash
cat > ~/Library/LaunchAgents/com.atlas.mcp-proxy.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.atlas.mcp-proxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>node</string>
        <string>dist/index.js</string>
        <string>--config</string>
        <string>../config/native-stdio.json</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/$USER/mcp-stack/proxy/src</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/$USER/mcp-stack/proxy/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/$USER/mcp-stack/proxy/logs/stderr.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.atlas.mcp-proxy.plist
```

## Этап 6: Тестирование и Валидация

### 6.1 Health Check Script
```bash
cat > ~/mcp-stack/scripts/health_check.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import sys

async def check_proxy_health():
    try:
        async with aiohttp.ClientSession() as session:
            # Test list_tools
            payload = {"jsonrpc": "2.0", "id": "health", "method": "list_tools"}
            async with session.post("http://127.0.0.1:4010", json=payload, timeout=10) as resp:
                if resp.status != 200:
                    return False, f"HTTP {resp.status}"
                
                result = await resp.json()
                tools = result.get('result', {}).get('tools', [])
                
                # Check expected namespaces
                namespaces = set()
                for tool in tools:
                    if '.' in tool['name']:
                        namespaces.add(tool['name'].split('.')[0])
                
                expected = {'as', 'macos', 'sys', 'browser', 'voice', 'vnc'}
                missing = expected - namespaces
                
                if missing:
                    return False, f"Missing namespaces: {missing}"
                
                return True, f"OK: {len(tools)} tools, namespaces: {sorted(namespaces)}"
                
    except Exception as e:
        return False, f"Error: {e}"

async def main():
    success, message = await check_proxy_health()
    print(f"MCP Proxy Health: {message}")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x ~/mcp-stack/scripts/health_check.py
```

### 6.2 Функциональное тестирование
```bash
# Тест AppleScript
curl -s http://127.0.0.1:4010 -d '{"jsonrpc":"2.0","id":"test","method":"call_tool","params":{"name":"as.run_applescript","arguments":{"script":"tell application \"Calculator\" to activate"}}}'

# Тест Browser 
curl -s http://127.0.0.1:4010 -d '{"jsonrpc":"2.0","id":"test","method":"call_tool","params":{"name":"browser.navigate","arguments":{"url":"https://example.com"}}}'

# Тест VNC Screenshot
curl -s http://127.0.0.1:4010 -d '{"jsonrpc":"2.0","id":"test","method":"call_tool","params":{"name":"vnc.vnc_screenshot","arguments":{}}}'

# Тест Ukrainian TTS
curl -s http://127.0.0.1:4010 -d '{"jsonrpc":"2.0","id":"test","method":"call_tool","params":{"name":"voice.tts_ukrainian","arguments":{"text":"Привіт світе"}}}'
```

## Этап 7: Мониторинг и Логирование

### 7.1 Простой метрики сборщик (без Prometheus)
```bash
cat > ~/mcp-stack/scripts/metrics_collector.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import time
from pathlib import Path

async def collect_metrics():
    metrics = {
        "timestamp": int(time.time()),
        "proxy_status": "unknown",
        "tools_count": 0,
        "response_time_ms": 0
    }
    
    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"jsonrpc": "2.0", "id": "metrics", "method": "list_tools"}
            async with session.post("http://127.0.0.1:4010", json=payload, timeout=5) as resp:
                metrics["response_time_ms"] = int((time.time() - start_time) * 1000)
                
                if resp.status == 200:
                    result = await resp.json()
                    tools = result.get('result', {}).get('tools', [])
                    metrics["proxy_status"] = "ok"
                    metrics["tools_count"] = len(tools)
                else:
                    metrics["proxy_status"] = f"http_{resp.status}"
                    
    except Exception as e:
        metrics["proxy_status"] = f"error: {str(e)}"
        metrics["response_time_ms"] = int((time.time() - start_time) * 1000)
    
    # Append to metrics file
    metrics_file = Path("~/mcp-stack/proxy/logs/metrics.jsonl").expanduser()
    with open(metrics_file, "a") as f:
        f.write(json.dumps(metrics) + "\n")
    
    return metrics

if __name__ == "__main__":
    result = asyncio.run(collect_metrics())
    print(json.dumps(result, indent=2))
EOF

# Cron job для метрик (каждые 5 минут)
echo "*/5 * * * * /usr/bin/python3 $HOME/mcp-stack/scripts/metrics_collector.py" | crontab -
```

## Этап 8: Бэкап и Восстановление

### 8.1 Бэкап конфигурации
```bash
cat > ~/mcp-stack/scripts/backup_config.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/mcp-stack/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Конфигурации
cp -r "$HOME/mcp-stack/proxy/config" "$BACKUP_DIR/"
cp "$HOME/Library/LaunchAgents/com.atlas.mcp-proxy.plist" "$BACKUP_DIR/"

# Ключи и сертификаты
cp -r "$HOME/.ssh/mcp_internal*" "$BACKUP_DIR/" 2>/dev/null || true

# Логи (последние 100 строк)
tail -100 "$HOME/mcp-stack/proxy/logs/audit.log" > "$BACKUP_DIR/recent_audit.log" 2>/dev/null || true

echo "Backup created: $BACKUP_DIR"
EOF

chmod +x ~/mcp-stack/scripts/backup_config.sh
```

## Результат

После выполнения всех этапов получаем:

1. **Единый endpoint**: `http://127.0.0.1:4010` для Atlas
2. **Нулевые внутренние порты**: все MCP серверы как stdio процессы  
3. **Полная изоляция**: каждый MCP в отдельном процессе
4. **Автозапуск**: через launchd при загрузке системы
5. **Мониторинг**: health checks + простые метрики
6. **Namespace isolation**: as.*, macos.*, sys.*, browser.*, voice.*, vnc.*
7. **Fallback chain**: при отказе сервиса автопереключение
8. **Украинский TTS**: встроен в voice namespace
9. **VNC поддержка**: локальный + возможность удалённых десктопов

**Сетевые порты минимизированы до:**
- 4010: MCP Proxy (единственный HTTP)
- 5900: VNC Screen Sharing (системный, не MCP)

Все остальное — процессы stdio без портов.
