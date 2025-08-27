# 📚 Atlas MCP Documentation

Ця папка містить повну документацію для Atlas MCP системи з 92 інструментами.

## 📖 Основна документація

### 🚀 Розгортання та установка
- **[📖 Deployment Guide](DEPLOYMENT_GUIDE.md)** - Детальні інструкції розгортання системи
- **[📋 Components Checklist](DEPLOYMENT_COMPONENTS_CHECKLIST.md)** - Перевірочний список всіх компонентів
- **[📋 Installation Summary](INSTALLATION_SUMMARY.md)** - Підсумок установки та конфігурації

### 📊 Моніторинг та статус
- **[🎯 Status Report](DEPLOYMENT_STATUS_REPORT.md)** - Поточний статус системи та компонентів
- **[📊 Prometheus Integration](PROMETHEUS_INTEGRATION_SUMMARY.md)** - Інтеграція системи моніторингу

### 🔧 Інтеграції та аналіз
- **[📊 MCP Tools Discovery](MCP_TOOLS_DISCOVERY_REPORT.md)** - Детальний аналіз виявлення інструментів
- **[🎉 Playwright Integration](PLAYWRIGHT_MCP_SUCCESS_REPORT.md)** - Успішна інтеграція Better Playwright MCP

## 🏗️ Архітектура системи

Atlas MCP - це enterprise-ready система з:

- **92 інструменти** у 6 активних сервісах
- **AppleScript MCP** - 32 native macOS automation tools  
- **Better Playwright** - 29 веб-автоматизація tools
- **Task Orchestrator** - 15 planning & execution tools
- **Atlas Automation** - 8 core automation tools
- **Web Fetch MCP** - 5 web content tools
- **TTS Ukrainian** - 3 text-to-speech tools

## 🛠️ Компоненти системи

### Core Services
1. **Atlas Core** (`atlas_core.py`) - Основний HTTP API сервер
2. **Task Orchestrator** (`task_orchestrator_http_server.py`) - Планування та виконання
3. **AppleScript MCP** - macOS automation через TypeScript
4. **Better Playwright** - Веб-автоматизація через Node.js  
5. **Web Fetch MCP** - HTTP content fetching
6. **TTS Ukrainian** - Українське text-to-speech

### Infrastructure
- **MCP Proxy** - Агрегація всіх MCP сервісів
- **Prometheus Metrics** - HTTP API моніторинг
- **Auto-deployment** - Повна автоматизація розгортання
- **Health Checks** - Система валідації компонентів

## 🔄 Lifecycle Commands

```bash
# Повне розгортання системи
./deploy_atlas.sh

# Оновлення існуючої системи  
./update_atlas.sh

# Запуск всіх сервісів
./start_atlas.sh

# Зупинка всіх сервісів
./stop_atlas.sh

# Валідація MCP серверів
make validate-mcp
```

## 📊 Моніторинг

### API Endpoints
- `http://localhost:8000/` - Atlas Core API
- `http://localhost:8000/tools` - Список всіх 92 інструментів
- `http://localhost:8000/metrics` - Prometheus метрики
- `http://localhost:4006/` - Task Orchestrator API

### Metrics
- `atlas_requests_total` - Загальна кількість HTTP запитів
- `atlas_request_latency_seconds` - Латентність запитів

## 🤝 Contributing

Для додавання нових MCP сервісів:
1. Додати до `deploy_atlas.sh` - автоматична установка
2. Оновити `atlas-global-config.json` - конфігурація MCP Proxy
3. Модифікувати `atlas_core.py` - автодетекція інструментів

---

**Atlas MCP v2.0** - Production Ready Enterprise System! 🚀
