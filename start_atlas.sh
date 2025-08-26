#!/bin/bash

# Atlas Universal Startup Script
# Запускає MCP Proxy + Atlas Core + Frontend в правильному порядку

set -e

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Функція очищення при виході
cleanup() {
    echo -e "\n${YELLOW}🧹 Зупиняю Atlas...${NC}"
    
    # Зупиняємо всі процеси
    pkill -f "atlas_core.py" 2>/dev/null || true
    pkill -f "mcp-proxy" 2>/dev/null || true
    pkill -f "atlas_minimal_live.py" 2>/dev/null || true
    
    # Очищуємо PID файли
    rm -f /tmp/atlas_*.pid 2>/dev/null || true
    
    log "Atlas зупинено"
    exit 0
}

# Встановлюємо trap для cleanup
trap cleanup SIGINT SIGTERM EXIT

# Функція перевірки порту
check_port() {
    local port=$1
    lsof -i :$port >/dev/null 2>&1
}

# Функція очищення процесів
clean_processes() {
    info "Очищення старих процесів..."
    
    pkill -f "atlas_core.py" 2>/dev/null || true
    pkill -f "mcp-proxy" 2>/dev/null || true
    pkill -f "atlas_minimal_live.py" 2>/dev/null || true
    
    # Очищення портів
    if check_port 4010; then
        lsof -ti:4010 | xargs -r kill -9 2>/dev/null || true
    fi
    
    if check_port 8080; then
        lsof -ti:8080 | xargs -r kill -9 2>/dev/null || true
    fi
    
    sleep 2
    log "Очищення завершено"
}

# Функція перевірки сервісу
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    info "Очікування готовності $name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            log "$name готовий!"
            return 0
        fi
        sleep 1
        ((attempt++))
    done
    
    error "$name не запустився за $max_attempts секунд"
    return 1
}

echo "🚀 Atlas Universal Startup"
echo "========================="

# Перевірка директорій
if [ ! -d "/Users/dev/mcp-stack/proxy" ]; then
    error "MCP Stack не знайдено в /Users/dev/mcp-stack/"
    exit 1
fi

if [ ! -f "/Users/dev/Documents/Atlas-mcp/atlas_core.py" ]; then
    error "Atlas Core не знайдено"
    exit 1
fi

if [ ! -f "/Users/dev/Documents/Atlas-mcp/3d_helmet_viewer/atlas_minimal_live.py" ]; then
    error "Frontend не знайдено"
    exit 1
fi

# Очищення
clean_processes

# 1. Запуск MCP Proxy
info "Запускаю MCP Proxy..."
cd /Users/dev/mcp-stack/proxy
nohup ./mcp-proxy/build/mcp-proxy > /tmp/mcp_proxy.log 2>&1 &
MCP_PID=$!
echo $MCP_PID > /tmp/atlas_mcp.pid
log "MCP Proxy запущено (PID: $MCP_PID)"

# Перевірка MCP Proxy
sleep 3
if ! kill -0 $MCP_PID 2>/dev/null; then
    error "MCP Proxy не запустився"
    cat /tmp/mcp_proxy.log
    exit 1
fi

# 2. Запуск Atlas Core
info "Запускаю Atlas Core..."
cd /Users/dev/Documents/Atlas-mcp
export ATLAS_MCP_PROXY_MODE=true
export UKRAINIAN_TTS_ENABLED=true
source atlas_venv/bin/activate
nohup python3 atlas_core.py > /tmp/atlas_core.log 2>&1 &
ATLAS_PID=$!
echo $ATLAS_PID > /tmp/atlas_core.pid
log "Atlas Core запущено (PID: $ATLAS_PID)"

# Перевірка Atlas Core
sleep 3
if ! kill -0 $ATLAS_PID 2>/dev/null; then
    error "Atlas Core не запустився"
    cat /tmp/atlas_core.log
    exit 1
fi

# 3. Запуск Frontend
info "Запускаю Frontend..."
cd /Users/dev/Documents/Atlas-mcp/3d_helmet_viewer
source ../atlas_venv/bin/activate
nohup python3 atlas_minimal_live.py > /tmp/atlas_frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/atlas_frontend.pid
log "Frontend запущено (PID: $FRONTEND_PID)"

# Перевірка Frontend
sleep 3
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    error "Frontend не запустився"
    cat /tmp/atlas_frontend.log
    exit 1
fi

# Перевірка сервісів
wait_for_service "http://localhost:4010" "MCP Proxy" || exit 1
wait_for_service "http://localhost:8080" "Frontend" || exit 1

echo ""
log "🎉 Atlas повністю запущено!"
echo ""
info "📊 Статус сервісів:"
info "   MCP Proxy:  http://localhost:4010 (PID: $MCP_PID)"
info "   Atlas Core: Активний (PID: $ATLAS_PID)"
info "   Frontend:   http://localhost:8080 (PID: $FRONTEND_PID)"
echo ""
info "🌐 Відкрийте браузер: http://localhost:8080"
info "🛑 Для зупинки: Ctrl+C"
echo ""

# Система запущена у фоні
log "🎉 Система працює у фоні"
log "📊 Для перегляду логів:"
info "   Atlas Core: tail -f /tmp/atlas_core.log"
info "   Frontend:   tail -f /tmp/atlas_frontend.log"
info "   MCP Proxy:  tail -f /tmp/mcp_proxy.log"
echo ""
log "⏰ Система буде працювати до зупинки або перезавантаження"
log "🛑 Для зупинки: ./stop_atlas.sh"
echo ""

# Виходимо з trap cleanup, залишаючи процеси працювати
trap - SIGINT SIGTERM EXIT
log "🚀 Atlas працює автономно!"
