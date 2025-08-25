#!/bin/bash

# Atlas MCP Kubernetes Management Script
# Скрипт для управління Kubernetes кластером Atlas MCP

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="${SCRIPT_DIR}/k8s"

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функція логування
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Перевірка залежностей
check_dependencies() {
    log "Перевірка залежностей..."
    
    if ! command -v kubectl &> /dev/null; then
        error "kubectl не знайдено. Будь ласка, встановіть kubectl."
    fi
    
    if ! command -v kustomize &> /dev/null; then
        warn "kustomize не знайдено. Спробую використати kubectl kustomize..."
        if ! kubectl kustomize --help &> /dev/null; then
            error "Ні kustomize, ні kubectl kustomize не доступні."
        fi
        KUSTOMIZE_CMD="kubectl kustomize"
    else
        KUSTOMIZE_CMD="kustomize build"
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        error "Не можу підключитися до Kubernetes кластера."
    fi
    
    log "Всі залежності встановлені ✓"
}

# Створення namespace
create_namespace() {
    local env=${1:-development}
    local namespace="atlas-mcp"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    log "Створення namespace: $namespace"
    kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -
    kubectl label namespace "$namespace" name="$namespace" --overwrite
}

# Конфігурація Ollama host підключення для macOS Kind кластера
configure_ollama_host() {
    local env=${1:-development}
    local namespace="atlas-mcp"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    log "Конфігурація Ollama host підключення для $env середовища..."
    
    # Detect host IP for Kind cluster on macOS
    local host_ip=""
    
    # Method 1: Try to get Kind network gateway
    if command -v docker &> /dev/null; then
        # Get Kind cluster container name
        local kind_container=$(docker ps --filter "label=io.x-k8s.kind.cluster=atlas-mcp-dev" --format "{{.Names}}" | head -1)
        if [ -n "$kind_container" ]; then
            # Get the gateway IP from Kind container
            host_ip=$(docker exec "$kind_container" ip route show default | awk '/default/ {print $3}' | head -1)
            log "Detected Kind gateway IP: $host_ip"
        fi
    fi
    
    # Method 2: Fallback to common Kind gateway IPs on macOS
    if [ -z "$host_ip" ] || [ "$host_ip" = "127.0.0.1" ]; then
        # Common Kind gateway IPs on macOS Docker Desktop
        for ip in "172.18.0.1" "172.17.0.1" "192.168.65.2"; do
            if ping -c 1 -W 1000 "$ip" &> /dev/null; then
                host_ip="$ip"
                log "Using reachable host IP: $host_ip"
                break
            fi
        done
    fi
    
    # Method 3: Final fallback
    if [ -z "$host_ip" ]; then
        host_ip="172.18.0.1"  # Most common Kind gateway on macOS
        warn "Using default Kind gateway IP: $host_ip"
    fi
    
    # Update the Ollama host service endpoint
    log "Оновлення Ollama host service endpoint з IP: $host_ip"
    
    kubectl patch endpoints ollama-host-service -n "$namespace" --type='json' \
        -p="[{\"op\": \"replace\", \"path\": \"/subsets/0/addresses/0/ip\", \"value\": \"$host_ip\"}]" || {
        # If patch fails, create the endpoint
        cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Endpoints
metadata:
  name: ollama-host-service
  namespace: $namespace
  annotations:
    atlas.mcp/dynamic-endpoint: "true"
    atlas.mcp/host-ip: "$host_ip"
subsets:
- addresses:
  - ip: $host_ip
  ports:
  - name: http
    port: 11434
    protocol: TCP
EOF
    }
    
    log "Ollama host service налаштовано для IP: $host_ip ✓"
    
    # Verify Ollama connectivity
    log "Перевірка доступності Ollama на хості..."
    if curl -s --connect-timeout 5 "http://$host_ip:11434/api/tags" > /dev/null; then
        log "Ollama доступний на $host_ip:11434 ✓"
    else
        warn "Ollama недоступний на $host_ip:11434. Переконайтеся, що Ollama запущений на хост-системі."
        warn "Запустіть: brew services start ollama"
    fi
}

# Встановлення Atlas MCP
install() {
    local env=${1:-development}
    
    log "Встановлення Atlas MCP в середовище: $env"
    
    check_dependencies
    create_namespace "$env"
    
    # Застосування конфігурації
    if [ "$env" = "base" ]; then
        log "Застосування базової конфігурації..."
        $KUSTOMIZE_CMD "$K8S_DIR/base" | kubectl apply -f -
    else
        log "Застосування конфігурації для середовища: $env"
        $KUSTOMIZE_CMD "$K8S_DIR/overlays/$env" | kubectl apply -f -
    fi
    
    # Конфігурація Ollama host підключення для macOS Kind кластера
    configure_ollama_host "$env"
    
    log "Очікування готовності подів..."
    wait_for_pods "$env"
    
    log "Atlas MCP успішно встановлено! ✓"
    show_status "$env"
}

