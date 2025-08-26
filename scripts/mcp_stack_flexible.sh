#!/bin/bash
# Управління MCP стеком з гнучкою конфігурацією
# Версія 2.0 - Підтримка stdio/http/sse

set -e

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

MCP_DIR="$HOME/mcp-stack"
PROXY_DIR="$MCP_DIR/proxy/mcp-proxy"
CONFIG_FILE="$MCP_DIR/proxy/config.json"
PID_FILE="$MCP_DIR/proxy.pid"
LOG_FILE="$MCP_DIR/logs/proxy.log"

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Перевірка конфігурації
check_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        error "Конфігурація не знайдена: $CONFIG_FILE"
        return 1
    fi
    
    # Перевірка JSON синтаксису
    if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
        error "Невірний JSON в конфігурації"
        return 1
    fi
    
    success "Конфігурація валідна"
    return 0
}

# Створення базової конфігурації якщо не існує
create_default_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log "Створення базової конфігурації..."
        mkdir -p "$(dirname "$CONFIG_FILE")"
        
        # Копіюємо з Atlas проекту
        local atlas_config="/Users/dev/Documents/Atlas-mcp/configs/mcp-proxy-flexible.json"
        if [[ -f "$atlas_config" ]]; then
            cp "$atlas_config" "$CONFIG_FILE"
            # Заміна шляхів для поточного користувача
            sed -i "" "s|/Users/dev|$HOME|g" "$CONFIG_FILE"
            success "Конфігурація скопійована з Atlas проекту"
        else
            error "Не вдалося створити конфігурацію"
            return 1
        fi
    fi
}

# Запуск MCP proxy
start_proxy() {
    if is_running; then
        warning "MCP proxy вже працює (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    log "Запуск MCP proxy..."
    
    # Перевірка конфігурації
    if ! check_config; then
        return 1
    fi
    
    # Створення директорії для логів
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Запуск proxy
    cd "$PROXY_DIR"
    nohup ./build/mcp-proxy --config "$CONFIG_FILE" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # Очікування запуску
    sleep 3
    
    if is_running; then
        success "MCP proxy запущено (PID: $pid)"
        
        # Перевірка health
        local retries=5
        for ((i=1; i<=retries; i++)); do
            if health_check; then
                success "Health check пройдено"
                return 0
            fi
            log "Очікування готовності... ($i/$retries)"
            sleep 2
        done
        
        warning "Proxy запущено, але health check не пройдено"
        return 0
    else
        error "Помилка запуску proxy"
        return 1
    fi
}

# Зупинка proxy
stop_proxy() {
    if [[ ! -f "$PID_FILE" ]]; then
        warning "PID файл не знайдено"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    
    if ! kill -0 "$pid" 2>/dev/null; then
        warning "Процес з PID $pid не існує"
        rm -f "$PID_FILE"
        return 0
    fi
    
    log "Зупинка MCP proxy (PID: $pid)..."
    
    # Спроба graceful shutdown
    kill -TERM "$pid" 2>/dev/null
    
    # Очікування завершення
    for ((i=0; i<10; i++)); do
        if ! kill -0 "$pid" 2>/dev/null; then
            success "MCP proxy зупинено"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill
    warning "Примусове завершення процесу"
    kill -KILL "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    
    success "MCP proxy зупинено"
}

# Перевірка статусу
is_running() {
    [[ -f "$PID_FILE" ]] && kill -0 "$(cat $PID_FILE)" 2>/dev/null
}

# Health check
health_check() {
    curl -s -f http://127.0.0.1:4010/health >/dev/null 2>&1
}

# Статус системи
status() {
    echo "=== MCP STACK STATUS ==="
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        success "MCP proxy працює (PID: $pid)"
        
        # Детальна інформація про процес
        ps -p "$pid" -o pid,ppid,cpu,pmem,etime,command 2>/dev/null || true
        
        # Health check
        echo ""
        log "Health check..."
        if health_check; then
            success "✓ HTTP endpoint доступний"
        else
            error "✗ HTTP endpoint недоступний"
        fi
        
        # Тест list_tools
        echo ""
        log "Тестування list_tools..."
        local tools_response=$(curl -s -X POST http://127.0.0.1:4010 \
            -H "Content-Type: application/json" \
            -d '{"jsonrpc":"2.0","id":"status","method":"list_tools"}' 2>/dev/null)
        
        if [[ -n "$tools_response" ]]; then
            local tools_count=$(echo "$tools_response" | jq -r '.result.tools | length' 2>/dev/null || echo "0")
            if [[ "$tools_count" -gt 0 ]]; then
                success "✓ Доступно $tools_count MCP інструментів"
            else
                warning "✗ Інструменти не знайдено"
            fi
        else
            error "✗ Немає відповіді від MCP proxy"
        fi
        
    else
        warning "MCP proxy не працює"
    fi
    
    # Інформація про конфігурацію
    echo ""
    log "Конфігурація: $CONFIG_FILE"
    if [[ -f "$CONFIG_FILE" ]]; then
        local clients_count=$(jq -r '.clients | length' "$CONFIG_FILE" 2>/dev/null || echo "0")
        log "Клієнтів в конфігурації: $clients_count"
        
        # Показати namespace'и
        echo ""
        log "Налаштовані MCP сервери:"
        jq -r '.clients[] | "  \(.namespace // .name): \(.description // .name) (\(.type))"' "$CONFIG_FILE" 2>/dev/null || echo "  Помилка читання конфігурації"
    fi
}

