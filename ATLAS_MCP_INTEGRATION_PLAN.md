# Интеграция Нативного MCP Стека с Atlas

## Архитектурная Схема Интеграции

```
┌──────── NATIVE macOS HOST ──────────┐
│                                     │
│ ┌─── MCP STACK (stdio процессы) ───┐ │
│ │ applescript-mcp                  │ │
│ │ macos-automator-mcp             │ │
│ │ automation-mcp                  │ │
│ │ playwright-mcp                  │ │
│ │ tts-mcp + ukrainian-tts         │ │
│ │ mcp-vnc                         │ │
│ └───────────────┬─────────────────┘ │
│                 ▼                   │
│ ┌── mcp-proxy :4010 (HTTP) ─────┐   │
│ │ - Агрегация всех MCP          │   │
│ │ - Namespacing                 │   │
│ │ - Fallback chain              │   │
│ │ - Audit logging               │   │
│ └─────────────┬─────────────────┘   │
└───────────────┼─────────────────────┘
                ▼
┌─── ATLAS ORCHESTRATOR (Docker/нативно) ───┐
│                                            │
│ ┌─── atlas_core.py (3 LLM AGENTS) ───┐     │
│ │ LLM1: Interface Agent            │     │
│ │ LLM2: Orchestrator Agent         │     │
│ │ LLM3: Monitor Agent              │     │
│ │                                  │     │
│ │ MCP Client → http://127.0.0.1:4010 │     │
│ └──────────────┬───────────────────┘     │
│                ▼                         │
│ ┌─── WEB API :8000 ───────────────┐       │
│ │ /chat    - Чат с пользователем │       │
│ │ /action  - Выполнение команд   │       │
│ │ /status  - Статус системы      │       │
│ │ /metrics - Prometheus метрики  │       │
│ └─────────────┬──────────────────┘       │
└───────────────┼──────────────────────────┘
                ▼
┌─── FRONTEND :8080 ───────────────────────┐
│ enhanced_frontend_simple.html            │
│ - 3D UI Avatar                          │
│ - WebSocket real-time                   │
│ - Matrix hacker theme                   │
│ - Chat interface                        │
│ - TTS/voice integration                 │
└─────────────────────────────────────────┘
```

## Изменения в Atlas Core для Proxy Mode

### 1. Новые Environment Variables

```bash
# Режим единого proxy
ATLAS_MCP_PROXY_MODE=true
ATLAS_MCP_PROXY_URL=http://127.0.0.1:4010

# Отключить старые отдельные MCP endpoints
ATLAS_MCP_SERVERS=""
```

### 2. Модификация atlas_core.py

```python
# Добавить в класс AtlasCore:

async def load_mcp_config_proxy_mode(self):
    """Загрузка конфигурации в режиме единого proxy"""
    proxy_url = os.getenv('ATLAS_MCP_PROXY_URL', 'http://127.0.0.1:4010')
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            payload = {
                "jsonrpc": "2.0",
                "id": "atlas_bootstrap",
                "method": "list_tools"
            }
            async with session.post(proxy_url, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    tools = result.get('result', {}).get('tools', [])
                    
                    # Группировка по namespace
                    self.mcp_tools_cache = {}
                    for tool in tools:
                        namespace = tool['name'].split('.')[0] if '.' in tool['name'] else 'default'
                        if namespace not in self.mcp_tools_cache:
                            self.mcp_tools_cache[namespace] = []
                        self.mcp_tools_cache[namespace].append(tool)
                    
                    logger.info(f"Loaded {len(tools)} tools from MCP proxy across {len(self.mcp_tools_cache)} namespaces")
                    self.mcp_proxy_url = proxy_url
                    return True
                else:
                    logger.error(f"MCP Proxy returned HTTP {resp.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"Failed to connect to MCP proxy: {e}")
        return False

async def call_mcp_tool_via_proxy(self, tool_name: str, args: dict):
    """Вызов MCP инструмента через proxy"""
    if not hasattr(self, 'mcp_proxy_url'):
        raise Exception("MCP Proxy not initialized")
    
    payload = {
        "jsonrpc": "2.0",
        "id": f"atlas_{int(time.time())}",
        "method": "call_tool",
        "params": {
            "name": tool_name,
            "arguments": args
        }
    }
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
        async with session.post(self.mcp_proxy_url, json=payload) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result.get('result', {})
            else:
                raise Exception(f"MCP Proxy call failed: HTTP {resp.status}")

# Модификация метода инициализации:
def __init__(self):
    # ... existing code ...
    self.mcp_proxy_mode = os.getenv('ATLAS_MCP_PROXY_MODE', 'false').lower() == 'true'
    
async def initialize(self):
    """Инициализация системы"""
    if self.mcp_proxy_mode:
        success = await self.load_mcp_config_proxy_mode()
        if not success:
            logger.warning("Failed to initialize MCP proxy, falling back to direct mode")
            self.mcp_proxy_mode = False
            self.load_mcp_config()  # Fallback to old method
    else:
        self.load_mcp_config()
    
    # ... rest of initialization
```

