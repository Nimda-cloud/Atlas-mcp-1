#!/bin/bash
# Atlas MCP Deployment Manager
# Керування різними режимами розгортання з автоматичним звільненням портів

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функції логування
log_info() { echo -e "${BLUE}ℹ️ INFO:${NC} $1"; }
log_success() { echo -e "${GREEN}✅ SUCCESS:${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠️ WARNING:${NC} $1"; }
log_error() { echo -e "${RED}❌ ERROR:${NC} $1"; }

# Функція зупинки всіх Atlas сервісів
stop_all_atlas() {
    log_info "Зупиняю всі Atlas сервіси..."
    
    # Зупинка Docker Compose
    if [ -f "docker-compose.yml" ]; then
        log_info "Зупиняю Docker Compose сервіси..."
        docker compose down || true
        docker compose --profile monitoring --profile mcp --profile macos down || true
    fi
    
    # Зупинка Kind кластерів
    log_info "Зупиняю Kind кластери..."
    kind get clusters 2>/dev/null | grep -E "(atlas|mcp)" | while read cluster; do
        log_info "Видаляю Kind кластер: $cluster"
        kind delete cluster --name "$cluster" || true
    done
    
    # Зупинка локальних Python процесів
    log_info "Зупиняю локальні Python Atlas процеси..."
    pkill -f "atlas_core.py" || true
    pkill -f "mcp_.*_server.py" || true
    
    # НЕ зупиняємо Ollama - вона потрібна як зовнішній сервіс
    log_info "Ollama залишається запущеною як зовнішній LLM сервіс"
    
    log_success "Всі Atlas сервіси зупинено"
}

