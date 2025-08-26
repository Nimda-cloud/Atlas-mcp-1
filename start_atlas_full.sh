#!/bin/bash

# Atlas Full System Startup Script
# Запускає всі компоненти Atlas включаючи мінімальний фронтенд

set -e

echo "🚀 Starting Atlas Full System..."

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функція для логування
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Функція для очищення процесів
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up existing processes...${NC}"
    
    # Зупиняємо всі Atlas процеси
    pkill -f "atlas_core.py" 2>/dev/null || true
    pkill -f "mcp-proxy" 2>/dev/null || true
    pkill -f "atlas_minimal_live.py" 2>/dev/null || true
    pkill -f "enhanced_server.py" 2>/dev/null || true
    
    # Очищуємо порти
    lsof -ti:4010 | xargs -r kill -9 2>/dev/null || true
    lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
    lsof -ti:8080 | xargs -r kill -9 2>/dev/null || true
    
    sleep 2
    log "Cleanup completed"
}

# Функція для перевірки статусу сервісу
check_service() {
    local url=$1
    local name=$2
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            log "✅ $name is ready"
            return 0
        fi
        echo -ne "\r${BLUE}⏳ Waiting for $name... (attempt $attempt/$max_attempts)${NC}"
        sleep 2
        ((attempt++))
    done
    
    echo ""
    error "❌ $name failed to start after $max_attempts attempts"
    return 1
}

# Функція для тестування API
test_api() {
    local url=$1
    local name=$2
    local payload=$3
    
    echo -e "\n${BLUE}🧪 Testing $name...${NC}"
    
    if [ -n "$payload" ]; then
        response=$(curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$url" 2>/dev/null || echo "ERROR")
    else
        response=$(curl -s "$url" 2>/dev/null || echo "ERROR")
    fi
    
    if [ "$response" != "ERROR" ]; then
        log "✅ $name test passed"
        echo "   Response: ${response:0:100}$([ ${#response} -gt 100 ] && echo '...')"
    else
        error "❌ $name test failed"
    fi
}

# Основний блок запуску
main() {
    cd "$(dirname "$0")"
    
    log "🌟 Atlas Full System Startup"
    log "📍 Working directory: $(pwd)"
    
    # Очищення
    cleanup
    
    # Перевіряємо віртуальне середовище
    if [ ! -d "atlas_venv" ]; then
        error "Virtual environment 'atlas_venv' not found. Please run setup first."
        exit 1
    fi
    
    log "🐍 Activating Python virtual environment..."
    source atlas_venv/bin/activate
    
    # 1. Запускаємо MCP Proxy
    log "🔗 Starting MCP Proxy..."
    if [ -f "/Users/dev/mcp-stack/proxy/mcp-proxy/build/mcp-proxy" ]; then
        cd /Users/dev/mcp-stack/proxy/mcp-proxy
        ./build/mcp-proxy -config /Users/dev/mcp-stack/proxy/config.json > /tmp/mcp-proxy.log 2>&1 &
        MCP_PID=$!
        cd - >/dev/null
        log "MCP Proxy started (PID: $MCP_PID)"
    else
        warning "MCP Proxy binary not found, skipping..."
    fi
    
    # 2. Запускаємо Atlas Core
    log "🧠 Starting Atlas Core..."
    ATLAS_MCP_PROXY_MODE=true python atlas_core.py > /tmp/atlas-core.log 2>&1 &
    ATLAS_PID=$!
    log "Atlas Core started (PID: $ATLAS_PID)"
    
    # 3. Запускаємо Minimal Frontend Server
    log "🎨 Starting Minimal Frontend Server..."
    python 3d_helmet_viewer/atlas_minimal_live.py > /tmp/atlas-frontend.log 2>&1 &
    FRONTEND_PID=$!
    log "Frontend Server started (PID: $FRONTEND_PID)"
    
    # Зберігаємо PIDs для подальшого керування
    echo "$MCP_PID" > /tmp/atlas_mcp.pid 2>/dev/null || true
    echo "$ATLAS_PID" > /tmp/atlas_core.pid
    echo "$FRONTEND_PID" > /tmp/atlas_frontend.pid
    
    # Перевіряємо статус сервісів
    echo -e "\n${BLUE}🔍 Checking services status...${NC}"
    
    # Перевіряємо MCP Proxy (якщо запущений)
    if [ -n "$MCP_PID" ] && kill -0 "$MCP_PID" 2>/dev/null; then
        check_service "http://localhost:4010/health" "MCP Proxy"
    fi
    
    # Перевіряємо Atlas Core
    check_service "http://localhost:8000/" "Atlas Core"
    
    # Перевіряємо Frontend
    check_service "http://localhost:8080/" "Frontend Server"
    
    # Запускаємо тести API
    echo -e "\n${BLUE}🧪 Running API Tests...${NC}"
    
    # Тест Atlas Core health
    test_api "http://localhost:8000/" "Atlas Core Main Page"
    
    # Тест чату через Atlas Core
    test_api "http://localhost:8000/chat" "Atlas Core Chat" '{"message": "Привіт, тест системи"}'
    
    # Тест MCP Proxy (якщо доступний)
    if curl -s "http://localhost:4010/health" >/dev/null 2>&1; then
        test_api "http://localhost:4010/health" "MCP Proxy Health"
        test_api "http://localhost:4010/api/chat" "MCP Proxy Chat" '{"message": "Тест MCP"}'
    fi
    
    # Тест Frontend логів
    test_api "http://localhost:8080/api/logs" "Frontend Logs API"
    
    # Фінальний статус
    echo -e "\n${GREEN}🎉 Atlas Full System Status:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -n "$MCP_PID" ] && kill -0 "$MCP_PID" 2>/dev/null; then
        echo -e "🔗 MCP Proxy:     ${GREEN}✅ Running${NC} (PID: $MCP_PID, Port: 4010)"
    else
        echo -e "🔗 MCP Proxy:     ${YELLOW}⚠️  Skipped${NC}"
    fi
    
    if kill -0 "$ATLAS_PID" 2>/dev/null; then
        echo -e "🧠 Atlas Core:    ${GREEN}✅ Running${NC} (PID: $ATLAS_PID, Port: 8000)"
    else
        echo -e "🧠 Atlas Core:    ${RED}❌ Failed${NC}"
    fi
    
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "🎨 Frontend:      ${GREEN}✅ Running${NC} (PID: $FRONTEND_PID, Port: 8080)"
    else
        echo -e "🎨 Frontend:      ${RED}❌ Failed${NC}"
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}🌐 Frontend URL:${NC}  http://localhost:8080"
    echo -e "${GREEN}🔧 Atlas API:${NC}    http://localhost:8000"
    echo -e "${GREEN}🔗 MCP Proxy:${NC}    http://localhost:4010"
    echo ""
    echo -e "${BLUE}📋 Management Commands:${NC}"
    echo "  • Stop all:      pkill -f 'atlas_core|mcp-proxy|atlas_minimal'"
    echo "  • View logs:     tail -f /tmp/atlas-*.log"
    echo "  • Restart:       ./start_atlas_full.sh"
    echo ""
    echo -e "${GREEN}✨ Atlas system is ready!${NC}"
    
    # Автоматично відкриваємо браузер (опціонально)
    if command -v open >/dev/null 2>&1; then
        log "🌐 Opening browser..."
        sleep 2
        open "http://localhost:8080" 2>/dev/null || true
    fi
}

# Обробка сигналів для graceful shutdown
trap cleanup SIGINT SIGTERM

# Запуск основної функції
main "$@"
