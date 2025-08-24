# Решение проблем Firewall в Atlas MCP

Этот документ описывает решения для обхода firewall блокировок при работе с Kubernetes кластерами и сетевыми вызовами в CI/CD среде.

## 🔍 Проблема

GitHub Copilot coding agent и некоторые CI среды блокируют доступ к:
- Приватным IP адресам (10.x.x.x, 172.x.x.x, 192.168.x.x)
- Pod CIDR диапазонам Kubernetes (обычно 10.244.x.x)
- DNS запросам к *.cluster.local
- Произвольным внешним доменам

Типичные ошибки:
```
Firewall rules blocked me from connecting to 10.244.0.2
Triggering command: /usr/bin/kubelet (packet block)
Triggering command: /coredns -conf /etc/coredns/Corefile (dns block)
```

## ✅ Решения

### 1. Self-hosted GitHub Runner (Рекомендуется)

**Преимущества:**
- Полный контроль над сетевым доступом
- Локальный доступ к кластерам
- Нет firewall ограничений

**Конфигурация:**
```yaml
jobs:
  k8s-test:
    runs-on: [self-hosted, macOS]  # или [self-hosted, linux]
    steps:
      - uses: actions/checkout@v4
      - name: Setup and test
        run: ./scripts/setup-k8s-ci.sh
```

**Установка self-hosted runner:**
1. Перейдите в Settings → Actions → Runners
2. Нажмите "New self-hosted runner"
3. Следуйте инструкциям для вашей ОС
4. Добавьте метки: `macOS` или `linux`

### 2. Kind кластер внутри CI job

**Принцип:**
- Создаем изолированный кластер внутри CI среды
- Обращаемся через localhost/port-forward
- Обходим внешние сетевые ограничения

**Пример:**
```bash
# Создание кластера
kind create cluster --name atlas-mcp-ci

# Загрузка образов
kind load docker-image atlas-mcp/atlas-core:ci-latest --name atlas-mcp-ci

# Деплой приложения
kubectl apply -k k8s/overlays/development

# Тестирование через localhost
kubectl port-forward svc/atlas-core-service 8000:8000 &
curl http://127.0.0.1:8000/status
```

### 3. Артефакты вместо прямых сетевых вызовов

**Принцип:**
- Собираем данные в CI среде через kubectl
- Сохраняем как артефакты
- Анализируем файлы вместо сетевых вызовов

**Пример:**
```bash
# Сбор данных
kubectl get pods -A -o wide > k8s_pods.txt
kubectl get deploy -A -o wide > k8s_deploy.txt
kubectl describe ns atlas-mcp-dev > k8s_ns_desc.txt

# Тестирование через localhost с сохранением результатов
kubectl port-forward svc/atlas-core-service 8000:8000 &
curl -s http://127.0.0.1:8000/status > atlas_core_status.json || true

# Загрузка как артефакт
- uses: actions/upload-artifact@v4
  with:
    name: k8s-status
    path: |
      k8s_*.txt
      atlas_core_status.json
```

### 4. Custom Allowlist (Ограниченное решение)

**Где настроить:**
Repository → Settings → GitHub Copilot → Coding agents → Custom allowlist

**Что добавить:**
- `localhost` - для локальных тестов
- `127.0.0.1` - для port-forward
- Публичные домены API (если нужны)

**Что НЕ поможет:**
- `10.244.x.x` - приватные Pod IP
- `*.cluster.local` - внутренние DNS имена

### 5. Публичный доступ (Только для демо)

**Внимание:** Используйте только для краткосрочных демонстраций!

```bash
# Временный Ingress с внешним IP
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: atlas-demo
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: atlas-demo.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: atlas-core-service
            port:
              number: 8000
EOF
```

## 🚀 Готовые скрипты

### scripts/setup-k8s-ci.sh
Автоматизированный скрипт для firewall-safe развертывания:
- Создает kind кластер
- Строит и загружает образы
- Деплоит приложение
- Тестирует через localhost
- Сохраняет артефакты

**Использование:**
```bash
# Базовый запуск
./scripts/setup-k8s-ci.sh

# С custom настройками
CLUSTER_NAME=my-cluster NAMESPACE=my-ns ./scripts/setup-k8s-ci.sh

# С очисткой после тестов
CLEANUP_CLUSTER=true ./scripts/setup-k8s-ci.sh
```

### .github/workflows/k8s-firewall-safe.yml
GitHub Actions workflow с множественными стратегиями:
- Build на GitHub-hosted runners
- Тест на self-hosted runners  
- Альтернативный тест в изолированной среде
- Автоматическое создание issues при фейлах

**Активация:**
```bash
# Через лейбл на PR
gh pr edit <PR_NUMBER> --add-label "k8s-test"

# Или вручную
gh workflow run "Atlas MCP Kubernetes CI (Firewall Safe)"
```

## 🔧 Диагностика проблем

### Проверка текущих ограничений
```bash
# Тест доступности Pod IP
curl -v http://10.244.1.5:8080 2>&1 | grep -i "blocked\|denied\|refused"

# Тест DNS резолюции
nslookup atlas-core-service.atlas-mcp-dev.svc.cluster.local

# Тест через port-forward (должен работать)
kubectl port-forward svc/atlas-core-service 8000:8000 &
curl http://127.0.0.1:8000/status
```

### Проверка образов в kind
```bash
# Список кластеров
kind get clusters

# Список образов в кластере
docker exec -it atlas-mcp-ci-control-plane crictl images | grep atlas-mcp
```

### Логи для диагностики
```bash
# Логи kind кластера
kind export logs ./kind-logs --name atlas-mcp-ci

# Статус deployments
kubectl get deploy -A -o wide

# Describe проблемных pods
kubectl describe pod <POD_NAME> -n atlas-mcp-dev
```

## 📝 Best Practices

1. **Используйте self-hosted runners** для production CI/CD
2. **Тестируйте через localhost/port-forward** вместо прямых Pod IP
3. **Сохраняйте артефакты** для анализа вместо онлайн доступа
4. **Минимизируйте allowlist** - добавляйте только реально нужные домены
5. **Никогда не публикуйте** internal сервисы без proper authentication
6. **Используйте временные кластеры** для CI тестов
7. **Автоматизируйте cleanup** для экономии ресурсов

## 🆘 Troubleshooting

### "ErrImageNeverPull"
```bash
# Загрузите образы в kind
kind load docker-image atlas-mcp/atlas-core:latest --name cluster-name
```

### "spec.selector: field is immutable"
```bash
# Удалите deployment и пересоздайте
kubectl delete deployment atlas-core -n atlas-mcp-dev
kubectl apply -k k8s/overlays/development
```

### Port-forward не работает
```bash
# Проверьте, что pod запущен
kubectl get pods -n atlas-mcp-dev

# Используйте другой порт
kubectl port-forward svc/atlas-core-service 8001:8000
```

### Кластер не создается
```bash
# Очистите старые кластеры
kind get clusters | xargs -I {} kind delete cluster --name {}

# Проверьте Docker
docker info
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте logs в GitHub Actions артефактах
2. Запустите `./scripts/setup-k8s-ci.sh` локально
3. Используйте `kubectl describe` для диагностики
4. Проверьте firewall logs в системе

Для быстрого решения используйте self-hosted runner с локальным доступом к кластеру.
