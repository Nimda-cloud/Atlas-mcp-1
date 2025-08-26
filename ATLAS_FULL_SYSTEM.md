# Atlas Full System Management

## 🚀 Швидкий Запуск

### Запуск всієї системи:
```bash
./start_atlas_full.sh
```

### Зупинка системи:
```bash
./stop_atlas_full.sh
```

## 📋 Компоненти Системи

### 1. 🔗 MCP Proxy
- **Порт:** 4010
- **Призначення:** Model Context Protocol proxy для взаємодії з AI моделями
- **Статус:** Автоматично запускається якщо доступний

### 2. 🧠 Atlas Core
- **Порт:** 8000  
- **Призначення:** Основний AI агент системи з Ollama інтеграцією
- **API:** Основний веб-інтерфейс та chat endpoints

### 3. 🎨 Minimal Frontend
- **Порт:** 8080
- **Призначення:** Хакерський 3D інтерфейс з живими логами
- **Особливості:** 
  - Лівий панель: Живі логи системи (прихований скрол)
  - Правий панель: Чат з Atlas
  - Voice control (одинарний/подвійний клік)
  - 3D background з DamagedHelmet.glb

## 🔧 API Endpoints

### Atlas Core (localhost:8000)
- `GET /` - Головна сторінка з веб-інтерфейсом  
- `POST /api/chat` - Chat API (приймає JSON з message)

### Frontend Server (localhost:8080)
- `GET /` - Мінімальний хакерський інтерфейс
- `GET /api/logs` - Живі логи системи (JSON)
- `POST /api/chat` - Проксі для чату з Atlas/MCP
- `GET /DamagedHelmet.glb` - 3D модель

### MCP Proxy (localhost:4010) 
- `GET /health` - Health check
- `POST /api/chat` - MCP chat proxy

## 🧪 Тестування

Скрипт `start_atlas_full.sh` автоматично:
- ✅ Очищує старі процеси
- ✅ Запускає всі компоненти  
- ✅ Перевіряє статус кожного сервісу
- ✅ Тестує API endpoints
- ✅ Відкриває браузер з інтерфейсом

## 🗂️ Логи

Логи зберігаються в `/tmp/`:
- `/tmp/atlas-core.log` - Atlas Core логи
- `/tmp/mcp-proxy.log` - MCP Proxy логи  
- `/tmp/atlas-frontend.log` - Frontend Server логи

### Перегляд логів:
```bash
# Всі логи разом
tail -f /tmp/atlas-*.log

# Окремо по компонентах
tail -f /tmp/atlas-core.log
tail -f /tmp/mcp-proxy.log  
tail -f /tmp/atlas-frontend.log
```

## 🎮 Використання Frontend

### Чат:
- Введіть повідомлення у правій панелі
- **Enter** - відправити
- **Shift+Enter** - новий рядок

### Voice Control:
- **Одинарний клік 🎤** - Continuous режим (постійно слухає)
- **Подвійний клік 🎤** - Single режим (одна команда, автовідправка)

### Логи:
- Ліва панель показує живі логи з усіх компонентів
- Автоматичне оновлення кожну секунду
- Чисто зелений текст без парсінгу
- Прихований скролбар (прокрутка колесом/тачпадом)

## 🔄 Керування Процесами  

### PID файли:
- `/tmp/atlas_core.pid`
- `/tmp/atlas_mcp.pid`  
- `/tmp/atlas_frontend.pid`

### Ручне зупинення:
```bash
# Всі Atlas процеси
pkill -f 'atlas_core|mcp-proxy|atlas_minimal'

# Окремо
pkill -f atlas_core.py
pkill -f mcp-proxy  
pkill -f atlas_minimal_live.py
```

### Перевірка статусу:
```bash
ps aux | grep -E "(atlas_core|mcp-proxy|atlas_minimal)" | grep -v grep
lsof -i :8000,:8080,:4010
```

## 🛠️ Налаштування

### Конфігурація MCP Proxy:
`/Users/dev/mcp-stack/proxy/config.json`

### Конфігурація Atlas Core:
Змінні середовища:
- `ATLAS_MCP_PROXY_MODE=true` - Включає режим MCP proxy

### Frontend налаштування:
- Порт: змінити в `atlas_minimal_live.py` (PORT = 8080)
- Pollling інтервал: в `atlas_minimal_frontend.html` (1000ms)
- Стилізація: CSS у `atlas_minimal_frontend.html`

## 🎯 Готово!

Система повністю автоматизована:
1. `./start_atlas_full.sh` - запускає все
2. Відкривається браузер з http://localhost:8080  
3. Працює чат + voice control + живі логи
4. `./stop_atlas_full.sh` - зупиняє все

**Hacker-style мінімалістичний інтерфейс з повним функціоналом готовий! 🔥**
