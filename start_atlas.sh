#!/bin/bash

# Atlas Universal Startup Script
# Запускає Task Orchestrator + Atlas Core + Frontend в правильному порядку

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
    pkill -f "task_orchestrator_http_server.py" 2>/dev/null || true
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
    lsof -i :$port >/dev/null 2>&1 || netstat -an 2>/dev/null | grep ":$port " >/dev/null 2>&1
}

# Функція очищення процесів
clean_processes() {
    info "Очищення старих процесів..."
    
    pkill -f "atlas_core.py" 2>/dev/null || true
    pkill -f "task_orchestrator_http_server.py" 2>/dev/null || true
    pkill -f "mcp-proxy" 2>/dev/null || true
    pkill -f "atlas_minimal_live.py" 2>/dev/null || true
    
    # Очищення портів
    if check_port 4006; then
        lsof -ti:4006 2>/dev/null | xargs -r kill -9 2>/dev/null || true
    fi
    
    if check_port 8000; then
        lsof -ti:8000 2>/dev/null | xargs -r kill -9 2>/dev/null || true
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

# Визначаємо робочу директорію
ATLAS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
info "Робоча директорія: $ATLAS_DIR"

# Перевірка необхідних файлів
if [ ! -f "$ATLAS_DIR/atlas_core.py" ]; then
    error "Atlas Core не знайдено в $ATLAS_DIR"
    exit 1
fi

if [ ! -f "$ATLAS_DIR/task_orchestrator_http_server.py" ]; then
    error "Task Orchestrator HTTP Server не знайдено"
    exit 1
fi

# Очищення
clean_processes

# 1. Запуск Task Orchestrator HTTP Server
info "Запускаю Task Orchestrator..."
cd "$ATLAS_DIR"

# Перевіряємо наявність віртуального середовища
if [ -d "atlas_venv" ]; then
    source atlas_venv/bin/activate
    PYTHON_CMD="$ATLAS_DIR/atlas_venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

export TASK_ORCHESTRATOR_PORT=4006
export ATLAS_MCP_SERVERS="task-orchestrator"
export ATLAS_MCP_TASK_ORCHESTRATOR_URL="http://localhost:4006"
export ATLAS_WORKING_DIR="$ATLAS_DIR"

nohup $PYTHON_CMD task_orchestrator_http_server.py > /tmp/task_orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
echo $ORCHESTRATOR_PID > /tmp/atlas_orchestrator.pid
log "Task Orchestrator запущено (PID: $ORCHESTRATOR_PID)"

# Перевірка Task Orchestrator
sleep 5
if ! kill -0 $ORCHESTRATOR_PID 2>/dev/null; then
    error "Task Orchestrator не запустився"
    cat /tmp/task_orchestrator.log
    exit 1
fi

# 2. Запуск Atlas Core
info "Запускаю Atlas Core..."
cd "$ATLAS_DIR"
export ATLAS_MCP_PROXY_MODE=false  # Use direct MCP mode
export UKRAINIAN_TTS_ENABLED=true

nohup $PYTHON_CMD atlas_core.py > /tmp/atlas_core.log 2>&1 &
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

# Перевірка сервісів
wait_for_service "http://localhost:4006/health" "Task Orchestrator" || exit 1
wait_for_service "http://localhost:8000/status" "Atlas Core" || exit 1

echo ""
log "🎉 Atlas повністю запущено!"
echo ""
info "📊 Статус сервісів:"
info "   Task Orchestrator: http://localhost:4006 (PID: $ORCHESTRATOR_PID)"
info "   Atlas Core:        http://localhost:8000 (PID: $ATLAS_PID)"
echo ""
info "🌐 Відкрийте браузер: http://localhost:8000"
info "🛑 Для зупинки: Ctrl+C або ./stop_atlas.sh"
echo ""

# Система запущена у фоні
log "🎉 Система працює у фоні"
log "📊 Для перегляду логів:"
info "   Task Orchestrator: tail -f /tmp/task_orchestrator.log"
info "   Atlas Core:        tail -f /tmp/atlas_core.log"
echo ""
log "⏰ Система буде працювати до зупинки або перезавантаження"
log "🛑 Для зупинки: ./stop_atlas.sh"
echo ""

# Виходимо з trap cleanup, залишаючи процеси працювати
trap - SIGINT SIGTERM EXIT
log "🚀 Atlas працює автономно!"
