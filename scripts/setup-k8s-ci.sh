#!/bin/bash
# Atlas MCP Kubernetes Cluster Setup for CI/CD
# Решает проблемы firewall блокировок через локальный kind кластер

set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-atlas-mcp-ci}"
NAMESPACE="${NAMESPACE:-atlas-mcp-dev}"
TIMEOUT="${TIMEOUT:-300}"
ARTIFACTS_DIR="${ARTIFACTS_DIR:-./k8s-artifacts}"

echo "🚀 Setting up Atlas MCP Kubernetes cluster..."
echo "Cluster: $CLUSTER_NAME"
echo "Namespace: $NAMESPACE"
echo "Artifacts: $ARTIFACTS_DIR"

# Функция для логирования
log() {
    echo "[$(date +'%H:%M:%S')] $*"
}

# Функция для проверки команд
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log "❌ Error: $1 is not installed"
        exit 1
    fi
    log "✅ $1 is available"
}

# Проверка зависимостей
log "🔍 Checking dependencies..."
check_command docker
check_command kubectl
check_command kind

# Создание artifacts директории
mkdir -p "$ARTIFACTS_DIR"

# Проверка и создание кластера
if kind get clusters | grep -q "^$CLUSTER_NAME$"; then
    log "📋 Cluster $CLUSTER_NAME already exists"
else
    log "🏗️ Creating kind cluster: $CLUSTER_NAME"
    
    # Создаем конфигурацию для kind
    cat > /tmp/kind-config.yaml << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: $CLUSTER_NAME
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 8090
    protocol: TCP
  - containerPort: 443
    hostPort: 8453
    protocol: TCP
- role: worker
networking:
  # Важно: используем стандартные CIDR для избежания конфликтов
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
EOF

    kind create cluster --config /tmp/kind-config.yaml --wait "${TIMEOUT}s"
    log "✅ Kind cluster created successfully"
fi

# Установка контекста kubectl
kubectl config use-context "kind-$CLUSTER_NAME"
log "🔧 Kubectl context set to kind-$CLUSTER_NAME"

# Проверка образов Docker
log "🐳 Checking Docker images..."
if ! docker images | grep -q "atlas-mcp"; then
    log "⚠️ No Atlas MCP images found, will need to build them"
    
    # Попытка сборки основных образов
    if [ -f "Dockerfile" ]; then
        log "🔨 Building atlas-core image..."
        docker build -t atlas-mcp/atlas-core:ci-latest . || log "⚠️ Failed to build atlas-core"
    fi
    
    if [ -f "3d_helmet_viewer/Dockerfile" ]; then
        log "🔨 Building atlas-frontend image..."
        docker build -t atlas-mcp/atlas-frontend:ci-latest ./3d_helmet_viewer/ || log "⚠️ Failed to build atlas-frontend"
    fi
    
    if [ -f "Dockerfile.mcp-automation" ]; then
        log "🔨 Building mcp-automation image..."
        docker build -t atlas-mcp/mcp-automation:ci-latest -f Dockerfile.mcp-automation . || log "⚠️ Failed to build mcp-automation"
    fi
    
    if [ -f "Dockerfile.mcp-automator" ]; then
        log "🔨 Building mcp-automator image..."
        docker build -t atlas-mcp/mcp-automator:ci-latest -f Dockerfile.mcp-automator . || log "⚠️ Failed to build mcp-automator"
    fi
fi

# Загрузка образов в kind
log "📦 Loading Docker images into kind cluster..."
for image in atlas-mcp/atlas-core:ci-latest atlas-mcp/atlas-frontend:ci-latest atlas-mcp/mcp-automation:ci-latest atlas-mcp/mcp-automator:ci-latest; do
    if docker images | grep -q "$(echo $image | cut -d: -f1)"; then
        log "Loading $image..."
        kind load docker-image "$image" --name "$CLUSTER_NAME" || log "⚠️ Failed to load $image"
    else
        log "⚠️ Image $image not found, skipping"
    fi
done

# Создание namespace
log "🏠 Creating namespace: $NAMESPACE"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Применение Kubernetes манифестов
if [ -d "k8s/overlays/development" ]; then
    log "🎯 Applying Kubernetes manifests..."
    kubectl apply -k k8s/overlays/development || log "⚠️ Failed to apply some manifests"
    
    log "⏳ Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout="${TIMEOUT}s" deployment --all -n "$NAMESPACE" || log "⚠️ Some deployments failed to become ready"
else
    log "⚠️ No k8s/overlays/development found, skipping manifest application"
fi

# Сбор статуса кластера для артефактов
log "📊 Collecting cluster status..."

# Общий статус кластера
kubectl cluster-info > "$ARTIFACTS_DIR/cluster-info.txt" 2>&1 || true
kubectl get nodes -o wide > "$ARTIFACTS_DIR/nodes.txt" 2>&1 || true

# Статус в namespace
kubectl get all -n "$NAMESPACE" -o wide > "$ARTIFACTS_DIR/namespace-all.txt" 2>&1 || true
kubectl get pods -n "$NAMESPACE" -o yaml > "$ARTIFACTS_DIR/pods.yaml" 2>&1 || true
kubectl get deployments -n "$NAMESPACE" -o wide > "$ARTIFACTS_DIR/deployments.txt" 2>&1 || true
kubectl get services -n "$NAMESPACE" -o wide > "$ARTIFACTS_DIR/services.txt" 2>&1 || true