# Оновлення Atlas MCP
update() {
    local env=${1:-development}
    
    log "Оновлення Atlas MCP в середовищі: $env"
    
    check_dependencies
    
    # Застосування конфігурації
    if [ "$env" = "base" ]; then
        $KUSTOMIZE_CMD "$K8S_DIR/base" | kubectl apply -f -
    else
        $KUSTOMIZE_CMD "$K8S_DIR/overlays/$env" | kubectl apply -f -
    fi
    
    # Оновлення конфігурації Ollama host підключення
    configure_ollama_host "$env"
    
    log "Перезапуск деплойментів для оновлення..."
    restart_deployments "$env"
    
    log "Atlas MCP успішно оновлено! ✓"
}

# Видалення Atlas MCP
uninstall() {
    local env=${1:-development}
    
    warn "УВАГА: Це видалить всі ресурси Atlas MCP в середовищі: $env"
    read -p "Ви впевнені? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Операцію скасовано."
        return
    fi
    
    log "Видалення Atlas MCP з середовища: $env"
    
    if [ "$env" = "base" ]; then
        $KUSTOMIZE_CMD "$K8S_DIR/base" | kubectl delete -f - --ignore-not-found=true
    else
        $KUSTOMIZE_CMD "$K8S_DIR/overlays/$env" | kubectl delete -f - --ignore-not-found=true
    fi
    
    # Видалення namespace
    local namespace="atlas-mcp"
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    kubectl delete namespace "$namespace" --ignore-not-found=true
    
    log "Atlas MCP успішно видалено! ✓"
}

# Перезапуск деплойментів
restart_deployments() {
    local env=${1:-development}
    local namespace="atlas-mcp"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    log "Перезапуск деплойментів в namespace: $namespace"
    
    kubectl rollout restart deployment -n "$namespace"
    kubectl rollout status deployment -n "$namespace" --timeout=300s
}

# Очікування готовності подів
wait_for_pods() {
    local env=${1:-development}
    local namespace="atlas-mcp"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    log "Очікування готовності подів в namespace: $namespace"
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/part-of=atlas-autonomous-system -n "$namespace" --timeout=300s
}

# Показати статус
show_status() {
    local env=${1:-development}
    local namespace="atlas-mcp"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    info "=== Статус Atlas MCP в середовищі: $env ==="
    echo
    
    info "Поди:"
    kubectl get pods -n "$namespace" -o wide
    echo
    
    info "Сервіси:"
    kubectl get services -n "$namespace"
    echo
    
    info "Ingress:"
    kubectl get ingress -n "$namespace" 2>/dev/null || echo "Ingress не знайдено"
    echo
    
    info "HPA (Horizontal Pod Autoscaler):"
    kubectl get hpa -n "$namespace" 2>/dev/null || echo "HPA не знайдено"
    echo
    
    info "PVC (Persistent Volume Claims):"
    kubectl get pvc -n "$namespace"
    echo
}

# Показати логи
show_logs() {
    local env=${1:-development}
    local service=${2:-atlas-core}
    local namespace="atlas-mcp"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    log "Показ логів для сервісу: $service в середовищі: $env"
    kubectl logs -f -l app.kubernetes.io/name="$service" -n "$namespace" --tail=100
}

# Скалювання сервісу
scale() {
    local env=${1:-development}
    local service=${2:-atlas-core}
    local replicas=${3:-2}
    local namespace="atlas-mcp"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    log "Скалювання сервісу $service до $replicas реплік в середовищі: $env"
    kubectl scale deployment "$service" --replicas="$replicas" -n "$namespace"
    kubectl rollout status deployment "$service" -n "$namespace"
}

