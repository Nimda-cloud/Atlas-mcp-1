# 🧠 Task Orchestrator Installation Guide

## 📋 Огляд

MCP Task Orchestrator - це інтелектуальна система планування і виконання завдань, що надає 32 спеціалізованих інструменти для:
- **Планування завдань** з розбивкою на підзадачі
- **Спеціалізовані AI ролі** (Architect, Implementer, Tester, Documenter)
- **Управління сесіями** з персистентною пам'яттю
- **Синтез результатів** та автоматичну документацію

## 🚀 Автоматичне встановлення (Рекомендовано)

Task Orchestrator автоматично встановлюється разом з Atlas:

```bash
# Повне розгортання Atlas (включає Task Orchestrator)
./deploy_atlas.sh

# Або з конкретними опціями
./deploy_atlas.sh --proxy    # З MCP Proxy режимом
```

## 🔧 Ручне встановлення

### Вимоги
- Python 3.8+
- Віртуальне середовище `atlas_venv`
- Доступ до директорії `mcp-task-orchestrator/`

### Кроки встановлення

1. **Активація віртуального середовища:**
```bash
cd /Users/dev/Documents/Atlas-mcp
source atlas_venv/bin/activate
```

2. **Встановлення Task Orchestrator:**
```bash
cd mcp-task-orchestrator
pip install -e .
cd ..
```

3. **Перевірка встановлення:**
```bash
python -c "from mcp_task_orchestrator.infrastructure.mcp.tool_definitions import get_all_tools; print('✅ Task Orchestrator ready!'); print(f'Available tools: {len(get_all_tools())}')"
```

**Очікуваний результат:**
```
✅ Task Orchestrator ready!
Available tools: 32
```

## 🔄 Інтеграція з Atlas

### HTTP Server Integration

Task Orchestrator інтегрується з Atlas через `task_orchestrator_http_server.py`:

```bash
# Запуск HTTP сервера (автоматично в start_atlas.sh)
python task_orchestrator_http_server.py
```

**Порт:** 4006  
**Health Check:** `http://localhost:4006/health`

### Atlas Core Integration

Atlas Core підключається до Task Orchestrator через:
- **Direct connection:** `http://localhost:4006` (fallback)
- **MCP Proxy:** `http://localhost:9090/atlas-task-orchestrator/` (primary)

## 📊 Доступні інструменти (32 tools)

### 🎯 Core Orchestration
- `orchestrator_initialize_session` - Ініціалізація нової сесії
- `orchestrator_plan_task` - Створення плану з підзадачами
- `orchestrator_execute_task` - Виконання завдання з спеціалістом
- `orchestrator_complete_task` - Завершення з артефактами
- `orchestrator_synthesize_results` - Синтез результатів

### 📋 Task Management
- `orchestrator_get_status` - Перевірка статусу
- `orchestrator_update_task` - Оновлення завдання
- `orchestrator_delete_task` - Видалення завдання
- `orchestrator_query_tasks` - Пошук завдань

### 📊 Session Management
- `orchestrator_list_sessions` - Список сесій
- `orchestrator_resume_session` - Відновлення сесії
- `orchestrator_cleanup_sessions` - Очищення старих сесій
- `orchestrator_session_status` - Статус сесії

### ⚡ Advanced Features
- `orchestrator_execute_subtask` - Виконання підзадач
- `orchestrator_complete_subtask` - Завершення підзадач
- `orchestrator_maintenance_coordinator` - Автоматичне обслуговування

## 🧪 Тестування

### Базовий тест через Atlas API

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "відкрий мені калькулятор", "user_id": "test"}'
```

### Прямий тест Task Orchestrator

```bash
curl -s -X POST http://localhost:4006/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "orchestrator_initialize_session",
    "parameters": {"working_directory": "/Users/dev/Documents/Atlas-mcp"}
  }'
```

## 🔧 Налагодження

### Перевірка логів

```bash
# Task Orchestrator HTTP Server
tail -f /tmp/task_orchestrator.log

# Atlas Core інтеграція
tail -f /tmp/atlas_core.log | grep "Task Orchestrator"
```

### Типові проблеми

**❌ `ModuleNotFoundError: No module named 'mcp_task_orchestrator'`**
```bash
# Переконайтеся, що встановлено в правильному venv
source atlas_venv/bin/activate
cd mcp-task-orchestrator && pip install -e .
```

**❌ `Task orchestrator not available`**
```bash
# Перевірте HTTP сервер
curl http://localhost:4006/health
# Якщо не працює - перезапустіть Atlas
./stop_atlas.sh && ./start_atlas.sh --proxy
```

**❌ `Failed to initialize intelligent task orchestrator`**
```bash
# Перевірте імпорт в середовищі Atlas
source atlas_venv/bin/activate
python -c "from mcp_task_orchestrator.infrastructure.mcp.tool_definitions import get_all_tools; print(len(get_all_tools()))"
```

## 📝 Конфігурація

### Environment Variables

```bash
# В atlas_venv/bin/activate або .env
export TASK_ORCHESTRATOR_PORT=4006
export ATLAS_WORKING_DIR="/Users/dev/Documents/Atlas-mcp"
export ATLAS_MCP_TASK_ORCHESTRATOR_URL="http://localhost:4006"
```

### MCP Proxy Configuration

В `mcp-proxy/atlas-global-config.json`:
```json
{
  "atlas-task-orchestrator": {
    "url": "http://localhost:4006/sse",
    "type": "sse",
    "options": {
      "panicIfInvalid": false,
      "logEnabled": true
    }
  }
}
```

## 🎯 Використання

### Через Atlas Chat API

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Створи Python скрипт для обробки CSV файлів",
    "user_id": "developer"
  }'
```

### Прямий виклик інструментів

```bash
# Ініціалізація сесії
curl -X POST http://localhost:4006/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "orchestrator_initialize_session",
    "parameters": {"working_directory": "/path/to/project"}
  }'

# Планування завдання
curl -X POST http://localhost:4006/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "orchestrator_plan_task",
    "parameters": {
      "task_description": "Build a REST API",
      "context": "Python FastAPI project"
    }
  }'
```

## 🔄 Оновлення

Task Orchestrator оновлюється разом з Atlas:

```bash
./update_atlas.sh --mcp-only    # Тільки MCP компоненти
./update_atlas.sh               # Повне оновлення
```

---

**✅ Task Orchestrator готовий до використання з Atlas!**

Для детальної документації Task Orchestrator див. `mcp-task-orchestrator/README.md`.