# Показати логи
show_logs() {
    local lines="${1:-50}"
    
    if [[ -f "$LOG_FILE" ]]; then
        log "Останні $lines рядків логу:"
        tail -n "$lines" "$LOG_FILE"
    else
        warning "Лог файл не знайдено: $LOG_FILE"
    fi
}

# Перегляд логів в real-time
tail_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        log "Моніторинг логів (Ctrl+C для виходу):"
        tail -f "$LOG_FILE"
    else
        warning "Лог файл не знайдено: $LOG_FILE"
    fi
}

# Тестування MCP endpoint
test_mcp() {
    log "Тестування MCP proxy..."
    
    if ! health_check; then
        error "MCP proxy недоступний"
        return 1
    fi
    
    echo ""
    log "1. Список інструментів:"
    local tools_response=$(curl -s -X POST http://127.0.0.1:4010 \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":"test_tools","method":"list_tools"}')
    
    if [[ -n "$tools_response" ]]; then
        echo "$tools_response" | jq '.' 2>/dev/null || echo "$tools_response"
    else
        error "Немає відповіді"
        return 1
    fi
    
    echo ""
    log "2. Список ресурсів:"
    local resources_response=$(curl -s -X POST http://127.0.0.1:4010 \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":"test_resources","method":"list_resources"}')
    
    if [[ -n "$resources_response" ]]; then
        echo "$resources_response" | jq '.' 2>/dev/null || echo "$resources_response"
    fi
    
    success "Тестування завершено"
}

# Показати конфігурацію
show_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        log "Поточна конфігурація:"
        jq '.' "$CONFIG_FILE"
    else
        error "Конфігурація не знайдена"
    fi
}

# Перезавантаження
restart() {
    log "Перезавантаження MCP proxy..."
    stop_proxy
    sleep 2
    start_proxy
}

# Показати використання
usage() {
    echo "Управління MCP стеком"
    echo ""
    echo "Використання: $0 КОМАНДА [ОПЦІЇ]"
    echo ""
    echo "КОМАНДИ:"
    echo "  start              Запустити MCP proxy"
    echo "  stop               Зупинити MCP proxy"
    echo "  restart            Перезапустити MCP proxy"
    echo "  status             Показати статус"
    echo "  logs [N]           Показати останні N рядків логу (за замовчуванням 50)"
    echo "  tail               Моніторинг логів в real-time"
    echo "  test               Тестувати MCP endpoint"
    echo "  config             Показати конфігурацію"
    echo "  health             Перевірити health endpoint"
    echo ""
    echo "ПРИКЛАДИ:"
    echo "  $0 start           # Запуск"
    echo "  $0 logs 100        # Останні 100 рядків логу"
    echo "  $0 status          # Детальний статус"
}

# Головна функція
main() {
    # Перевірка наявності jq та curl
    if ! command -v jq &> /dev/null; then
        error "jq не встановлено. Встановіть: brew install jq"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        error "curl не встановлено"
        exit 1
    fi
    
    # Створення директорій
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$(dirname "$PID_FILE")"
    
    # Створення конфігурації за замовчуванням
    create_default_config
    
    case "${1:-}" in
        start)
            start_proxy
            ;;
        stop)
            stop_proxy
            ;;
        restart)
            restart
            ;;
        status)
            status
            ;;
        logs)
            show_logs "${2:-50}"
            ;;
        tail)
            tail_logs
            ;;
        test)
            test_mcp
            ;;
        config)
            show_config
            ;;
        health)
            if health_check; then
                success "Health check пройдено"
            else
                error "Health check не вдався"
                exit 1
            fi
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Запуск
main "$@"
