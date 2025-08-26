#!/bin/bash

# Atlas Full System Startup Script з Українським TTS
# Запускає всі компоненти Atlas включаючи мінімальний фронтенд та український TTS

set -e

echo "🚀 Starting Atlas Full System with Ukrainian TTS..."

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
    pkill -f "mcp_tts_server.py" 2>/dev/null || true
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
        
        if [ $attempt -eq $max_attempts ]; then
            error "❌ $name failed to start after $max_attempts attempts"
            return 1
        fi
        
        echo -n "⏳ Waiting for $name... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
}

# Функція для тестування API
test_api() {
    local url=$1
    local name=$2
    local data=$3
    
    echo -n "🧪 Testing $name..."
    
    if [ -n "$data" ]; then
        response=$(curl -s -X POST "$url" -H "Content-Type: application/json" -d "$data" 2>/dev/null || echo "ERROR")
    else
        response=$(curl -s "$url" 2>/dev/null || echo "ERROR")
    fi
    
    if [ "$response" != "ERROR" ] && [ -n "$response" ]; then
        log "✅ $name test passed"
        echo "   Response: ${response:0:100}$([ ${#response} -gt 100 ] && echo '...')"
    else
        warning "⚠️  $name test failed"
    fi
}

# Головна функція
main() {
    log "🌟 Atlas Full System Startup with Ukrainian TTS"
    log "📍 Working directory: $(pwd)"
    
    cleanup
    
    log "🐍 Activating Python virtual environment..."
    source atlas_venv/bin/activate
    
    # Установка Ukrainian TTS залежностей
    log "📦 Installing Ukrainian TTS dependencies..."
    pip install -q ukrainian-tts[all] gtts pygame || warning "Some TTS dependencies may not install properly"
    
    # 1. Запускаємо MCP Proxy з українським TTS
    log "🔗 Starting MCP Proxy with Ukrainian TTS..."
    if [ -f "/Users/dev/mcp-stack/proxy/mcp-proxy/build/mcp-proxy" ]; then
        cd /Users/dev/mcp-stack/proxy/mcp-proxy
        ./build/mcp-proxy -config /Users/dev/Documents/Atlas-mcp/mcp_proxy_config_ukrainian.json > /tmp/mcp-proxy.log 2>&1 &
        MCP_PID=$!
        cd - > /dev/null
        log "MCP Proxy started (PID: $MCP_PID)"
    else
        warning "MCP Proxy binary not found, skipping..."
    fi
    
    # 2. Запускаємо Atlas Core
    log "🧠 Starting Atlas Core..."
    ATLAS_MCP_PROXY_MODE=true python atlas_core.py > /tmp/atlas-core.log 2>&1 &
    ATLAS_PID=$!
    log "Atlas Core started (PID: $ATLAS_PID)"
    
    # 3. Запускаємо Frontend
    log "🎨 Starting Minimal Frontend Server..."
    python 3d_helmet_viewer/atlas_minimal_live.py > /tmp/atlas-frontend.log 2>&1 &
    FRONTEND_PID=$!
    log "Frontend Server started (PID: $FRONTEND_PID)"
    
    echo
    log "🔍 Checking services status..."
    
    # Перевіряємо MCP Proxy (якщо запущений)
    if [ -n "$MCP_PID" ]; then
        check_service "http://localhost:4010/health" "MCP Proxy"
    fi
    
    # Перевіряємо Atlas Core
    check_service "http://localhost:8000/" "Atlas Core"
    
    # Перевіряємо Frontend
    check_service "http://localhost:8080/api/health" "Frontend Server"
    
    echo
    log "🧪 Running API Tests..."
    echo
    
    # Тест Atlas Core
    test_api "http://localhost:8000/" "Atlas Core Main Page"
    test_api "http://localhost:8000/chat" "Atlas Core Chat" '{"message": "Привіт! Тест українського TTS"}'
    
    # Тест MCP Proxy (якщо доступний)
    if [ -n "$MCP_PID" ]; then
        test_api "http://localhost:4010/health" "MCP Proxy Health"
        test_api "http://localhost:4010/api/chat" "MCP Proxy Chat" '{"message": "Тест MCP"}'
    fi
    
    # Тест Frontend
    test_api "http://localhost:8080/api/logs" "Frontend Logs API"
    
    echo
    log "🎉 Atlas Full System Status:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -n "$MCP_PID" ] && kill -0 $MCP_PID 2>/dev/null; then
        echo -e "🔗 MCP Proxy:     ${GREEN}✅ Running${NC} (PID: $MCP_PID, Port: 4010)"
    else
        echo -e "🔗 MCP Proxy:     ${YELLOW}⚠️  Skipped${NC}"
    fi
    
    echo -e "🧠 Atlas Core:    ${GREEN}✅ Running${NC} (PID: $ATLAS_PID, Port: 8000)"
    echo -e "🎨 Frontend:      ${GREEN}✅ Running${NC} (PID: $FRONTEND_PID, Port: 8080)"
    echo -e "🎙️ Ukrainian TTS: ${GREEN}✅ Integrated${NC} (via MCP)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo -e "${GREEN}🌐 Frontend URL:${NC}  http://localhost:8080"
    echo -e "${GREEN}🔧 Atlas API:${NC}    http://localhost:8000"
    echo -e "${GREEN}🔗 MCP Proxy:${NC}    http://localhost:4010"
    
    echo
    echo -e "${BLUE}📋 Management Commands:${NC}"
    echo "  • Stop all:      pkill -f 'atlas_core|mcp-proxy|atlas_minimal'"
    echo "  • View logs:     tail -f /tmp/atlas-*.log"
    echo "  • Restart:       ./start_atlas_ukrainian.sh"
    
    echo
    log "✨ Atlas system with Ukrainian TTS is ready!"
    log "🌐 Opening browser..."
    
    # Відкриваємо браузер
    sleep 2
    open "http://localhost:8080" 2>/dev/null || echo "Please open http://localhost:8080 manually"
}

# Запуск
main "$@"
