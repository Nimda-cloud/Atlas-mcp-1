# Atlas MCP - Autonomous System

## Quick Start (Core + optional Viewer)

```bash
# Start Atlas Core + Task Orchestrator
./start_atlas.sh

# Start with 3D viewer (port 8080)
./start_atlas.sh --viewer

# Stop everything
./stop_atlas.sh
```

### Core API Endpoints

| Purpose        | URL                                  |
| -------------- | ------------------------------------ |
| Health (fast)  | <http://localhost:8000/health>         |
| Status (full)  | <http://localhost:8000/status>         |
| Chat API       | <http://localhost:8000/chat> (POST)    |
| Action API     | <http://localhost:8000/action> (POST)  |
| Viewer (static)| <http://localhost:8080/atlas_minimal_frontend.html> (if started) |

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
export ATLAS_MCP_PROXY_URL=http://localhost:4010
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

- `http://localhost:4010/` - базовий proxy
- `http://localhost:4010/{service}/sse` - для sse клієнтів
- `http://localhost:4010/{service}/mcp` - для streamable-http клієнтів

### Прямий запуск Proxy

```bash
cd mcp-proxy
./start-atlas-proxy.sh [config-file]
```

### Additional Notes

- UI терміналний інтерфейс видалено; API-first архітектура.
- 3D Viewer ізольовано і може еволюціонувати незалежно.
- Додаткові MCP сервіси можна додати через `ATLAS_MCP_SERVERS` (direct mode) або `ATLAS_MCP_PROXY_CLIENTS` (proxy mode).
 
