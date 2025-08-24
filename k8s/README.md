# Atlas MCP Kubernetes Configuration

Професійна Kubernetes конфігурація для Atlas MCP з повним набором інструментів для управління, моніторингу та масштабування.

## 🏗️ Архітектура

Atlas MCP Kubernetes стек включає:

### Основні компоненти
- **Atlas Core** - основний сервіс з автоматичним масштабуванням
- **Atlas Frontend** - 3D інтерфейс з балансуванням навантаження
- **MCP Services** - набір мікросервісів (automation, automator, TTS, playwright)

### Підтримуючі сервіси
- **Redis** - кешування та черги повідомлень
- **Qdrant** - векторна база даних для AI
- **Prometheus** - моніторинг та метрики
- **Grafana** - візуалізація та дашборди

### Мережа та безпека
- **NGINX Ingress** - входящий трафік з SSL/TLS
- **Network Policies** - ізоляція мережевого трафіку
- **RBAC** - контроль доступу на рівні кластера
- **Secrets Management** - безпечне зберігання секретів

## 📋 Передумови

### Програмне забезпечення
```bash
# Kubernetes кластер (minikube, kind, EKS, GKE, AKS)
kubectl version --client
kustomize version  # або використовуйте kubectl kustomize
make --version
```

### Мінімальні вимоги до кластера
- **CPU**: 4 vCPU
- **RAM**: 8 GB
- **Storage**: 50 GB
- **Nodes**: 2+

## 🚀 Швидкий старт

### 1. Клонування та підготовка
```bash
git clone <repository>
cd Atlas-mcp
chmod +x k8s-manage.sh
```

### 2. Налаштування кластера
```bash
# Встановлення metrics-server та NGINX Ingress
make setup-cluster
```

### 3. Побудова образів
```bash
# Побудова Docker образів
make build-images
```

### 4. Розгортання в development
```bash
# Встановлення в development середовище
make install-dev

# Або використовуючи скрипт
./k8s-manage.sh install development
```

### 5. Перевірка статусу
```bash
make status-dev
```

## 🛠️ Керування

### Встановлення та оновлення
```bash
# Development
make install-dev          # Встановити
make update-dev           # Оновити
make restart-dev          # Перезапустити

# Production
make install-prod
make update-prod
make restart-prod
```

### Моніторинг та логи
```bash
# Статус
make status-dev
make monitoring-dev

# Логи
make logs-dev             # Atlas Core
make logs-frontend-dev    # Frontend

# Діагностика
make diagnose-dev
```

### Масштабування
```bash
# Frontend масштабування
make scale-frontend-dev REPLICAS=5

# Core масштабування
make scale-core-prod REPLICAS=3
```

### Доступ до сервісів
```bash
# Grafana dashboard
make port-forward-grafana-dev
# Відкрийте http://localhost:3000

# Prometheus
make port-forward-prometheus-dev
# Відкрийте http://localhost:9090

# Atlas Frontend
make port-forward-atlas-dev
# Відкрийте http://localhost:8080
```

## 📁 Структура проекту

```
k8s/
├── base/                           # Базова конфігурація
│   ├── namespace.yaml              # Namespace
│   ├── configmaps.yaml            # ConfigMaps
│   ├── secrets.yaml               # Secrets
│   ├── persistentvolumeclaims.yaml # PVC для зберігання
│   ├── atlas-core-deployment.yaml # Atlas Core
│   ├── atlas-frontend-deployment.yaml # Atlas Frontend
│   ├── mcp-services-deployments.yaml # MCP сервіси
│   ├── data-services-deployments.yaml # Redis, Qdrant
│   ├── services.yaml              # Kubernetes Services
│   ├── hpa.yaml                   # Horizontal Pod Autoscaler
│   ├── poddisruptionbudgets.yaml  # Pod Disruption Budgets
│   ├── networkpolicies.yaml       # Network Policies
│   └── kustomization.yaml         # Kustomize конфігурація
├── overlays/                      # Середовища
│   ├── development/               # Development конфігурація
│   │   ├── kustomization.yaml
│   │   ├── deployment-patches.yaml
│   │   └── service-patches.yaml
│   └── production/                # Production конфігурація
│       ├── kustomization.yaml
│       ├── deployment-patches.yaml
│       └── hpa-patches.yaml
├── monitoring/                    # Моніторинг стек
│   ├── monitoring-deployments.yaml
│   ├── monitoring-services.yaml
│   ├── prometheus-config.yaml
│   ├── grafana-config.yaml
│   └── rbac.yaml
└── ingress/                       # Ingress конфігурація
    └── ingress.yaml
```

