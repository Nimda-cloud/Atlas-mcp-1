#!/bin/bash

# Atlas Universal Startup Script
# Запускає Task Orchestrator + Atlas Core (UI вилучено, опціонально можна підняти окремий viewer)

set -euo pipefail

SHOW_VIEWER=0

for arg in "$@"; do
    case "$arg" in
        --viewer) SHOW_VIEWER=1 ; shift ;;
        --help|-h)
            echo "Usage: $0 [--viewer]"
            echo "  --viewer   також стартує 3d_helmet_viewer/start_viewer.sh (порт 8080) якщо існує"
            exit 0
            ;;
    esac
done

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

#############################################
# 2. Опціональний запуск MCP Proxy
#############################################
MCP_PROXY_PID=""
if [[ "${ATLAS_MCP_PROXY_MODE:-false}" == "true" ]]; then
    info "Запускаю MCP Proxy..."
    cd "$ATLAS_DIR/mcp-proxy"
    if [[ -f "start-atlas-proxy.sh" ]]; then
        nohup ./start-atlas-proxy.sh > /tmp/mcp_proxy.log 2>&1 &
        MCP_PROXY_PID=$!
        echo $MCP_PROXY_PID > /tmp/mcp_proxy.pid
        log "MCP Proxy запущено (PID: $MCP_PROXY_PID)"
        sleep 3
        wait_for_service "http://localhost:9090/" "MCP Proxy" || {
            warn "MCP Proxy не запустився, продовжую в direct mode"
            export ATLAS_MCP_PROXY_MODE=false
        }
    else
        warn "MCP Proxy скрипт не знайдено, продовжую в direct mode"
        export ATLAS_MCP_PROXY_MODE=false
    fi
fi

#############################################
# 3. Запуск Atlas Core
#############################################
info "Запускаю Atlas Core..."
cd "$ATLAS_DIR"
export UKRAINIAN_TTS_ENABLED=true

# Підказка щодо CORS, якщо увімкнуто
if [[ "${ATLAS_ENABLE_CORS:-0}" == "1" ]]; then
    info "CORS увімкнено (origins: ${ATLAS_ALLOWED_ORIGINS:-*})"
fi

nohup $PYTHON_CMD atlas_core.py > /tmp/atlas_core.log 2>&1 &
ATLAS_PID=$!
echo $ATLAS_PID > /tmp/atlas_core.pid
log "Atlas Core запущено (PID: $ATLAS_PID)"

# Перевірка Atlas Core процеса
sleep 2
if ! kill -0 $ATLAS_PID 2>/dev/null; then
        error "Atlas Core не запустився"
        cat /tmp/atlas_core.log || true
        exit 1
fi

# Швидкий liveness (/health), потім докладний /status
wait_for_service "http://localhost:4006/health" "Task Orchestrator" || exit 1
wait_for_service "http://localhost:8000/health" "Atlas Core (health)" || exit 1
wait_for_service "http://localhost:8000/status" "Atlas Core (status)" || exit 1

echo ""
log "🎉 Atlas повністю запущено!"
echo ""
info "📊 Статус сервісів:"
if [[ -n "$MCP_PROXY_PID" ]]; then
    info "   MCP Proxy: http://localhost:9090 (PID: $MCP_PROXY_PID)"
fi
info "   Task Orchestrator: http://localhost:4006 (PID: $ORCHESTRATOR_PID)"
info "   Atlas Core API:    http://localhost:8000 (PID: $ATLAS_PID)"
if [[ $SHOW_VIEWER -eq 1 ]]; then
    if [[ -f "$ATLAS_DIR/3d_helmet_viewer/start_viewer.sh" ]]; then
        info "   Viewer:            http://localhost:8080 (автозапуск)"
    else
        warning "   Viewer (--viewer) запитано, але скрипт 3d_helmet_viewer/start_viewer.sh не знайдено"
    fi
fi
echo ""
info "🌐 Перевірка стану: http://localhost:8000/status (root / -> короткий JSON, /health -> швидкий)"
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

# Опціональний запуск viewer
if [[ $SHOW_VIEWER -eq 1 ]]; then
    if [[ -f "$ATLAS_DIR/3d_helmet_viewer/start_viewer.sh" ]]; then
        info "Запускаю viewer (--viewer) на порту 8080..."
        nohup bash "$ATLAS_DIR/3d_helmet_viewer/start_viewer.sh" > /tmp/atlas_viewer.log 2>&1 &
        VIEWER_PID=$!
        echo $VIEWER_PID > /tmp/atlas_viewer.pid
        log "Viewer запущено (PID: $VIEWER_PID)"
    else
        warning "Viewer не запущено: скрипт start_viewer.sh відсутній"
    fi
fi
