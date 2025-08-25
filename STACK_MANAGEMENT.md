# Atlas Stack Management Guide

## Правильний запуск після змін

### 1. Звичайний запуск
```bash
./docker-entrypoint.sh
```
Цей скрипт тепер автоматично:
- Запускає основні сервіси першими
- Чекає їх готовності
- Потім запускає monitoring сервіси
- Нарешті запускає MCP сервіси

### 2. Повна перебудова
```bash
./rebuild_stack.sh
```
Використовуйте для:
- Після змін у коді
- Коли щось працює неправильно
- Після оновлення Docker образів

### 3. Перебудова з очищенням
```bash
./rebuild_stack.sh --clean
```
Використовуйте коли:
- Маєте проблеми з мережею
- Потрібно повністю очистити volumes
- Після серйозних змін у конфігурації

### 4. Перебудова без кешу
```bash
./rebuild_stack.sh --no-cache
```
Використовуйте коли:
- Змінювали Dockerfile
- Потрібно принудити перебудову всіх образів

## Виправлені проблеми

### Redis Exporter
- Тепер має `depends_on` з `condition: service_healthy`
- Запускається тільки після того, як Redis повністю готовий
- Має власний health check

### Порядок запуску
1. **Core services** (atlas-core, frontend, TTS, Redis, Qdrant)
2. **Monitoring services** (Prometheus, Grafana, Redis Exporter)
3. **MCP services** (automation, automator, playwright)

### Health Checks
- Redis: `redis-cli ping`
- Redis Exporter: перевірка `/metrics` endpoint
- Всі інші сервіси мають відповідні health checks

## Моніторинг стану

### Перевірка стану всіх сервісів
```bash
docker compose ps
```

### Перевірка логів
```bash
docker compose logs -f redis-exporter
docker compose logs -f redis
```

### Перевірка мережі
```bash
docker network inspect atlas-network
```

## Усунення неполадок

### Якщо Redis Exporter не підключається:
```bash
# Перезапуск monitoring профілю
docker compose --profile monitoring down
docker compose --profile monitoring up -d
```

### Якщо проблеми з мережею:
```bash
./rebuild_stack.sh --clean
```

### Якщо сервіси не стартують:
```bash
# Перевірити логи
docker compose logs [service-name]

# Перебудувати без кешу
./rebuild_stack.sh --no-cache
```