## Интеграция с Enhanced Frontend

### 1. Обновление atlas-enhanced-frontend

Контейнер `atlas-enhanced-frontend` остается без изменений, но нужно обновить переменные окружения:

```yaml
# В docker-compose.yml:
atlas-enhanced-frontend:
  build: ./3d_helmet_viewer
  container_name: atlas-enhanced-frontend
  ports:
    - "8080:8080"
  environment:
    - ATLAS_CORE_URL=http://atlas-core:8000        # Подключение к Atlas
    - TTS_SERVICE_URL=http://host.docker.internal:4010  # Теперь через proxy
    - MCP_PROXY_URL=http://host.docker.internal:4010    # Прямой доступ к MCP
```

### 2. Расширенная интеграция через WebSocket

```javascript
// В enhanced_frontend_simple.html добавить:

class AtlasMCPIntegration {
    constructor(websocket) {
        this.ws = websocket;
        this.mcpProxyUrl = 'http://localhost:4010';
    }
    
    async getAvailableTools() {
        try {
            const response = await fetch(this.mcpProxyUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: 'frontend_tools',
                    method: 'list_tools'
                })
            });
            
            const result = await response.json();
            return result.result?.tools || [];
        } catch (error) {
            console.error('Failed to fetch MCP tools:', error);
            return [];
        }
    }
    
    async callTool(toolName, args) {
        const payload = {
            jsonrpc: '2.0',
            id: `frontend_${Date.now()}`,
            method: 'call_tool',
            params: { name: toolName, arguments: args }
        };
        
        try {
            const response = await fetch(this.mcpProxyUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            
            return await response.json();
        } catch (error) {
            console.error(`Failed to call tool ${toolName}:`, error);
            throw error;
        }
    }
    
    // Специальные методы для популярных namespace
    async takeScreenshot() {
        return await this.callTool('vnc.vnc_screenshot', {});
    }
    
    async speakUkrainian(text) {
        return await this.callTool('voice.tts_ukrainian', {text});
    }
    
    async runAppleScript(script) {
        return await this.callTool('as.run_applescript', {script});
    }
    
    async openApp(appName) {
        return await this.callTool('macos.open_application', {name: appName});
    }
}
```

## Планы Развертывания

### Вариант A: Полностью Нативный (Рекомендуемый)

```bash
# 1. Установить нативный MCP стек
./scripts/deploy_native_mcp.sh

# 2. Обновить Atlas для proxy mode
export ATLAS_MCP_PROXY_MODE=true
export ATLAS_MCP_PROXY_URL=http://127.0.0.1:4010

# 3. Запустить Atlas нативно (без Docker)
python3 atlas_core.py

# 4. Запустить только frontend в Docker
docker-compose up atlas-enhanced-frontend
```

### Вариант B: Гибридный (Atlas в Docker, MCP нативно)

```bash
# 1. Установить нативный MCP стек
./scripts/deploy_native_mcp.sh

# 2. Обновить docker-compose.yml для proxy
atlas-core:
  environment:
    ATLAS_MCP_PROXY_MODE: true
    ATLAS_MCP_PROXY_URL: http://host.docker.internal:4010
    # Убрать старые ATLAS_MCP_SERVERS

# 3. Запустить все через Docker
docker-compose up
```

