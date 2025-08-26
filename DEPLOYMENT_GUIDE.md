# 🚀 Atlas Deployment Guide

## 📦 Повне розгортання з нуля

### Автоматичне розгортання (рекомендовано)
```bash
# Завантажте Atlas
git clone https://github.com/Nimda-cloud/Atlas-mcp-1.git
cd Atlas-mcp-1

# Запустіть повне розгортання
./deploy_atlas.sh
```

### Опції розгортання
```bash
./deploy_atlas.sh                    # Повна установка (рекомендовано)
./deploy_atlas.sh --skip-python      # Пропустити Python залежності
./deploy_atlas.sh --skip-npm         # Пропустити NPM залежності  
./deploy_atlas.sh --quick            # Швидка установка (мінімум)
```

## 🔄 Оновлення існуючої установки

### Швидке оновлення
```bash
./update_atlas.sh                    # Стандартне оновлення
./update_atlas.sh --force            # Форсоване оновлення
./update_atlas.sh --mcp-only         # Тільки MCP компоненти
```

## 📋 Встановлювані компоненти

### 🐍 Python пакети (38+ пакетів)
- **Atlas Core**: fastapi, uvicorn, aiohttp, ollama, prometheus-client
- **MCP**: mcp, anthropic, openai  
- **TTS**: ukrainian-tts, gTTS
- **Automation**: pyautogui, pynput, pyobjc
- **AI/ML**: torch, transformers, numpy
- **Dev Tools**: black, flake8, pytest

### 📦 NPM пакети (6+ глобальних)
- **@modelcontextprotocol/inspector** - MCP налагодження
- **@modelcontextprotocol/server-github** - GitHub інтеграція
- **@playwright/mcp** - Офіційний Playwright MCP
- **better-playwright-mcp** - Покращений Playwright (29 інструментів)
- **playwright-mcp-chromium** - Chromium-based Playwright
- **@mcp-world/playwright-mcp-world** - Community Playwright tools

### 🔧 Go компоненти
- **atlas-mcp-proxy** - MCP агрегація сервер (порт 9090)

## 🏗️ Структура після розгортання

```
Atlas-mcp/
├── 🚀 deploy_atlas.sh              # Повне розгортання
├── 🔄 update_atlas.sh              # Швидке оновлення  
├── ▶️  start_atlas.sh               # Запуск Atlas
├── ⏹️  stop_atlas.sh                # Зупинка Atlas
├── 📄 requirements_complete.txt     # Python залежності
├── 🌍 .env                          # Конфігурація середовища
├── 📊 deployment.log               # Лог розгортання
├── ✅ .atlas_deployed              # Маркер успішного розгортання
│
├── atlas_venv/                     # Python середовище
├── mcp-proxy/                      # MCP Proxy конфігурації
│   ├── atlas-mcp-proxy            # Go executable
│   ├── atlas-global-config.json   # Основна конфігурація
│   └── atlas-config.json          # Базова конфігурація
│
├── mcp_tts_ukrainian/              # Ukrainian TTS сервер
├── mcp-task-orchestrator/          # Task Orchestrator
└── 3d_helmet_viewer/              # 3D Viewer (опційно)
```

## 🎯 Автозапуск після розгортання

```bash
# Після успішного deploy_atlas.sh:
./start_atlas.sh                    # Запуск всіх сервісів

# Перевірка статусу:
curl http://localhost:8000/         # Atlas статус
curl http://localhost:8000/tools    # Список інструментів (60+)
curl http://localhost:9090/health   # MCP Proxy статус
```

## 🛠️ Порти та сервіси

| Сервіс | Порт | Опис |
|--------|------|------|
| **Atlas Core API** | 8000 | Основний API, чат, TTS |
| **MCP Proxy** | 9090 | Агрегація всіх MCP сервісів |
| **Task Orchestrator** | 4006 | Управління завданнями |
| **3D Helmet Viewer** | 8080 | 3D візуалізація (опційно) |
| **Better Playwright** | 3001 | HTTP API для браузера |
| **Prometheus Metrics** | 8000/metrics | Моніторинг продуктивності |

## 📊 Моніторинг та метрики

### Prometheus метрики
```bash
# Перевірка метрик Atlas
curl http://localhost:8000/metrics

# Основні метрики:
# - atlas_requests_total - кількість HTTP запитів
# - atlas_request_latency_seconds - час відгуку запитів
```

## 🧪 Тестування установки

```bash
# Тест компонентів
curl -s http://localhost:8000/ | jq '.mcp_tools'

# Повинен показати:
{
  "total_tools": 60,
  "services": 5,
  "by_service": {
    "task-orchestrator": 15,
    "tts": 3, 
    "automation": 8,
    "playwright": 29,
    "web-fetch": 5
  }
}
```

## 🔧 Ручна установка (за потреби)

### 1. Системні залежності
```bash
# Homebrew (якщо немає)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.11+, Node.js, Go
brew install python@3.11 node go
```

### 2. Python середовище
```bash
python3 -m venv atlas_venv
source atlas_venv/bin/activate
pip install -r requirements_complete.txt
```

### 3. NPM залежності
```bash
npm install -g @modelcontextprotocol/inspector
npm install -g better-playwright-mcp
npm install -g @playwright/mcp
```

### 4. MCP Proxy
```bash
cd mcp-proxy
go install github.com/TBXark/mcp-proxy@latest
```

## 🆘 Вирішення проблем

### Проблема: Python імпорти не працюють
```bash
source atlas_venv/bin/activate
pip install --upgrade pip
pip install -r requirements_complete.txt
```

### Проблема: NPM пакети не знайдено
```bash
npm install -g better-playwright-mcp --force
npm cache clean --force
```

### Проблема: MCP Proxy не запускається
```bash
cd mcp-proxy
go build -o atlas-mcp-proxy .
chmod +x atlas-mcp-proxy
```

### Проблема: Порти зайняті
```bash
# Перевірити зайняті порти
lsof -i :8000,:9090,:4006,:8080

# Зупинити Atlas повністю
./stop_atlas.sh
```

## 📈 Результат успішного розгортання

✅ **92 інструменти** доступні через MCP  
✅ **6 активних сервісів** (TTS, Task Orchestrator, Automation, Playwright, AppleScript, Web-fetch)  
✅ **32 AppleScript інструменти** для нативної macOS автоматизації  
✅ **29 Playwright інструментів** для веб-автоматизації  
✅ **Автоматичний запуск** всіх компонентів  
✅ **Єдина точка входу** через Atlas Core API  

🎉 **Atlas готовий до роботи!**
