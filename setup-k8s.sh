#!/bin/bash

# Atlas MCP Kubernetes Quick Setup
# Скрипт для швидкого налаштування та розгортання Atlas MCP в Kubernetes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# ASCII Art
show_banner() {
    echo -e "${PURPLE}"
    cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║      █████╗ ████████╗██╗      █████╗ ███████╗     ███╗   ███╗║
    ║     ██╔══██╗╚══██╔══╝██║     ██╔══██╗██╔════╝     ████╗ ████║║
    ║     ███████║   ██║   ██║     ███████║███████╗     ██╔████╔██║║
    ║     ██╔══██║   ██║   ██║     ██╔══██║╚════██║     ██║╚██╔╝██║║
    ║     ██║  ██║   ██║   ███████╗██║  ██║███████║     ██║ ╚═╝ ██║║
    ║     ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝     ╚═╝     ╚═╝║
    ║                                                               ║
    ║                 Kubernetes Professional Setup                 ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓ $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] ❌ $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] ℹ️  $1${NC}"
}

step() {
    echo -e "${PURPLE}[STEP] 🚀 $1${NC}"
}

# Перевірка передумов
check_prerequisites() {
    step "Перевірка передумов..."
    
    # Перевірка kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl не встановлено. Встановіть kubectl для продовження."
    fi
    
    # Перевірка kustomize або kubectl kustomize
    if ! command -v kustomize &> /dev/null && ! kubectl kustomize --help &> /dev/null; then
        error "kustomize або kubectl kustomize не доступні."
    fi
    
    # Перевірка Docker
    if ! command -v docker &> /dev/null; then
        error "Docker не встановлено. Встановіть Docker для побудови образів."
    fi
    
    # Перевірка make
    if ! command -v make &> /dev/null; then
        warn "make не встановлено. Рекомендується встановити для зручності."
    fi
    
    # Перевірка підключення до кластера
    if ! kubectl cluster-info &> /dev/null; then
        error "Не можу підключитися до Kubernetes кластера. Перевірте конфігурацію kubectl."
    fi
    
    log "Всі передумови виконані ✨"
}

# Встановлення базових компонентів кластера
setup_cluster_components() {
    step "Встановлення базових компонентів кластера..."
    
    # Metrics Server
    info "Встановлення Metrics Server..."
    if ! kubectl get deployment metrics-server -n kube-system &> /dev/null; then
        kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
        log "Metrics Server встановлено"
    else
        log "Metrics Server вже встановлено"
    fi
    
    # NGINX Ingress Controller
    info "Встановлення NGINX Ingress Controller..."
    if ! kubectl get namespace ingress-nginx &> /dev/null; then
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
        log "NGINX Ingress Controller встановлено"
        
        info "Очікування готовності NGINX Ingress..."
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/component=controller \
            --timeout=300s
        log "NGINX Ingress готовий"
    else
        log "NGINX Ingress Controller вже встановлено"
    fi
}

# Побудова Docker образів
build_images() {
    step "Побудова Docker образів..."
    
    info "Побудова Atlas Core образу..."
    docker build -t atlas-mcp/atlas-core:latest "$SCRIPT_DIR" || error "Не вдалося побудувати Atlas Core образ"
    
    info "Побудова Atlas Frontend образу..."
    docker build -t atlas-mcp/atlas-frontend:latest "$SCRIPT_DIR/3d_helmet_viewer/" || error "Не вдалося побудувати Atlas Frontend образ"
    
    info "Побудова MCP Automation образу..."
    docker build -t atlas-mcp/mcp-automation:latest -f "$SCRIPT_DIR/Dockerfile.mcp-automation" "$SCRIPT_DIR" || error "Не вдалося побудувати MCP Automation образ"
    
    info "Побудова MCP Automator образу..."
    docker build -t atlas-mcp/mcp-automator:latest -f "$SCRIPT_DIR/Dockerfile.mcp-automator" "$SCRIPT_DIR" || error "Не вдалося побудувати MCP Automator образ"
    
    # Перевірка наявності TTS сервісу
    if [ -d "$SCRIPT_DIR/services/tts_mcp_adapter" ]; then
        info "Побудова MCP TTS образу..."
        docker build -t atlas-mcp/mcp-tts:latest "$SCRIPT_DIR/services/tts_mcp_adapter/" || warn "Не вдалося побудувати MCP TTS образ"
    else
        warn "Директорія TTS сервісу не знайдена, пропускаємо побудову образу"
    fi
    
    log "Всі образи побудовано успішно 🐳"
}