## 🏗️ Середовища

### Development
- **Namespace**: `atlas-mcp-dev`
- **Replicas**: Мінімум для тестування
- **Resources**: Знижені лімити
- **Ingress**: NodePort доступ
- **Логування**: DEBUG рівень

### Production
- **Namespace**: `atlas-mcp-prod`
- **Replicas**: Високодоступність
- **Resources**: Production лімити
- **Ingress**: LoadBalancer з SSL
- **Логування**: INFO рівень
- **Security**: Розширені security contexts

## 🔒 Безпека

### Network Policies
- Ізоляція трафіку між сервісами
- Дозволений доступ тільки до потрібних портів
- Блокування зовнішнього трафіку за замовчуванням

### RBAC
- Окремі ServiceAccounts для кожного компонента
- Мінімальні привілеї
- Prometheus має доступ тільки до метрик

### Secrets
```bash
# Development
make create-secrets-dev

# Production (потребує файли секретів)
mkdir secrets/
echo "your-api-key" > secrets/google-tts-api-key.txt
echo "secure-password" > secrets/grafana-admin-password.txt
make create-secrets-prod
```

## 📊 Моніторинг

### Prometheus метрики
- **Application metrics**: HTTP запити, помилки, latency
- **System metrics**: CPU, пам'ять, мережа
- **Custom metrics**: Atlas-специфічні метрики

### Grafana дашборди
- **Atlas Overview**: Загальний огляд системи
- **Resource Usage**: Використання ресурсів
- **Error Tracking**: Моніторинг помилок
- **Performance**: Продуктивність сервісів

### Алерти
- Високе використання CPU/пам'яті
- Високий рівень помилок
- Недоступність сервісів
- Проблеми з зберіганням

## 🔄 Автоматичне масштабування

### Horizontal Pod Autoscaler (HPA)
```yaml
# Atlas Core
CPU: 70% -> scale up
Memory: 80% -> scale up
Min replicas: 2 (dev) / 3 (prod)
Max replicas: 10 (dev) / 20 (prod)

# Atlas Frontend
CPU: 70% -> scale up
Min replicas: 3 (dev) / 5 (prod)
Max replicas: 15 (dev) / 30 (prod)
```

### Pod Disruption Budgets
- Гарантія мінімальної кількості доступних подів
- Захист від одночасного оновлення всіх подів

## 💾 Зберігання даних

### Persistent Volumes
- **Atlas Data**: 10GB (dev) / 100GB (prod)
- **Redis**: 5GB (dev) / 20GB (prod)
- **Qdrant**: 20GB (dev) / 200GB (prod)
- **Prometheus**: 15GB (dev) / 100GB (prod)
- **Grafana**: 5GB
- **TTS Audio**: 10GB

### Резервне копіювання
```bash
# Створення резервної копії
make backup-dev
make backup-prod

# Відновлення
./k8s-manage.sh restore backups/20240824_120000/atlas-mcp-prod.yaml
```

## 🌐 Ingress та SSL

### Доступ до сервісів
- **Atlas Frontend**: https://atlas.local
- **Atlas API**: https://api.atlas.local
- **MCP Services**: https://api.atlas.local/mcp/*