# Describe проблемных pods
kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running -o name 2>/dev/null | while read pod; do
    if [ -n "$pod" ]; then
        kubectl describe "$pod" -n "$NAMESPACE" > "$ARTIFACTS_DIR/$(basename $pod)-describe.txt" 2>&1 || true
    fi
done

# Логи основных сервисов
for deployment in atlas-core atlas-frontend mcp-automation mcp-automator; do
    if kubectl get deployment "$deployment" -n "$NAMESPACE" &>/dev/null; then
        log "📋 Collecting logs for $deployment..."
        kubectl logs -l "app.kubernetes.io/name=$deployment" -n "$NAMESPACE" --tail=100 > "$ARTIFACTS_DIR/${deployment}-logs.txt" 2>&1 || true
    fi
done

# Функция для безопасного port-forward тестирования
test_service() {
    local service=$1
    local port=$2
    local health_path=${3:-"/health"}
    local namespace=${4:-$NAMESPACE}
    
    log "🧪 Testing service: $service:$port"
    
    # Запуск port-forward в фоне
    kubectl port-forward "svc/$service" "$port:$port" -n "$namespace" > "$ARTIFACTS_DIR/${service}-portforward.log" 2>&1 &
    local pf_pid=$!
    
    # Ждем немного для установки port-forward
    sleep 5
    
    # Тестируем подключение
    local status_file="$ARTIFACTS_DIR/${service}-status.json"
    if curl -s --connect-timeout 5 --max-time 10 "http://127.0.0.1:$port$health_path" > "$status_file" 2>&1; then
        log "✅ $service responds successfully"
        echo "SUCCESS" > "$ARTIFACTS_DIR/${service}-test-result.txt"
    else
        log "❌ $service test failed"
        echo "FAILED" > "$ARTIFACTS_DIR/${service}-test-result.txt"
        curl -s --connect-timeout 5 --max-time 10 "http://127.0.0.1:$port$health_path" > "$status_file" 2>&1 || true
    fi
    
    # Убиваем port-forward
    kill $pf_pid 2>/dev/null || true
    wait $pf_pid 2>/dev/null || true
}

# Тестирование сервисов через localhost (обход firewall)
log "🧪 Testing services via localhost port-forward..."

# Тестируем Atlas Core
if kubectl get service atlas-core-service -n "$NAMESPACE" &>/dev/null; then
    test_service "atlas-core-service" "8000" "/status" "$NAMESPACE"
fi

# Тестируем Atlas Frontend
if kubectl get service atlas-frontend-service -n "$NAMESPACE" &>/dev/null; then
    test_service "atlas-frontend-service" "8080" "/health" "$NAMESPACE"
fi

# Тестируем MCP сервисы
for service in mcp-automation-service mcp-automator-service mcp-tts-service; do
    if kubectl get service "$service" -n "$NAMESPACE" &>/dev/null; then
        port=""
        case $service in
            mcp-automation-service) port="4002" ;;
            mcp-automator-service) port="4003" ;;
            mcp-tts-service) port="4004" ;;
        esac
        if [ -n "$port" ]; then
            test_service "$service" "$port" "/health" "$NAMESPACE"
        fi
    fi
done

# Создание итогового отчета
log "📝 Creating summary report..."
cat > "$ARTIFACTS_DIR/summary.md" << EOF
# Atlas MCP Kubernetes Deployment Summary

**Cluster:** $CLUSTER_NAME
**Namespace:** $NAMESPACE
**Timestamp:** $(date)

## Deployment Status

\`\`\`
$(kubectl get deployments -n "$NAMESPACE" 2>/dev/null || echo "No deployments found")
\`\`\`

## Service Status

\`\`\`
$(kubectl get services -n "$NAMESPACE" 2>/dev/null || echo "No services found")
\`\`\`

## Pod Status

\`\`\`
$(kubectl get pods -n "$NAMESPACE" 2>/dev/null || echo "No pods found")
\`\`\`

## Service Tests

EOF

# Добавляем результаты тестов в отчет
for result_file in "$ARTIFACTS_DIR"/*-test-result.txt; do
    if [ -f "$result_file" ]; then
        service=$(basename "$result_file" -test-result.txt)
        result=$(cat "$result_file")
        echo "- **$service:** $result" >> "$ARTIFACTS_DIR/summary.md"
    fi
done

echo "" >> "$ARTIFACTS_DIR/summary.md"
echo "## Files Generated" >> "$ARTIFACTS_DIR/summary.md"
echo "" >> "$ARTIFACTS_DIR/summary.md"
ls -la "$ARTIFACTS_DIR" | tail -n +2 | awk '{print "- " $9 " (" $5 " bytes)"}' >> "$ARTIFACTS_DIR/summary.md"

log "✅ Kubernetes setup completed!"
log "📁 Artifacts saved to: $ARTIFACTS_DIR"
log "📄 Summary report: $ARTIFACTS_DIR/summary.md"

# Опциональная очистка кластера
if [ "${CLEANUP_CLUSTER:-false}" = "true" ]; then
    log "🧹 Cleaning up cluster: $CLUSTER_NAME"
    kind delete cluster --name "$CLUSTER_NAME"
fi

exit 0