# Функція перевірки зайнятих портів
check_ports() {
    local atlas_ports=("8000" "8080" "4002" "4003" "4004" "4005" "3000" "9090" "80" "30000" "30001" "30002")
    local occupied_ports=()
    local critical_ports=()
    
    log_info "Перевіряю зайняті Atlas порти..."
    
    for port in "${atlas_ports[@]}"; do
        if lsof -i :$port >/dev/null 2>&1; then
            occupied_ports+=("$port")
            
            # Перевіряю, чи це критичний Atlas процес
            local process_name=$(lsof -i :$port -c atlas -c docker -c python 2>/dev/null | grep -v COMMAND | head -1 | awk '{print $1}' || echo "")
            if [[ "$process_name" =~ (atlas|docker|python) ]]; then
                critical_ports+=("$port")
            fi
        fi
    done
    
    # Перевіряємо Ollama окремо (це нормально що вона працює)
    if lsof -i :11434 >/dev/null 2>&1; then
        log_info "Ollama працює на порті 11434 (це нормально)"
    else
        log_warning "Ollama не запущена на порті 11434 - Atlas може не працювати з LLM"
    fi
    
    if [ ${#occupied_ports[@]} -eq 0 ]; then
        log_success "Всі Atlas порти вільні"
        return 0
    else
        if [ ${#critical_ports[@]} -gt 0 ]; then
            log_warning "Зайняті критичні Atlas порти: ${critical_ports[*]}"
            return 1
        else
            log_info "Зайняті порти (не критичні для Atlas): ${occupied_ports[*]}"
            return 0
        fi
    fi
}

# Функція запуску в Local режимі
start_local() {
    log_info "Запускаю Atlas в Local режимі..."
    
    # Перевірка Python віртуального середовища
    if [ ! -d "atlas_env" ]; then
        log_info "Створюю Python віртуальне середовище..."
        python3 -m venv atlas_env
    fi
    
    source atlas_env/bin/activate
    
    # Встановлення залежностей (з timeout)
    log_info "Встановлюю залежності (може зайняти 3-5 хвилин)..."
    gtimeout 600 pip install -r requirements.txt 2>/dev/null || timeout 600 pip install -r requirements.txt 2>/dev/null || {
        log_warning "Повна установка не вдалася, встановлюю мінімальний набір..."
        pip install ollama openai fastapi uvicorn aiohttp psutil pydantic python-dotenv pyyaml click pytest pytest-asyncio
    }
    
    # Запуск Atlas Core
    log_info "Запускаю Atlas Core..."
    python atlas_core.py &
    
    # Очікування запуску
    sleep 10
    
    if curl -f http://localhost:8000/status >/dev/null 2>&1; then
        log_success "Atlas запущено в Local режимі: http://localhost:8000"
    else
        log_error "Не вдалося запустити Atlas в Local режимі"
        return 1
    fi
}

# Функція запуску в Docker режимі
start_docker() {
    log_info "Запускаю Atlas в Docker режимі..."
    
    # Збірка образів (з timeout)
    log_info "Будую Docker образи (може зайняти 5-10 хвилин)..."
    gtimeout 900 docker compose build 2>/dev/null || docker compose build || {
        log_error "Не вдалося побудувати Docker образи"
        return 1
    }
    
    # Запуск повного стеку
    log_info "Запускаю повний стек..."
    docker compose --profile monitoring --profile mcp --profile macos up -d
    
    # Очікування запуску (2-3 хвилини)
    log_info "Очікування готовності сервісів (2-3 хвилини)..."
    sleep 180
    
    # Перевірка здоров'я
    local services=("http://localhost:8000/status" "http://localhost:8080/health" "http://localhost:4002/health")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if ! curl -f "$service" >/dev/null 2>&1; then
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "Atlas запущено в Docker режимі:"
        echo "  • Core: http://localhost:8000"
        echo "  • Frontend: http://localhost:8080"
        echo "  • Grafana: http://localhost:3000"
        echo "  • Prometheus: http://localhost:9090"
    else
        log_warning "Деякі сервіси не готові: ${failed_services[*]}"
        log_info "Перевірте статус: docker compose logs"
    fi
}

# Функція запуску в Kubernetes режимі
start_kubernetes() {
    log_info "Запускаю Atlas в Kubernetes режимі..."
    
    # Перевірка наявності Kind кластера
    if ! kind get clusters 2>/dev/null | grep -q "atlas-mcp-dev"; then
        log_info "Створюю Kind кластер atlas-mcp-dev..."
        kind create cluster --name atlas-mcp-dev --config kind-config.yaml || {
            log_error "Не вдалося створити Kind кластер"
            return 1
        }
        
        # Очікування готовності кластера
        log_info "Очікування готовності кластера..."
        sleep 30
        
        # Перевірка підключення
        kubectl cluster-info --context kind-atlas-mcp-dev || {
            log_error "Не можу підключитися до створеного кластера"
            return 1
        }
    else
        log_info "Kind кластер atlas-mcp-dev вже існує"
        kubectl config use-context kind-atlas-mcp-dev
    fi
    
    # Збірка образів
    log_info "Будую Docker образи для Kubernetes (може зайняти 10-15 хвилин)..."
    make build-images || {
        log_error "Не вдалося побудувати образи для Kubernetes"
        return 1
    }
    
    # Завантаження образів в Kind кластер
    log_info "Завантажую образи в Kind кластер..."
    kind load docker-image atlas-mcp/atlas-core:latest --name atlas-mcp-dev
    kind load docker-image atlas-mcp/atlas-frontend:latest --name atlas-mcp-dev
    kind load docker-image atlas-mcp/mcp-automation:latest --name atlas-mcp-dev
    kind load docker-image atlas-mcp/mcp-automator:latest --name atlas-mcp-dev
    kind load docker-image atlas-mcp/mcp-tts:latest --name atlas-mcp-dev
    
    # Розгортання
    log_info "Розгортаю в Kubernetes (може зайняти 5-8 хвилин)..."
    make install-dev || {
        log_error "Не вдалося розгорнути в Kubernetes"
        return 1
    }
    
    # Очікування готовності подів
    log_info "Очікування готовності подів..."
    kubectl wait --for=condition=Ready pod \
      -l app.kubernetes.io/part-of=atlas-autonomous-system \
      -n atlas-mcp-dev \
      --timeout=300s || {
        log_warning "Деякі поди не готові за 5 хвилин"
    }
    
    # Port forwarding
    log_info "Налаштовую port forwarding..."
    make port-forward-atlas-dev &
    make port-forward-grafana-dev &
    make port-forward-prometheus-dev &
    
    sleep 10
    
    log_success "Atlas запущено в Kubernetes режимі:"
    echo "  • Atlas: http://localhost:8080 (port-forward)"
    echo "  • Grafana: http://localhost:3000 (port-forward)"
    echo "  • Prometheus: http://localhost:9090 (port-forward)"
    echo "  • Статус: make status-dev"
    echo "  • Логи: make logs-dev"
}

# Функція показу статусу
show_status() {
    log_info "Статус Atlas MCP системи:"
    echo ""
    
    # Docker Compose
    echo "🐳 Docker Compose:"
    if docker compose ps 2>/dev/null | grep -q "Up"; then
        echo "  ✅ Запущено"
        docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    else
        echo "  ❌ Не запущено"
    fi
    echo ""
    
    # Kind Кластери
    echo "☸️ Kubernetes (Kind):"
    if kind get clusters 2>/dev/null | grep -q atlas; then
        echo "  ✅ Кластери:"
        kind get clusters | grep atlas | sed 's/^/    • /'
    else
        echo "  ❌ Немає активних кластерів"
    fi
    echo ""
    
    # Локальні процеси
    echo "🐍 Локальні Python процеси:"
    if pgrep -f "atlas_core.py" >/dev/null; then
        echo "  ✅ Atlas Core запущено (PID: $(pgrep -f atlas_core.py))"
    else
        echo "  ❌ Atlas Core не запущено"
    fi
    
    # Порти
    echo ""
    echo "🌐 Зайняті порти:"
    local ports=("8000" "8080" "4002" "4003" "4004" "3000" "9090")
    for port in "${ports[@]}"; do
        if lsof -i :$port >/dev/null 2>&1; then
            local process=$(lsof -i :$port -t | head -1)
            local name=$(ps -p $process -o comm= 2>/dev/null || echo "unknown")
            echo "  • $port: $name (PID: $process)"
        fi
    done
}

# Головна функція
main() {
    case "${1:-help}" in
        "stop"|"clean")
            stop_all_atlas
            ;;
        "local")
            stop_all_atlas
            sleep 2
            check_ports
            start_local
            ;;
        "docker")
            stop_all_atlas
            sleep 2
            check_ports
            start_docker
            ;;
        "k8s"|"kubernetes")
            stop_all_atlas
            sleep 2
            check_ports
            start_kubernetes
            ;;
        "status")
            show_status
            ;;
        "ports")
            check_ports
            ;;
        "help"|*)
            echo "Atlas MCP Deployment Manager"
            echo ""
            echo "Використання: $0 {local|docker|k8s|status|stop|ports}"
            echo ""
            echo "Команди:"
            echo "  local      - Запустити в Local Python режимі"
            echo "  docker     - Запустити в Docker Compose режимі"
            echo "  k8s        - Запустити в Kubernetes режимі"
            echo "  status     - Показати статус всіх режимів"
            echo "  stop       - Зупинити всі Atlas сервіси"
            echo "  ports      - Перевірити зайняті порти"
            echo "  help       - Показати цю довідку"
            echo ""
            echo "Приклади:"
            echo "  $0 stop     # Зупинити все"
            echo "  $0 docker   # Запустити повний Docker стек"
            echo "  $0 k8s      # Запустити в Kubernetes"
            echo "  $0 status   # Перевірити статус"
            ;;
    esac
}

main "$@"
