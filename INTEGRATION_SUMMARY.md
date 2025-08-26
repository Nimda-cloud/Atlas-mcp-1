# Atlas + Native MCP Integration Configuration

## Summary

Нативный MCP стек интегрируется с Atlas через единый proxy endpoint, обеспечивая:

1. **Simplified Architecture**: 1 порт вместо 4-6 MCP портов
2. **Enhanced Frontend**: 3D UI + полный доступ к MCP tools
3. **Flexible Deployment**: 3 варианта (полностью нативно / гибридно / Docker)
4. **Unified Monitoring**: Centralized audit logging + Prometheus metrics

## Integration Points

### 1. Atlas Core ↔ MCP Proxy
```
atlas_core.py → http://127.0.0.1:4010 (single MCP endpoint)
- list_tools → получает все доступные MCP инструменты
- call_tool → выполняет через proxy с namespace routing
- Fallback: если proxy недоступен → старый режим прямых endpoints
```

### 2. Enhanced Frontend ↔ Atlas Core  
```
enhanced_frontend_simple.html → http://127.0.0.1:8000 (Atlas API)
- /chat → пользовательский интерфейс
- /action → прямые команды  
- /status → статус системы + MCP proxy health
- WebSocket → real-time updates
```

### 3. Frontend ↔ MCP Proxy (Direct)
```javascript
// Прямой доступ к MCP для UI элементов
const mcpIntegration = new AtlasMCPIntegration();
await mcpIntegration.takeScreenshot();  // vnc.vnc_screenshot
await mcpIntegration.speakUkrainian('Привіт'); // voice.tts_ukrainian
```

## Deployment Scenarios

### Scenario A: Fully Native (Recommended)
```bash
# Native MCP stack
~/mcp-stack/scripts/start_proxy.sh

# Native Atlas  
ATLAS_MCP_PROXY_MODE=true python3 atlas_core.py

# Native Frontend
cd 3d_helmet_viewer && python3 enhanced_server.py
```

### Scenario B: Hybrid (Atlas in Docker)
```yaml
# docker-compose.yml
atlas-core:
  environment:
    ATLAS_MCP_PROXY_MODE: true
    ATLAS_MCP_PROXY_URL: http://host.docker.internal:4010
```

### Scenario C: Current (Fallback)
```bash
# Keep current docker-compose setup as fallback
docker-compose up
```

## Environment Variables

```bash
# MCP Proxy Configuration
ATLAS_MCP_PROXY_MODE=true
ATLAS_MCP_PROXY_URL=http://127.0.0.1:4010

# Legacy (fallback when proxy fails)
ATLAS_MCP_SERVERS=automation,macos-automator,tts,playwright

# Frontend Integration  
ATLAS_CORE_URL=http://127.0.0.1:8000
MCP_PROXY_URL=http://127.0.0.1:4010
```

## Key Benefits

| Component | Before | After |
|-----------|--------|-------|
| **Ports** | 6 HTTP ports | 1 HTTP port (proxy) |
| **Complexity** | Multiple endpoint mgmt | Single endpoint |
| **Frontend** | Limited TTS access | Full MCP toolset |
| **Native Support** | Docker-dependent | macOS native |
| **Tool Discovery** | Static config | Dynamic via list_tools |
| **Monitoring** | Scattered logs | Centralized audit |

## Next Actions

1. **Complete MCP stack deployment**: `./scripts/deploy_native_mcp.sh`
2. **Test proxy functionality**: `python3 ~/mcp-stack/scripts/health_check.py`  
3. **Update Atlas configuration**: Set ATLAS_MCP_PROXY_MODE=true
4. **Verify integration**: Check /status endpoint shows proxy mode
5. **Optional**: Migrate to fully native deployment

## Files Created

- `NATIVE_MCP_DEPLOYMENT_PLAN.md` - Full deployment guide
- `ATLAS_MCP_INTEGRATION_PLAN.md` - Integration architecture  
- `scripts/deploy_native_mcp.sh` - Automated installer
- `scripts/mcp_stack.sh` - Management utility
- `scripts/atlas_core_proxy_patch.py` - Code integration guide
- `configs/mcp-proxy.native.json` - Native proxy configuration

Архітектура готова для повної інтеграції нативного MCP стека з Atlas та enhanced frontend!
