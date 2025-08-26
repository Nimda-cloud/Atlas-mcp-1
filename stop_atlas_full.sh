#!/bin/bash

# Atlas System Stop Script
# Зупиняє всі компоненти Atlas

echo "🛑 Stopping Atlas Full System..."

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

# Зупиняємо процеси за PID файлами
if [ -f "/tmp/atlas_mcp.pid" ]; then
    MCP_PID=$(cat /tmp/atlas_mcp.pid)
    if kill -0 "$MCP_PID" 2>/dev/null; then
        kill "$MCP_PID"
        log "Stopped MCP Proxy (PID: $MCP_PID)"
    fi
    rm -f /tmp/atlas_mcp.pid
fi

if [ -f "/tmp/atlas_core.pid" ]; then
    ATLAS_PID=$(cat /tmp/atlas_core.pid)
    if kill -0 "$ATLAS_PID" 2>/dev/null; then
        kill "$ATLAS_PID"
        log "Stopped Atlas Core (PID: $ATLAS_PID)"
    fi
    rm -f /tmp/atlas_core.pid
fi

if [ -f "/tmp/atlas_frontend.pid" ]; then
    FRONTEND_PID=$(cat /tmp/atlas_frontend.pid)
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID"
        log "Stopped Frontend (PID: $FRONTEND_PID)"
    fi
    rm -f /tmp/atlas_frontend.pid
fi

# Додаткове очищення
pkill -f "atlas_core.py" 2>/dev/null || true
pkill -f "mcp-proxy" 2>/dev/null || true
pkill -f "atlas_minimal_live.py" 2>/dev/null || true

# Очищуємо порти (якщо потрібно)
lsof -ti:4010 | xargs -r kill -9 2>/dev/null || true
lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
lsof -ti:8080 | xargs -r kill -9 2>/dev/null || true

log "🧹 Atlas system stopped"
