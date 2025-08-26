
# Atlas MCP System Dependency Fix Guide
======================================

## Issue Analysis
The main issue preventing the Atlas system from starting is missing Python dependencies.
The system requires several packages that aren't installed.

## Quick Fix (Recommended)
Use the working mock system we've created:

```bash
# Start the working mock system
./simple_start_atlas.sh

# Test it
python3 comprehensive_atlas_tool_tester.py

# Stop it when done
./simple_stop_atlas.sh
```

## Full System Fix (For Production)

### 1. Install Python Dependencies
```bash
# Try installing with increased timeout
pip3 install --timeout=300 --retries=3 \
    fastapi uvicorn aiohttp pydantic \
    prometheus-client python-dotenv pyyaml

# Or install one by one
pip3 install fastapi
pip3 install uvicorn
pip3 install aiohttp
pip3 install pydantic
```

### 2. Start Individual MCP Servers
The system expects these servers to be running:

```bash
# Start Playwright MCP (port 3001)
# Start Atlas Coordinator (port 3002) 
# Start MCP Orchestrator (port 3003)
# Start Atlas 2 Visual (port 3004)
# Start Context MCP (port 3005)
# Start macOS Automator (port 3006)
# Start Streaming TTS (port 3007)
# Start Linux Automator (port 3008)
# Start Atlas Controller (port 3009)
```

### 3. Fix MCP Proxy Configuration
```bash
cd mcp-proxy
# Build the Go proxy
go build -o atlas-mcp-proxy .
# Start it
./atlas-mcp-proxy --config atlas-config.json
```

### 4. Start Main Services
```bash
# Start Task Orchestrator
python3 task_orchestrator_http_server.py &

# Start Atlas Core  
python3 atlas_core.py &
```

## Expected Results
After fixing dependencies and starting all services, you should see:
- ✅ 143+ tools available across all categories
- ✅ Ukrainian chat and TTS working
- ✅ All MCP servers responding on ports 3001-3009
- ✅ Atlas Core providing status at http://localhost:8000/status

## Testing Commands
```bash
# Test status
curl -s http://localhost:8000/status | jq '.'

# Test Ukrainian chat
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Привіт! Тест системи"}'

# Test comprehensive tools
python3 comprehensive_atlas_tool_tester.py
```
