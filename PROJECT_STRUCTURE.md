# Atlas MCP - Project Structure

## Overview
Atlas Autonomous System з професійним управлінням контейнерів через Kubernetes.

## Core Files
```
atlas_core.py              # Основний модуль Atlas системи
mcp_automation_server.py   # MCP сервер автоматизації
mcp_macos_automator.py     # macOS автоматизатор
requirements.txt           # Python залежності
README.md                  # Основна документація
```

## Configuration
```
.env                       # Локальні змінні середовища
.env.k8s.example          # Шаблон для Kubernetes змінних
docker-compose.yml         # Docker Compose конфігурація
```

## Docker & Containers
```
Dockerfile                 # Основний Docker образ
Dockerfile.mcp-automation  # MCP автоматизація
Dockerfile.mcp-automator   # MCP автоматизатор
docker-entrypoint.sh      # Docker точка входу
```

## Kubernetes (Production-Ready)
```
k8s/                      # Kubernetes конфігурації
├── base/                 # Базові ресурси
├── overlays/             # Середовища (dev/prod)
├── monitoring/           # Prometheus + Grafana
└── ingress/             # Load balancer + SSL

setup-k8s.sh            # Установка Kubernetes
k8s-manage.sh           # Управління кластером
Makefile                # Швидкі команди
KUBERNETES-SUMMARY.md   # Документація Kubernetes
```

## Installation & Scripts
```
install_macos.sh         # Установка на macOS
start_atlas.sh          # Запуск системи
```

## Testing
```
test_atlas.py           # Основні тести Atlas
test_basic.py           # Базові синтаксичні тести
```

## Data & Services
```
data/                   # Дані системи (PV мounts)
services/              # Допоміжні сервіси
monitoring/            # Конфігурація моніторингу
scripts/               # Утилітарні скрипти
```

## 3D Assets & Frontend
```
3d_helmet_viewer/      # 3D viewer з WebGL
archived_3d_assets/    # Архів 3D моделей
```

## Development Environment
```
atlas_env/             # Python virtual environment
.vscode/               # VS Code налаштування
.pytest_cache/         # Pytest кеш
.playwright-mcp/       # Playwright MCP
```

## Archive
```
archive/               # Архівовані файли (не в git)
├── Atlas.md           # Старе ТЗ
├── ІНСТРУКЦІЯ.md      # Українська інструкція
├── demo_atlas.py      # Демо скрипт
├── atlas.log          # Старі логи
├── __pycache__/       # Python кеш
├── 3d_viewer.html     # Порожній HTML
└── night_lighting_control.py  # Порожній файл
```

## Quick Start

### Local Development
```bash
./install_macos.sh      # Установка
./start_atlas.sh        # Запуск
```

### Kubernetes Production
```bash
./setup-k8s.sh          # Установка K8s
make install-prod        # Деплой продакшн
make status-prod         # Статус
```

### Management Commands
```bash
make logs-dev           # Логи dev
make scale-dev          # Масштабування
make backup             # Резервна копія
make cleanup            # Очистка
```

## Architecture

- **Atlas Core**: Основна логіка та AI агенти
- **MCP Automation**: Model Context Protocol сервер  
- **MCP Automator**: macOS системна автоматизація
- **Kubernetes**: Професійне управління контейнерами
- **Monitoring**: Prometheus + Grafana стек
- **Storage**: Persistent volumes для даних
- **Networking**: Ingress з SSL та load balancing
- **Security**: RBAC, Network Policies, Pod Security

## Environment Variables

Див. `.env.k8s.example` для повного списку змінних середовища.

## Monitoring & Observability

- **Prometheus**: Метрики та алерти
- **Grafana**: Візуалізація та дашборди  
- **Kubernetes Dashboard**: Управління кластером
- **Logs**: Централізований збір логів

## Security Features

- **RBAC**: Role-based access control
- **Network Policies**: Мережева ізоляція
- **Pod Security**: Security contexts та policies
- **Secrets Management**: Безпечне зберігання секретів
- **SSL/TLS**: Шифрування трафіку

## Scaling & High Availability

- **HPA**: Horizontal Pod Autoscaler
- **PDB**: Pod Disruption Budgets
- **Multi-replica**: Багато інстансів сервісів
- **Load Balancing**: Розподіл навантаження
- **Health Checks**: Автоматичне відновлення

---
*Документація оновлена після організації проекту та архівування застарілих файлів.*
