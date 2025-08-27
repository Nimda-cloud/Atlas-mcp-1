#!/bin/bash
"""
🔄 Atlas Quick Update Script
============================

Швидке оновлення Atlas компонентів без повного перевстановлення.
Оновлює тільки ключові залежності та конфігурації.

Використання:
  ./update_atlas.sh                    # Стандартне оновлення
  ./update_atlas.sh --force            # Форсоване оновлення з перевстановленням
  ./update_atlas.sh --mcp-only         # Тільки MCP компоненти
"""

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE_UPDATE=false
MCP_ONLY=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --force)
            FORCE_UPDATE=true
            shift
            ;;
        --mcp-only)
            MCP_ONLY=true
            shift
            ;;
    esac
done

echo -e "${BLUE}🔄 Atlas Quick Update${NC}"
echo "===================="

# Stop Atlas if running
if pgrep -f "atlas_core.py" > /dev/null; then
    echo -e "${YELLOW}🛑 Stopping Atlas...${NC}"
    ./stop_atlas.sh || true
    sleep 2
fi

if [ "$MCP_ONLY" = false ]; then
    # Update Python packages
    if [ -d "$SCRIPT_DIR/atlas_venv" ]; then
        echo -e "${PURPLE}🐍 Updating Python packages...${NC}"
        source "$SCRIPT_DIR/atlas_venv/bin/activate"
        pip install --upgrade pip
        pip install --upgrade fastapi uvicorn aiohttp ollama prometheus-client
        echo -e "${GREEN}✅ Python packages updated${NC}"
    fi
fi

# Update NPM MCP packages
echo -e "${PURPLE}📦 Updating MCP packages...${NC}"
npm update -g @modelcontextprotocol/inspector
npm update -g @playwright/mcp
npm update -g better-playwright-mcp

if [ "$FORCE_UPDATE" = true ]; then
    echo -e "${YELLOW}🔄 Force reinstalling MCP packages...${NC}"
    npm uninstall -g better-playwright-mcp
    npm install -g better-playwright-mcp
fi

echo -e "${GREEN}✅ MCP packages updated${NC}"

# Update AppleScript MCP Server
if [ -d "$SCRIPT_DIR/applescript-mcp-server" ]; then
    echo -e "${PURPLE}🍎 Updating AppleScript MCP Server...${NC}"
    cd "$SCRIPT_DIR/applescript-mcp-server"
    git pull origin main
    npm install
    npm run build
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✅ AppleScript MCP updated${NC}"
else
    echo -e "${YELLOW}⚠️ AppleScript MCP not found, run full deployment${NC}"
fi

# Update Atlas MCP Proxy
if [ "$MCP_ONLY" = false ]; then
    echo -e "${PURPLE}🔗 Updating MCP Proxy...${NC}"
    cd "$SCRIPT_DIR/mcp-proxy"
    go install github.com/TBXark/mcp-proxy@latest || echo "Using existing proxy"
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✅ MCP Proxy updated${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Atlas updated successfully!${NC}"
echo -e "${BLUE}To restart Atlas: ./start_atlas.sh${NC}"