### SSL/TLS
```bash
# Автоматичні сертифікати через cert-manager
# Замініть домени в ingress/ingress.yaml
```

## 🔧 Налаштування

### Конфігурація через ConfigMaps
- Змінні середовища для всіх сервісів
- Конфігурація Redis, Qdrant
- Prometheus правила та алерти

### Secrets
- API ключі
- Паролі баз даних
- TLS сертифікати

## 🐛 Діагностика та усунення проблем

### Перевірка здоров'я
```bash
# Загальна діагностика
make diagnose-dev

# Перевірка окремого сервісу
kubectl describe pod -l app.kubernetes.io/name=atlas-core -n atlas-mcp-dev

# Логи з помилками
kubectl logs -l app.kubernetes.io/name=atlas-core -n atlas-mcp-dev | grep ERROR
```

### Типові проблеми

#### Поди не запускаються
```bash
# Перевірка ресурсів
kubectl describe nodes
kubectl get pvc -n atlas-mcp-dev

# Перевірка образів
kubectl describe pod <pod-name> -n atlas-mcp-dev
```

#### Сервіси недоступні
```bash
# Перевірка Network Policies
kubectl get networkpolicy -n atlas-mcp-dev

# Перевірка Service endpoints
kubectl get endpoints -n atlas-mcp-dev
```

#### Проблеми з зберіганням
```bash
# Перевірка PVC
kubectl get pvc -n atlas-mcp-dev
kubectl describe pvc <pvc-name> -n atlas-mcp-dev

# Перевірка StorageClass
kubectl get storageclass
```

## 📈 Продуктивність

### Рекомендації по ресурсах

#### Development
- **Node**: 2 CPU, 4GB RAM
- **Total cluster**: 4 CPU, 8GB RAM

#### Production
- **Node**: 4+ CPU, 8+ GB RAM
- **Total cluster**: 12+ CPU, 24+ GB RAM

### Оптимізація
- Використання affinity rules для розподілу подів
- Resource quotas для контролю споживання
- Лімити на рівні namespace

## 🔄 CI/CD інтеграція

### GitHub Actions
```yaml
# Приклад workflow
- name: Deploy to Kubernetes
  run: |
    make build-images
    make push-images REGISTRY=${{ secrets.DOCKER_REGISTRY }}
    make update-prod
```

### Helm Charts (альтернатива)
```bash
# Якщо потрібно Helm замість Kustomize
helm package k8s/
helm install atlas-mcp ./atlas-mcp-chart
```

## 📞 Підтримка

### Команди для допомоги
```bash
# Повна допомога
./k8s-manage.sh help
make help

# Швидкі команди
make dev              # Швидке розгортання development
make status           # Статус development
make logs             # Логи development
```

### Корисні ресурси
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [Prometheus Operator](https://prometheus-operator.dev/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)

## 🎯 Наступні кроки

1. **Встановити кластер** (minikube/kind для локального розробки)
2. **Запустити `make setup-cluster`** для налаштування
3. **Побудувати образи** з `make build-images`
4. **Розгорнути в development** з `make install-dev`
5. **Перевірити доступ** через порт-форвардинг
6. **Налаштувати моніторинг** через Grafana
7. **Протестувати масштабування** з різними навантаженнями

## 🏆 Переваги цієї конфігурації

### ✅ Професійність
- Production-ready конфігурація
- Відповідає Kubernetes best practices
- Повний observability стек

### ✅ Надійність
- Автоматичне відновлення подів
- Health checks та liveness probes
- Graceful shutdowns

### ✅ Масштабованість
- Horizontal Pod Autoscaling
- Вертикальне масштабування через resource limits
- Multi-node підтримка

### ✅ Безпека
- Network isolation
- RBAC controls
- Secrets management

### ✅ Зручність
- Простий інтерфейс управління
- Автоматизовані скрипти
- Comprehensive monitoring

Atlas MCP тепер готовий до професійного використання в Kubernetes! 🚀