### Вариант C: Максимально Нативный

```bash
# 1. Нативный MCP стек
./scripts/deploy_native_mcp.sh

# 2. Нативный Atlas
ATLAS_MCP_PROXY_MODE=true python3 atlas_core.py

# 3. Нативный frontend (без Docker)
cd 3d_helmet_viewer && python3 enhanced_server.py
```

## Обновления Frontend для МCP

### 1. Новые UI элементы

```html
<!-- Добавить в enhanced_frontend_simple.html -->
<div class="mcp-tools-panel">
    <h3>MCP TOOLS</h3>
    <div id="mcpNamespaces" class="namespaces-grid">
        <!-- Динамически заполняется через JS -->
    </div>
</div>
```

### 2. JavaScript для MCP интеграции

```javascript
// Загрузка и отображение доступных MCP инструментов
async function loadMCPTools() {
    const integration = new AtlasMCPIntegration();
    const tools = await integration.getAvailableTools();
    
    const namespaces = {};
    tools.forEach(tool => {
        const ns = tool.name.split('.')[0];
        if (!namespaces[ns]) namespaces[ns] = [];
        namespaces[ns].push(tool);
    });
    
    const container = document.getElementById('mcpNamespaces');
    Object.keys(namespaces).forEach(ns => {
        const nsDiv = document.createElement('div');
        nsDiv.className = 'namespace-card';
        nsDiv.innerHTML = `
            <h4>${ns.toUpperCase()}</h4>
            <div class="tools-count">${namespaces[ns].length} tools</div>
        `;
        nsDiv.onclick = () => showNamespaceTools(ns, namespaces[ns]);
        container.appendChild(nsDiv);
    });
}

// Быстрые команды с MCP интеграцией
const quickMCPCommands = {
    'screenshot': () => integration.takeScreenshot(),
    'speak hello': () => integration.speakUkrainian('Привіт, це Atlas!'),
    'open calculator': () => integration.runAppleScript('tell application "Calculator" to activate'),
    'system info': () => integration.callTool('sys.get_system_info', {})
};
```

## Мониторинг и Логирование

### 1. Объединенные метрики

```python
# В atlas_core.py добавить метрики для MCP proxy
MCP_TOOL_CALLS = Counter(
    "atlas_mcp_tool_calls_total", 
    "Total MCP tool calls", 
    ["namespace", "tool", "status"]
)

MCP_CALL_LATENCY = Histogram(
    "atlas_mcp_call_latency_seconds",
    "MCP tool call latency",
    ["namespace", "tool"]
)
```

### 2. Логирование через proxy audit

```python
# MCP proxy уже ведет audit log:
# ~/mcp-stack/proxy/logs/audit.log

# Atlas может его читать для отображения:
async def get_mcp_audit_logs(self, lines: int = 100):
    try:
        audit_path = Path.home() / "mcp-stack/proxy/logs/audit.log"
        if audit_path.exists():
            with open(audit_path, 'r') as f:
                return f.readlines()[-lines:]
    except Exception as e:
        logger.error(f"Failed to read MCP audit log: {e}")
    return []
```

## Преимущества Интеграции

| Компонент | До | После |
|-----------|----|----|
| MCP Серверы | 4-6 портов HTTP | 1 порт (proxy) |
| Atlas Integration | Множественные endpoints | Единый proxy endpoint |
| Frontend | Прямые TTS вызовы | Полный MCP toolset |
| Мониторинг | Раздельные метрики | Объединенный audit trail |
| Deployment | Docker-зависимый | Нативно опциональный |
| Расширяемость | Сложное добавление MCP | Простое добавление в proxy config |

## Следующие Шаги

1. **Реализовать proxy mode в atlas_core.py**
2. **Обновить docker-compose.yml** для гибридного режима  
3. **Расширить enhanced_frontend** MCP интеграцией
4. **Добавить health checks** для нативного стека
5. **Создать migration script** с старой архитектуры
