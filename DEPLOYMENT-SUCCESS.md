# 🚀 Atlas MCP - Kubernetes Deployment Success!

## ✅ Статус розгортання

Atlas MCP успішно розгорнуто в локальному Kubernetes кластері Kind!

### 📊 Активні сервіси:
- ✅ **Atlas Core** - 2 репліки (основна система)
- ✅ **Atlas Frontend** - 3 репліки (веб-інтерфейс)
- ✅ **MCP Automation** - 2 репліки (автоматизація)
- ✅ **MCP Automator** - 2 репліки (macOS автоматизатор)
- ✅ **MCP TTS** - 2 репліки (синтез мови)
- ✅ **Redis** - 1 репліка (кеш)
- ✅ **Qdrant** - 1 репліка (векторна БД)
- ✅ **Prometheus** - 1 репліка (метрики)
- ✅ **Grafana** - 1 репліка (моніторинг)
- ⚠️ **MCP Playwright** - проблеми з образом (не критично)

## 🌐 Доступ до сервісів

### Локальні URL (через localhost):

```bash
# Основний веб-інтерфейс Atlas
http://localhost/

# API Atlas Core  
http://localhost/api/

# Grafana моніторинг
http://localhost/grafana/
# Логін: admin / admin

# Prometheus метрики
http://localhost/prometheus/
```

### Внутрішні сервіси (в кластері):

```bash
# Atlas Core API
http://atlas-core-service.atlas-mcp.svc.cluster.local:8000

# MCP сервіси
http://mcp-automation-service.atlas-mcp.svc.cluster.local:4002
http://mcp-automator-service.atlas-mcp.svc.cluster.local:4003
http://mcp-tts-service.atlas-mcp.svc.cluster.local:4004

# Дані
http://redis-service.atlas-mcp.svc.cluster.local:6379
http://qdrant-service.atlas-mcp.svc.cluster.local:6333
```

## 🔧 Управління кластером

### Швидкі команди через Makefile:

```bash
# Перевірка стану
make status-dev

# Перегляд логів
make logs-dev

# Масштабування
make scale-dev

# Очистка
make cleanup

# Повне видалення
make destroy-dev
```

### Ручні kubectl команди:

```bash
# Перевірка pods
kubectl get pods -n atlas-mcp

# Логи сервісу
kubectl logs -n atlas-mcp -l app.kubernetes.io/name=atlas-core

# Port forwarding для прямого доступу
kubectl port-forward -n atlas-mcp svc/atlas-core-service 8000:8000
kubectl port-forward -n atlas-mcp svc/grafana-service 3000:3000

# Виконання команди в контейнері
kubectl exec -it -n atlas-mcp deployment/atlas-core -- bash
```

## 📊 Моніторинг та діагностика

### Prometheus метрики:
- Доступні за адресою: `http://localhost/prometheus/`
- Метрики всіх сервісів автоматично збираються

### Grafana дашборди:
- Доступні за адресою: `http://localhost/grafana/`
- Попередньо налаштовані дашборди для Atlas MCP

### Логи:
```bash
# Всі логи Atlas
kubectl logs -n atlas-mcp -l app.kubernetes.io/part-of=atlas-autonomous-system

# Специфічний сервіс
kubectl logs -n atlas-mcp -l app.kubernetes.io/name=atlas-core -f
```

## 💾 Persistent Storage

Всі дані зберігаються в Persistent Volumes:
- `atlas-data-pvc` (10Gi) - основні дані
- `atlas-logs-pvc` (5Gi) - логи
- `redis-data-pvc` (5Gi) - Redis кеш  
- `qdrant-data-pvc` (20Gi) - векторна база
- `tts-audio-pvc` (10Gi) - аудіо файли TTS
- `prometheus-data-pvc` (15Gi) - метрики
- `grafana-data-pvc` (5Gi) - дашборди

## 🔒 Security Features

- ✅ RBAC налаштовано
- ✅ Network Policies активні
- ✅ Pod Security Contexts
- ✅ Resource Limits встановлені
- ✅ Health Checks активні

## 🎯 Автомасштабування

HPA (Horizontal Pod Autoscaler) налаштовано для всіх сервісів:
- CPU threshold: 70%
- Memory threshold: 80%
- Min replicas: як налаштовано
- Max replicas: 10

## 🚨 Troubleshooting

### Якщо сервіс не відповідає:
```bash
# Перевірка стану
kubectl get pods -n atlas-mcp
kubectl describe pod -n atlas-mcp <pod-name>

# Перезапуск
kubectl rollout restart deployment -n atlas-mcp <deployment-name>
```

### Очистка та перезапуск:
```bash
# Повне перестворення
kubectl delete namespace atlas-mcp
kubectl apply -k k8s/overlays/development/
```

## 🎉 Наступні кроки

1. **Відкрийте веб-інтерфейс**: `http://localhost/`
2. **Налаштуйте моніторинг**: `http://localhost/grafana/`
3. **Перевірте API**: `http://localhost/api/status`
4. **Досліджуйте логи та метрики**

---
**Atlas MCP готовий до роботи! 🤖✨**

*Система розгорнута з професійним управлінням контейнерів через Kubernetes*
