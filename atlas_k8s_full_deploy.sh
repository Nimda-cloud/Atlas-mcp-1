#!/bin/bash

# Atlas MCP - Полное развертывание Kubernetes стека
# Автор: Atlas MCP Team
# Описание: Автоматизированное развертывание и настройка всего стека Atlas MCP в Kubernetes

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Конфигурация
NAMESPACE="atlas-mcp-dev"
CLUSTER_NAME="atlas-mcp-cluster"
TIMEOUT="600s"
WAIT_TIME=30

# Логирование
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Проверка зависимостей
check_dependencies() {
    log "Проверка зависимостей..."
    
    local deps=("kubectl" "docker" "kind")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [[ ${#missing[@]} -ne 0 ]]; then
        error "Отсутствуют зависимости: ${missing[*]}"
        exit 1
    fi
    
    success "Все зависимости установлены"
}

# Проверка Docker
check_docker() {
    log "Проверка Docker..."
    
    if ! docker info &> /dev/null; then
        error "Docker не запущен или недоступен"
        exit 1
    fi
    
    success "Docker доступен"
}

# Создание кластера Kind
create_cluster() {
    log "Создание Kind кластера..."
    
    # Проверяем существующий кластер
    if kind get clusters | grep -q "$CLUSTER_NAME"; then
        warning "Кластер $CLUSTER_NAME уже существует. Удаляем..."
        kind delete cluster --name "$CLUSTER_NAME"
        sleep 5
    fi
    
    # Создаем новый кластер
    if [[ -f "kind-config.yaml" ]]; then
        kind create cluster --name "$CLUSTER_NAME" --config kind-config.yaml
    else
        # Создаем базовую конфигурацию
        cat > kind-config-temp.yaml << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  apiServerAddress: "127.0.0.1"
  apiServerPort: 6443
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
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
- role: worker
- role: worker
EOF
        kind create cluster --name "$CLUSTER_NAME" --config kind-config-temp.yaml
        rm -f kind-config-temp.yaml
    fi
    
    # Настройка kubectl контекста
    kubectl cluster-info --context "kind-$CLUSTER_NAME"
    kubectl config use-context "kind-$CLUSTER_NAME"
    
    success "Кластер Kind создан и настроен"
}

# Сборка Docker образов
build_images() {
    log "Сборка Docker образов..."
    
    # Список образов для сборки
    local images=(
        "atlas-core:latest"
        "atlas-frontend:latest"
        "mcp-automation:latest"
        "mcp-automator:latest"
        "mcp-playwright:latest"
        "mcp-tts:latest"
    )
    
    # Основной образ Atlas Core
    log "Сборка atlas-core..."
    docker build -t atlas-core:latest . || {
        error "Ошибка сборки atlas-core"
        return 1
    }
    
    # 3D Frontend
    log "Сборка atlas-frontend..."
    docker build -t atlas-frontend:latest ./3d_helmet_viewer/ || {
        error "Ошибка сборки atlas-frontend"
        return 1
    }
    
    # MCP Services
    log "Сборка mcp-automation..."
    docker build -t mcp-automation:latest -f Dockerfile.mcp-automation . || {
        warning "Не удалось собрать mcp-automation"
    }
    
    log "Сборка mcp-automator..."
    docker build -t mcp-automator:latest -f Dockerfile.mcp-automator . || {
        warning "Не удалось собрать mcp-automator"
    }
    
    # Загрузка образов в Kind
    log "Загрузка образов в Kind кластер..."
    for image in "${images[@]}"; do
        if docker images | grep -q "${image%:*}"; then
            kind load docker-image "$image" --name "$CLUSTER_NAME"
            success "Загружен образ: $image"
        else
            warning "Образ не найден: $image"
        fi
    done
    
    success "Сборка и загрузка образов завершена"
}

# Создание namespace
create_namespace() {
    log "Создание namespace..."
    
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    kubectl config set-context --current --namespace="$NAMESPACE"
    
    success "Namespace $NAMESPACE создан и активирован"
}

# Развертывание инфраструктуры
deploy_infrastructure() {
    log "Развертывание базовой инфраструктуры..."
    
    # Redis
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command: ["redis-server", "--appendonly", "yes"]
        volumeMounts:
        - name: redis-data
          mountPath: /data
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
      volumes:
      - name: redis-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: $NAMESPACE
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
EOF

    # Qdrant Vector Database
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
        - containerPort: 6334
        volumeMounts:
        - name: qdrant-data
          mountPath: /qdrant/storage
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: qdrant-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant-service
  namespace: $NAMESPACE
spec:
  selector:
    app: qdrant
  ports:
  - name: http
    port: 6333
    targetPort: 6333
  - name: grpc
    port: 6334
    targetPort: 6334
EOF

    # Ollama
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        env:
        - name: OLLAMA_HOST
          value: "0.0.0.0"
        volumeMounts:
        - name: ollama-data
          mountPath: /root/.ollama
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        lifecycle:
          postStart:
            exec:
              command:
              - "/bin/sh"
              - "-c"
              - |
                sleep 10
                ollama pull llama3.1:8b || true
                ollama pull llama3.1:latest || true
      volumes:
      - name: ollama-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: ollama-service
  namespace: $NAMESPACE
spec:
  selector:
    app: ollama
  ports:
  - port: 11434
    targetPort: 11434
EOF

    success "Базовая инфраструктура развернута"
}

# Развертывание мониторинга
deploy_monitoring() {
    log "Развертывание системы мониторинга..."
    
    # Prometheus
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus/'
        - '--web.console.libraries=/etc/prometheus/console_libraries'
        - '--web.console.templates=/etc/prometheus/consoles'
        - '--web.enable-lifecycle'
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus/
        - name: prometheus-data
          mountPath: /prometheus/
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-data
        emptyDir: {}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: $NAMESPACE
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
    - job_name: 'kubernetes-apiservers'
      kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          names:
          - default
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https
    
    - job_name: 'atlas-core'
      static_configs:
      - targets: ['atlas-core-service:8000']
    
    - job_name: 'redis'
      static_configs:
      - targets: ['redis-exporter-service:9121']
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: $NAMESPACE
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
EOF

    # Redis Exporter для мониторинга
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-exporter
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-exporter
  template:
    metadata:
      labels:
        app: redis-exporter
    spec:
      containers:
      - name: redis-exporter
        image: oliver006/redis_exporter:latest
        ports:
        - containerPort: 9121
        env:
        - name: REDIS_ADDR
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "32Mi"
            cpu: "10m"
          limits:
            memory: "64Mi"
            cpu: "50m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-exporter-service
  namespace: $NAMESPACE
spec:
  selector:
    app: redis-exporter
  ports:
  - port: 9121
    targetPort: 9121
EOF

    # Grafana
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "atlas_admin"
        - name: GF_USERS_ALLOW_SIGN_UP
          value: "false"
        volumeMounts:
        - name: grafana-data
          mountPath: /var/lib/grafana
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: grafana-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: grafana-service
  namespace: $NAMESPACE
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
EOF

    success "Система мониторинга развернута"
}

# Развертывание Atlas Core
deploy_atlas_core() {
    log "Развертывание Atlas Core..."
    
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atlas-core
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: atlas-core
  template:
    metadata:
      labels:
        app: atlas-core
    spec:
      containers:
      - name: atlas-core
        image: atlas-core:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8000
        env:
        - name: ATLAS_WEB_PORT
          value: "8000"
        - name: ATLAS_ENVIRONMENT
          value: "kubernetes"
        - name: OLLAMA_URL
          value: "http://ollama-service:11434"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: QDRANT_URL
          value: "http://qdrant-service:6333"
        - name: ATLAS_LLM1_MODEL
          value: "llama3.1:8b"
        - name: ATLAS_LLM2_MODEL
          value: "llama3.1:8b"
        - name: ATLAS_LLM3_MODEL
          value: "llama3.1:8b"
        - name: ATLAS_DATA_DIR
          value: "/app/data"
        volumeMounts:
        - name: atlas-data
          mountPath: /app/data
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: atlas-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: atlas-core-service
  namespace: $NAMESPACE
spec:
  selector:
    app: atlas-core
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: atlas-core-hpa
  namespace: $NAMESPACE
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: atlas-core
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

    success "Atlas Core развернут"
}

# Развертывание 3D Frontend
deploy_frontend() {
    log "Развертывание 3D Frontend..."
    
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atlas-frontend
  namespace: $NAMESPACE
spec:
  replicas: 3
  selector:
    matchLabels:
      app: atlas-frontend
  template:
    metadata:
      labels:
        app: atlas-frontend
    spec:
      containers:
      - name: atlas-frontend
        image: atlas-frontend:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8080
        env:
        - name: ATLAS_BACKEND_URL
          value: "http://atlas-core-service:8000"
        - name: PORT
          value: "8080"
        livenessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: atlas-frontend-service
  namespace: $NAMESPACE
spec:
  selector:
    app: atlas-frontend
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: atlas-frontend-hpa
  namespace: $NAMESPACE
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: atlas-frontend
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

    success "3D Frontend развернут"
}

# Развертывание MCP Services
deploy_mcp_services() {
    log "Развертывание MCP Services..."
    
    # MCP Automation
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-automation
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-automation
  template:
    metadata:
      labels:
        app: mcp-automation
    spec:
      containers:
      - name: mcp-automation
        image: mcp-automation:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 4002
        env:
        - name: MCP_PORT
          value: "4002"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        livenessProbe:
          httpGet:
            path: /health
            port: 4002
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 4002
          initialDelaySeconds: 10
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "300m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-automation-service
  namespace: $NAMESPACE
spec:
  selector:
    app: mcp-automation
  ports:
  - port: 4002
    targetPort: 4002
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-automation-hpa
  namespace: $NAMESPACE
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-automation
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

    # MCP Automator (macOS)
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-automator
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-automator
  template:
    metadata:
      labels:
        app: mcp-automator
    spec:
      containers:
      - name: mcp-automator
        image: mcp-automator:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 4003
        env:
        - name: MCP_PORT
          value: "4003"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        livenessProbe:
          httpGet:
            path: /health
            port: 4003
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 4003
          initialDelaySeconds: 10
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "300m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-automator-service
  namespace: $NAMESPACE
spec:
  selector:
    app: mcp-automator
  ports:
  - port: 4003
    targetPort: 4003
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-automator-hpa
  namespace: $NAMESPACE
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-automator
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

    # MCP TTS
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-tts
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-tts
  template:
    metadata:
      labels:
        app: mcp-tts
    spec:
      containers:
      - name: mcp-tts
        image: python:3.11-slim
        ports:
        - containerPort: 4004
        env:
        - name: MCP_PORT
          value: "4004"
        command: ["/bin/sh"]
        args:
        - -c
        - |
          pip install fastapi uvicorn gtts pydub aiohttp
          cat > /app/server.py << 'EOF'
          from fastapi import FastAPI
          import uvicorn
          
          app = FastAPI()
          
          @app.get("/health")
          async def health():
              return {"status": "healthy", "service": "mcp-tts"}
          
          @app.get("/")
          async def root():
              return {"message": "MCP TTS Service", "version": "1.0.0"}
          
          if __name__ == "__main__":
              uvicorn.run(app, host="0.0.0.0", port=4004)
          EOF
          python /app/server.py
        livenessProbe:
          httpGet:
            path: /health
            port: 4004
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 4004
          initialDelaySeconds: 30
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "300m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-tts-service
  namespace: $NAMESPACE
spec:
  selector:
    app: mcp-tts
  ports:
  - port: 4004
    targetPort: 4004
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-tts-hpa
  namespace: $NAMESPACE
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-tts
  minReplicas: 2
  maxReplicas: 6
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 75
EOF

    # MCP Playwright
    kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-playwright
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-playwright
  template:
    metadata:
      labels:
        app: mcp-playwright
    spec:
      containers:
      - name: mcp-playwright
        image: mcr.microsoft.com/playwright/python:v1.40.0-jammy
        ports:
        - containerPort: 4005
        env:
        - name: MCP_PORT
          value: "4005"
        command: ["/bin/sh"]
        args:
        - -c
        - |
          pip install fastapi uvicorn playwright
          playwright install chromium
          cat > /app/server.py << 'EOF'
          from fastapi import FastAPI
          import uvicorn
          
          app = FastAPI()
          
          @app.get("/health")
          async def health():
              return {"status": "healthy", "service": "mcp-playwright"}
          
          @app.get("/mcp")
          async def mcp():
              return {"message": "MCP Playwright Service", "version": "1.0.0"}
          
          if __name__ == "__main__":
              uvicorn.run(app, host="0.0.0.0", port=4005)
          EOF
          python /app/server.py
        livenessProbe:
          httpGet:
            path: /health
            port: 4005
          initialDelaySeconds: 120
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 4005
          initialDelaySeconds: 60
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-playwright-service
  namespace: $NAMESPACE
spec:
  selector:
    app: mcp-playwright
  ports:
  - port: 4005
    targetPort: 4005
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-playwright-hpa
  namespace: $NAMESPACE
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-playwright
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

    success "MCP Services развернуты"
}

# Ожидание готовности подов
wait_for_pods() {
    log "Ожидание готовности всех подов..."
    
    local deployments=(
        "redis"
        "qdrant"
        "ollama"
        "prometheus"
        "redis-exporter"
        "grafana"
        "atlas-core"
        "atlas-frontend"
        "mcp-automation"
        "mcp-automator"
        "mcp-tts"
        "mcp-playwright"
    )
    
    for deployment in "${deployments[@]}"; do
        log "Ожидание готовности $deployment..."
        if ! kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout="$TIMEOUT"; then
            warning "Deployment $deployment не готов в течение timeout"
        else
            success "Deployment $deployment готов"
        fi
    done
    
    log "Дополнительное ожидание стабилизации ($WAIT_TIME секунд)..."
    sleep "$WAIT_TIME"
}

# Настройка port-forward
setup_port_forwarding() {
    log "Настройка port forwarding..."
    
    # Остановка существующих процессов
    pkill -f "port-forward.*atlas" || true
    sleep 2
    
    # Atlas Core (8000)
    kubectl port-forward -n "$NAMESPACE" service/atlas-core-service 8000:8000 &
    local atlas_core_pid=$!
    
    # 3D Frontend (8080)
    kubectl port-forward -n "$NAMESPACE" service/atlas-frontend-service 8080:8080 &
    local frontend_pid=$!
    
    # Grafana (3000)
    kubectl port-forward -n "$NAMESPACE" service/grafana-service 3000:3000 &
    local grafana_pid=$!
    
    # Prometheus (9090)
    kubectl port-forward -n "$NAMESPACE" service/prometheus-service 9090:9090 &
    local prometheus_pid=$!
    
    # MCP Services
    kubectl port-forward -n "$NAMESPACE" service/mcp-automation-service 4002:4002 &
    kubectl port-forward -n "$NAMESPACE" service/mcp-automator-service 4003:4003 &
    kubectl port-forward -n "$NAMESPACE" service/mcp-tts-service 4004:4004 &
    kubectl port-forward -n "$NAMESPACE" service/mcp-playwright-service 4005:4005 &
    
    # Сохранение PID в файл для дальнейшего управления
    echo "$atlas_core_pid" > /tmp/atlas-port-forward.pid
    echo "$frontend_pid" >> /tmp/atlas-port-forward.pid
    echo "$grafana_pid" >> /tmp/atlas-port-forward.pid
    echo "$prometheus_pid" >> /tmp/atlas-port-forward.pid
    
    sleep 5
    success "Port forwarding настроен"
}

# Проверка состояния сервисов
verify_deployment() {
    log "Проверка состояния развертывания..."
    
    # Проверка подов
    log "Статус подов:"
    kubectl get pods -n "$NAMESPACE" --sort-by='.status.phase'
    
    # Проверка сервисов
    log "Статус сервисов:"
    kubectl get services -n "$NAMESPACE"
    
    # Проверка доступности через curl
    sleep 10
    
    log "Проверка доступности сервисов..."
    
    # Atlas Core
    if curl -s -f "http://localhost:8000/health" > /dev/null; then
        success "Atlas Core доступен на http://localhost:8000"
    else
        warning "Atlas Core недоступен"
    fi
    
    # 3D Frontend
    if curl -s -f "http://localhost:8080/" > /dev/null; then
        success "3D Frontend доступен на http://localhost:8080"
    else
        warning "3D Frontend недоступен"
    fi
    
    # Grafana
    if curl -s -f "http://localhost:3000/" > /dev/null; then
        success "Grafana доступен на http://localhost:3000 (admin/atlas_admin)"
    else
        warning "Grafana недоступен"
    fi
    
    # Prometheus
    if curl -s -f "http://localhost:9090/" > /dev/null; then
        success "Prometheus доступен на http://localhost:9090"
    else
        warning "Prometheus недоступен"
    fi
    
    # MCP Services
    local mcp_ports=(4002 4003 4004 4005)
    local mcp_names=("Automation" "Automator" "TTS" "Playwright")
    
    for i in "${!mcp_ports[@]}"; do
        local port="${mcp_ports[$i]}"
        local name="${mcp_names[$i]}"
        if curl -s -f "http://localhost:$port/health" > /dev/null; then
            success "MCP $name доступен на http://localhost:$port"
        else
            warning "MCP $name недоступен на порту $port"
        fi
    done
}

# Создание отчета о развертывании
create_deployment_report() {
    log "Создание отчета о развертывании..."
    
    local report_file="atlas_k8s_deployment_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "deployment_info": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "cluster_name": "$CLUSTER_NAME",
    "namespace": "$NAMESPACE",
    "script_version": "1.0.0"
  },
  "services": {
    "atlas_core": "http://localhost:8000",
    "atlas_frontend": "http://localhost:8080",
    "grafana": "http://localhost:3000",
    "prometheus": "http://localhost:9090",
    "mcp_automation": "http://localhost:4002",
    "mcp_automator": "http://localhost:4003",
    "mcp_tts": "http://localhost:4004",
    "mcp_playwright": "http://localhost:4005"
  },
  "credentials": {
    "grafana": {
      "username": "admin",
      "password": "atlas_admin"
    }
  },
  "cluster_info": {
    "context": "$(kubectl config current-context)",
    "cluster_info": "$(kubectl cluster-info)"
  },
  "deployment_status": "$(kubectl get deployments -n $NAMESPACE -o json)"
}
EOF

    success "Отчет сохранен в $report_file"
}

# Функция очистки
cleanup() {
    log "Запуск процедуры очистки..."
    
    # Остановка port-forward процессов
    if [[ -f "/tmp/atlas-port-forward.pid" ]]; then
        while read -r pid; do
            kill "$pid" 2>/dev/null || true
        done < /tmp/atlas-port-forward.pid
        rm -f /tmp/atlas-port-forward.pid
    fi
    
    pkill -f "port-forward.*atlas" 2>/dev/null || true
    
    warning "Очистка завершена"
}

# Обработка сигналов
trap cleanup EXIT INT TERM

# Основная функция
main() {
    echo -e "${PURPLE}"
    echo "=================================================="
    echo "🚀 Atlas MCP - Полное развертывание Kubernetes"
    echo "=================================================="
    echo -e "${NC}"
    
    local start_time=$(date +%s)
    
    # Проверка параметров
    case "${1:-deploy}" in
        "clean")
            log "Удаление кластера и очистка..."
            kind delete cluster --name "$CLUSTER_NAME" 2>/dev/null || true
            docker system prune -f
            success "Очистка завершена"
            exit 0
            ;;
        "restart")
            log "Перезапуск стека..."
            kind delete cluster --name "$CLUSTER_NAME" 2>/dev/null || true
            sleep 5
            ;;
        "status")
            log "Проверка статуса..."
            kubectl get all -n "$NAMESPACE" 2>/dev/null || error "Кластер не найден"
            exit 0
            ;;
        "logs")
            log "Просмотр логов Atlas Core..."
            kubectl logs -n "$NAMESPACE" -l app=atlas-core --tail=100 -f
            exit 0
            ;;
        "help")
            echo "Использование: $0 [команда]"
            echo "Команды:"
            echo "  deploy (по умолчанию) - Полное развертывание"
            echo "  restart               - Перезапуск кластера"
            echo "  clean                 - Удаление кластера"
            echo "  status                - Проверка статуса"
            echo "  logs                  - Просмотр логов"
            echo "  help                  - Эта справка"
            exit 0
            ;;
    esac
    
    # Выполнение развертывания
    check_dependencies
    check_docker
    create_cluster
    build_images
    create_namespace
    deploy_infrastructure
    deploy_monitoring
    deploy_atlas_core
    deploy_frontend
    deploy_mcp_services
    wait_for_pods
    setup_port_forwarding
    verify_deployment
    create_deployment_report
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo -e "${GREEN}"
    echo "=================================================="
    echo "✅ Развертывание завершено успешно!"
    echo "⏱️  Время развертывания: ${duration} секунд"
    echo "=================================================="
    echo -e "${NC}"
    
    info "Доступные сервисы:"
    echo "🌐 Atlas Web UI:      http://localhost:8000"
    echo "🎮 3D Frontend:       http://localhost:8080"
    echo "📊 Grafana:           http://localhost:3000 (admin/atlas_admin)"
    echo "📈 Prometheus:        http://localhost:9090"
    echo "🤖 MCP Automation:    http://localhost:4002"
    echo "🍎 MCP Automator:     http://localhost:4003"
    echo "🗣️  MCP TTS:          http://localhost:4004"
    echo "🎭 MCP Playwright:    http://localhost:4005"
    echo ""
    info "Управление:"
    echo "📋 Статус:            $0 status"
    echo "📜 Логи:              $0 logs"
    echo "🔄 Перезапуск:        $0 restart"
    echo "🧹 Очистка:           $0 clean"
    echo ""
    warning "Процессы port-forward работают в фоне. Для остановки используйте Ctrl+C или $0 clean"
}

# Запуск
main "$@"