# Вхід в под
exec_pod() {
    local env=${1:-development}
    local service=${2:-atlas-core}
    local namespace="atlas-mcp"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    local pod=$(kubectl get pods -n "$namespace" -l app.kubernetes.io/name="$service" -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$pod" ]; then
        error "Под для сервісу $service не знайдено"
    fi
    
    log "Підключення до поду: $pod"
    kubectl exec -it "$pod" -n "$namespace" -- /bin/bash
}

# Резервне копіювання
backup() {
    local env=${1:-development}
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    
    log "Створення резервної копії для середовища: $env"
    mkdir -p "$backup_dir"
    
    # Експорт конфігурації
    if [ "$env" = "base" ]; then
        $KUSTOMIZE_CMD "$K8S_DIR/base" > "$backup_dir/atlas-mcp-base.yaml"
    else
        $KUSTOMIZE_CMD "$K8S_DIR/overlays/$env" > "$backup_dir/atlas-mcp-$env.yaml"
    fi
    
    # Експорт даних PVC (якщо можливо)
    # TODO: Додати експорт даних з PVC
    
    log "Резервна копія створена в: $backup_dir"
}

# Відновлення з резервної копії
restore() {
    local backup_file=${1}
    
    if [ ! -f "$backup_file" ]; then
        error "Файл резервної копії не знайдено: $backup_file"
    fi
    
    warn "Відновлення з резервної копії: $backup_file"
    read -p "Ви впевнені? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Операцію скасовано."
        return
    fi
    
    kubectl apply -f "$backup_file"
    log "Відновлення завершено! ✓"
}

# Моніторинг
monitoring() {
    local env=${1:-development}
    local namespace="atlas-mcp"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    info "=== Моніторинг Atlas MCP ==="
    echo
    
    info "Топ подів за використанням CPU:"
    kubectl top pods -n "$namespace" --sort-by=cpu 2>/dev/null || echo "Metrics server не доступний"
    echo
    
    info "Топ подів за використанням пам'яті:"
    kubectl top pods -n "$namespace" --sort-by=memory 2>/dev/null || echo "Metrics server не доступний"
    echo
    
    info "Події (останні 10):"
    kubectl get events -n "$namespace" --sort-by='.lastTimestamp' | tail -10
    echo
    
    info "Для доступу до Grafana (якщо встановлено):"
    info "kubectl port-forward svc/grafana-service 3000:3000 -n $namespace"
    echo
    
    info "Для доступу до Prometheus (якщо встановлено):"
    info "kubectl port-forward svc/prometheus-service 9090:9090 -n $namespace"
}

# Діагностика
diagnose() {
    local env=${1:-development}
    local namespace="atlas-mcp"
    
    if [ "$env" = "production" ]; then
        namespace="atlas-mcp-prod"
    elif [ "$env" = "development" ]; then
        namespace="atlas-mcp-dev"
    fi
    
    info "=== Діагностика Atlas MCP ==="
    echo
    
    info "Перевірка готовності подів:"
    kubectl get pods -n "$namespace" | grep -v Running | grep -v Completed || echo "Всі поди в стані Running ✓"
    echo
    
    info "Перевірка ресурсів:"
    kubectl describe nodes | grep -A 5 "Allocated resources" || echo "Не можу отримати інформацію про ноди"
    echo
    
    info "Перевірка PVC:"
    kubectl get pvc -n "$namespace" | grep -v Bound || echo "Всі PVC підключені ✓"
    echo
    
    info "Останні помилки в логах:"
    kubectl logs -l app.kubernetes.io/part-of=atlas-autonomous-system -n "$namespace" --tail=50 | grep -i error || echo "Помилок не знайдено ✓"
}

# Допомога
show_help() {
    cat << EOF
Atlas MCP Kubernetes Management Script

Використання: $0 <команда> [опції]

Команди:
  install <env>           Встановити Atlas MCP (env: development|production|base)
  update <env>            Оновити Atlas MCP
  uninstall <env>         Видалити Atlas MCP
  status <env>            Показати статус
  logs <env> <service>    Показати логи сервісу
  scale <env> <service> <replicas>  Скалювати сервіс
  exec <env> <service>    Увійти в под сервісу
  restart <env>           Перезапустити всі деплойменти
  backup <env>            Створити резервну копію
  restore <file>          Відновити з резервної копії
  monitoring <env>        Показати моніторинг
  diagnose <env>          Виконати діагностику
  help                    Показати цю допомогу

Середовища:
  development    Середовище розробки (за замовчуванням)
  production     Продуктивне середовище
  base           Базова конфігурація без overlay

Сервіси:
  atlas-core         Основний сервіс Atlas
  atlas-frontend     Frontend Atlas
  mcp-automation     MCP Automation сервіс
  mcp-automator      MCP Automator сервіс
  mcp-tts           MCP TTS сервіс
  mcp-playwright    MCP Playwright сервіс
  redis             Redis база даних
  qdrant            Qdrant векторна база даних

Приклади:
  $0 install development
  $0 status production
  $0 logs development atlas-core
  $0 scale production atlas-frontend 5
  $0 monitoring development

EOF
}

# Головна функція
main() {
    case "${1:-help}" in
        install)
            install "${2:-development}"
            ;;
        update)
            update "${2:-development}"
            ;;
        uninstall)
            uninstall "${2:-development}"
            ;;
        status)
            show_status "${2:-development}"
            ;;
        logs)
            show_logs "${2:-development}" "${3:-atlas-core}"
            ;;
        scale)
            scale "${2:-development}" "${3:-atlas-core}" "${4:-2}"
            ;;
        exec)
            exec_pod "${2:-development}" "${3:-atlas-core}"
            ;;
        restart)
            restart_deployments "${2:-development}"
            ;;
        backup)
            backup "${2:-development}"
            ;;
        restore)
            restore "${2}"
            ;;
        monitoring)
            monitoring "${2:-development}"
            ;;
        diagnose)
            diagnose "${2:-development}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Невідома команда: $1. Використайте '$0 help' для допомоги."
            ;;
    esac
}

# Запуск скрипта
main "$@"