# Створення secrets
create_secrets() {
    local env=$1
    local namespace="atlas-mcp-dev"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    fi
    
    step "Створення secrets для середовища: $env..."
    
    # Створення namespace якщо не існує
    kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -
    
    if [ "$env" = "development" ]; then
        kubectl create secret generic atlas-secrets \
            --from-literal=GOOGLE_TTS_API_KEY="" \
            --from-literal=GRAFANA_ADMIN_PASSWORD="dev_admin" \
            --namespace="$namespace" \
            --dry-run=client -o yaml | kubectl apply -f -
        log "Development secrets створено"
    else
        # Production secrets
        if [ -d "secrets" ]; then
            kubectl create secret generic atlas-secrets \
                --from-file=GOOGLE_TTS_API_KEY=secrets/google-tts-api-key.txt \
                --from-file=GRAFANA_ADMIN_PASSWORD=secrets/grafana-admin-password.txt \
                --namespace="$namespace" \
                --dry-run=client -o yaml | kubectl apply -f -
            log "Production secrets створено з файлів"
        else
            warn "Директорія secrets/ не знайдена для production. Створюю з базовими значеннями."
            kubectl create secret generic atlas-secrets \
                --from-literal=GOOGLE_TTS_API_KEY="" \
                --from-literal=GRAFANA_ADMIN_PASSWORD="change-me-in-production" \
                --namespace="$namespace" \
                --dry-run=client -o yaml | kubectl apply -f -
        fi
    fi
}

# Розгортання Atlas MCP
deploy_atlas() {
    local env=$1
    
    step "Розгортання Atlas MCP в середовище: $env..."
    
    create_secrets "$env"
    
    # Застосування конфігурації через kustomize
    if command -v kustomize &> /dev/null; then
        kustomize build "$SCRIPT_DIR/k8s/overlays/$env" | kubectl apply -f -
    else
        kubectl kustomize "$SCRIPT_DIR/k8s/overlays/$env" | kubectl apply -f -
    fi
    
    log "Конфігурація застосована"
    
    # Очікування готовності подів
    local namespace="atlas-mcp-dev"
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    fi
    
    info "Очікування готовності подів..."
    kubectl wait --for=condition=Ready pod \
        -l app.kubernetes.io/part-of=atlas-autonomous-system \
        -n "$namespace" \
        --timeout=600s || warn "Не всі поди готові, але продовжуємо..."
    
    log "Atlas MCP розгорнуто успішно! 🎉"
}

# Показ статусу
show_status() {
    local env=$1
    local namespace="atlas-mcp-dev"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    fi
    
    step "Статус Atlas MCP в середовищі: $env"
    
    info "Поди:"
    kubectl get pods -n "$namespace" -o wide
    echo
    
    info "Сервіси:"
    kubectl get services -n "$namespace"
    echo
    
    info "Ingress:"
    kubectl get ingress -n "$namespace" 2>/dev/null || echo "Ingress не знайдено"
    echo
    
    info "PVC:"
    kubectl get pvc -n "$namespace"
    echo
}

# Показ інструкцій доступу
show_access_instructions() {
    local env=$1
    local namespace="atlas-mcp-dev"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    fi
    
    step "Інструкції доступу до Atlas MCP"
    
    echo -e "${BLUE}📱 Основні сервіси:${NC}"
    echo -e "${GREEN}  Atlas Frontend:${NC}"
    echo -e "    kubectl port-forward svc/atlas-frontend-service 8080:8080 -n $namespace"
    echo -e "    Відкрийте: http://localhost:8080"
    echo
    
    echo -e "${GREEN}  Atlas API:${NC}"
    echo -e "    kubectl port-forward svc/atlas-core-service 8000:8000 -n $namespace"
    echo -e "    Відкрийте: http://localhost:8000"
    echo
    
    echo -e "${BLUE}📊 Моніторинг:${NC}"
    echo -e "${GREEN}  Grafana:${NC}"
    echo -e "    kubectl port-forward svc/grafana-service 3000:3000 -n $namespace"
    echo -e "    Відкрийте: http://localhost:3000 (admin/dev_admin)"
    echo
    
    echo -e "${GREEN}  Prometheus:${NC}"
    echo -e "    kubectl port-forward svc/prometheus-service 9090:9090 -n $namespace"
    echo -e "    Відкрийте: http://localhost:9090"
    echo
    
    echo -e "${BLUE}🛠️ Управління:${NC}"
    echo -e "${GREEN}  Статус:${NC} ./k8s-manage.sh status $env"
    echo -e "${GREEN}  Логи:${NC} ./k8s-manage.sh logs $env atlas-core"
    echo -e "${GREEN}  Масштабування:${NC} ./k8s-manage.sh scale $env atlas-frontend 5"
    echo -e "${GREEN}  Перезапуск:${NC} ./k8s-manage.sh restart $env"
    echo
    
    if command -v make &> /dev/null; then
        echo -e "${BLUE}📋 Make команди:${NC}"
        echo -e "${GREEN}  make status-$env${NC} - статус"
        echo -e "${GREEN}  make logs-$env${NC} - логи"
        echo -e "${GREEN}  make monitoring-$env${NC} - моніторинг"
        echo -e "${GREEN}  make port-forward-atlas-$env${NC} - доступ до Atlas"
        echo
    fi
}

