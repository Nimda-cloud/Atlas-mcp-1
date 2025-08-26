# Atlas MCP - Autonomous System

## Quick Start

```bash
# Start Atlas (all components in background)
./start_atlas.sh

# Stop Atlas
./stop_atlas.sh
```

## Access
- Frontend: http://localhost:8080
- MCP Proxy: http://localhost:4010  
- Atlas Core: http://localhost:8000

## Components
- **MCP Proxy**: 6 services, 54+ tools
- **Atlas Core**: AI system with Ukrainian TTS
- **Frontend**: 3D interface with chat

## Manual Start
```bash
# MCP Proxy
cd /Users/dev/mcp-stack/proxy && ./mcp-proxy/build/mcp-proxy &

# Atlas Core  
source atlas_venv/bin/activate && ATLAS_MCP_PROXY_MODE=true python3 atlas_core.py &

# Frontend
cd 3d_helmet_viewer && source ../atlas_venv/bin/activate && python3 atlas_minimal_live.py &
```
