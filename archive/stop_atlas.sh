#!/bin/bash

# Atlas Stop Script
# Зупиняє всі компоненти Atlas

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🛑 Atlas Stop"
echo "============="

# Зупиняємо за PID файлами
if [ -f "/tmp/atlas_orchestrator.pid" ]; then
    ORCHESTRATOR_PID=$(cat /tmp/atlas_orchestrator.pid)
    if kill -0 "$ORCHESTRATOR_PID" 2>/dev/null; then
        kill "$ORCHESTRATOR_PID"
        log "Зупинено Task Orchestrator (PID: $ORCHESTRATOR_PID)"
    fi
    rm -f /tmp/atlas_orchestrator.pid
fi

if [ -f "/tmp/atlas_core.pid" ]; then
    ATLAS_PID=$(cat /tmp/atlas_core.pid)
    if kill -0 "$ATLAS_PID" 2>/dev/null; then
        kill "$ATLAS_PID"
        log "Зупинено Atlas Core (PID: $ATLAS_PID)"
    fi
    rm -f /tmp/atlas_core.pid
fi

if [ -f "/tmp/atlas_viewer.pid" ]; then
    VIEWER_PID=$(cat /tmp/atlas_viewer.pid)
    if kill -0 "$VIEWER_PID" 2>/dev/null; then
        kill "$VIEWER_PID"
        log "Зупинено Viewer (PID: $VIEWER_PID)"
    fi
    rm -f /tmp/atlas_viewer.pid
fi

# Зупинка MCP Proxy (якщо запущено)
if [ -f "/tmp/mcp_proxy.pid" ]; then
    MCP_PROXY_PID=$(cat /tmp/mcp_proxy.pid)
    if kill -0 "$MCP_PROXY_PID" 2>/dev/null; then
        kill "$MCP_PROXY_PID"
        log "Зупинено MCP Proxy (PID: $MCP_PROXY_PID)"
    fi
    rm -f /tmp/mcp_proxy.pid
fi

# Додаткове очищення
pkill -f "atlas_core.py" 2>/dev/null || true
pkill -f "task_orchestrator_http_server.py" 2>/dev/null || true
pkill -f "mcp-proxy" 2>/dev/null || true
pkill -f "atlas_minimal_live.py" 2>/dev/null || true
pkill -f "http.server.*8080" 2>/dev/null || true

# Очищення логів
rm -f /tmp/atlas_*.log 2>/dev/null || true
rm -f /tmp/task_orchestrator.log 2>/dev/null || true

log "🎉 Atlas повністю зупинено"