# Інтерактивний режим
interactive_setup() {
    show_banner
    
    echo -e "${BLUE}Ласкаво просимо до Atlas MCP Kubernetes Setup! 🚀${NC}"
    echo
    
    # Вибір середовища
    echo -e "${YELLOW}Оберіть середовище розгортання:${NC}"
    echo "1) Development (рекомендовано для початку)"
    echo "2) Production"
    echo
    read -p "Ваш вибір (1-2): " choice
    
    case $choice in
        1)
            ENVIRONMENT="development"
            ;;
        2)
            ENVIRONMENT="production"
            echo -e "${YELLOW}⚠️  Production режим потребує додаткової конфігурації!${NC}"
            ;;
        *)
            ENVIRONMENT="development"
            warn "Невірний вибір, використовуємо development"
            ;;
    esac
    
    echo
    echo -e "${BLUE}Обране середовище: ${GREEN}$ENVIRONMENT${NC}"
    echo
    
    # Підтвердження
    read -p "Продовжити встановлення? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Встановлення скасовано користувачем"
    fi
    
    # Виконання встановлення
    check_prerequisites
    setup_cluster_components
    build_images
    deploy_atlas "$ENVIRONMENT"
    show_status "$ENVIRONMENT"
    show_access_instructions "$ENVIRONMENT"
    
    echo
    log "🎉 Atlas MCP успішно встановлено в середовище $ENVIRONMENT!"
    echo
    echo -e "${GREEN}Наступні кроки:${NC}"
    echo "1. Перевірте статус подів: kubectl get pods -n atlas-mcp-$([ "$ENVIRONMENT" = "production" ] && echo "prod" || echo "dev")"
    echo "2. Налаштуйте порт-форвардинг для доступу до сервісів"
    echo "3. Відкрийте Atlas Frontend у браузері"
    echo "4. Перегляньте документацію в k8s/README.md"
    echo
    echo -e "${BLUE}Приємного користування Atlas MCP! 🌟${NC}"
}

# Автоматичний режим
auto_setup() {
    local env=${1:-development}
    
    show_banner
    
    log "Запуск автоматичного встановлення для середовища: $env"
    
    check_prerequisites
    setup_cluster_components
    build_images
    deploy_atlas "$env"
    show_status "$env"
    show_access_instructions "$env"
    
    log "Автоматичне встановлення завершено! 🎉"
}

# Допомога
show_help() {
    show_banner
    
    cat << EOF
Atlas MCP Kubernetes Quick Setup

Використання:
  $0                          # Інтерактивний режим
  $0 <environment>            # Автоматичне встановлення
  $0 --help                   # Показати цю допомогу

Середовища:
  development                 # Development середовище (за замовчуванням)
  production                  # Production середовище

Приклади:
  $0                          # Інтерактивне встановлення
  $0 development              # Автоматичне встановлення в development
  $0 production               # Автоматичне встановлення в production

Передумови:
  - kubectl (підключений до кластера)
  - Docker
  - kustomize або kubectl kustomize
  - make (опціонально, для зручності)

Додаткові команди після встановлення:
  ./k8s-manage.sh help        # Повна допомога по управлінню
  make help                   # Make команди (якщо доступно)

EOF
}

# Головна функція
main() {
    case "${1:-interactive}" in
        development|production)
            auto_setup "$1"
            ;;
        interactive)
            interactive_setup
            ;;
        --help|-h|help)
            show_help
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
}

# Обробка сигналів
trap 'echo -e "\n${RED}Встановлення перервано користувачем${NC}"; exit 1' INT TERM

# Запуск
main "$@"
