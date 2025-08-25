# Atlas MCP Kubernetes Makefile - Расширенная версия

.PHONY: help deploy deploy-full restart clean status logs ports scale build-images test health monitoring debug

# Переменные
SCRIPT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
DEPLOY_SCRIPT := $(SCRIPT_DIR)/atlas_k8s_full_deploy.sh
K8S_SCRIPT := $(SCRIPT_DIR)/k8s-manage.sh
ENV_DEV := development
ENV_PROD := production
NAMESPACE := atlas-mcp-dev

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m

# Помощь
help: ## Показать эту справку
	@echo "$(BLUE)╔══════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║          Atlas MCP Kubernetes Management             ║$(NC)"
	@echo "$(BLUE)╚══════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)🚀 Основные команды:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)📝 Примеры использования:$(NC)"
	@echo "  make deploy-full     # Полное развертывание с нуля"
	@echo "  make status          # Проверить состояние системы"
	@echo "  make logs            # Посмотреть логи Atlas Core"
	@echo "  make clean           # Полная очистка"

# Полное развертывание
deploy-full: ## 🚀 Полное развертывание Atlas MCP (новый подход)
	@echo "$(GREEN)🚀 Запуск полного развертывания Atlas MCP...$(NC)"
	$(DEPLOY_SCRIPT) deploy

restart: ## 🔄 Перезапуск всего стека
	@echo "$(YELLOW)🔄 Перезапуск Atlas MCP стека...$(NC)"
	$(DEPLOY_SCRIPT) restart

# Быстрое развертывание (старый подход)
deploy: install-dev ## 📦 Быстрое развертывание (legacy)

install-dev: ## 📦 Установить в development среду
	@echo "$(GREEN)📦 Установка Atlas MCP в development среду...$(NC)"
	$(K8S_SCRIPT) install $(ENV_DEV)

install-prod: ## 📦 Установить в production среду
	@echo "$(GREEN)📦 Установка Atlas MCP в production среду...$(NC)"
	$(K8S_SCRIPT) install $(ENV_PROD)

# Обновление
update-dev: ## 🔄 Обновить development среду
	@echo "$(GREEN)🔄 Обновление Atlas MCP в development среду...$(NC)"
	$(K8S_SCRIPT) update $(ENV_DEV)

update-prod: ## 🔄 Обновить production среду
	@echo "$(GREEN)🔄 Обновление Atlas MCP в production среду...$(NC)"
	$(K8S_SCRIPT) update $(ENV_PROD)

# Статус и мониторинг
status: ## 📊 Показать статус всех сервисов
	@echo "$(BLUE)📊 Статус Atlas MCP системы:$(NC)"
	$(DEPLOY_SCRIPT) status

status-dev: ## 📊 Показать статус development среды
	$(K8S_SCRIPT) status $(ENV_DEV)

status-prod: ## 📊 Показать статус production среды
	$(K8S_SCRIPT) status $(ENV_PROD)

# Логи
logs: ## 📜 Показать логи Atlas Core
	@echo "$(BLUE)📜 Логи Atlas Core:$(NC)"
	$(DEPLOY_SCRIPT) logs

logs-dev: ## 📜 Показать логи Atlas Core в development
	$(K8S_SCRIPT) logs $(ENV_DEV) atlas-core

logs-prod: ## 📜 Показать логи Atlas Core в production
	$(K8S_SCRIPT) logs $(ENV_PROD) atlas-core

logs-all: ## 📜 Показать все логи
	@echo "$(BLUE)📜 Все логи системы:$(NC)"
	kubectl logs -n $(NAMESPACE) -l app=atlas-core --tail=50
	kubectl logs -n $(NAMESPACE) -l app=atlas-frontend --tail=30
	kubectl logs -n $(NAMESPACE) -l app=mcp-automation --tail=20

# Порты и доступ
ports: ## 🌐 Настроить port forwarding
	@echo "$(GREEN)🌐 Настройка port forwarding...$(NC)"
	@echo "Atlas Core:      http://localhost:8000"
	@echo "3D Frontend:     http://localhost:8080"
	@echo "Grafana:         http://localhost:3000"
	@echo "Prometheus:      http://localhost:9090"
	kubectl port-forward -n $(NAMESPACE) service/atlas-core-service 8000:8000 &
	kubectl port-forward -n $(NAMESPACE) service/atlas-frontend-service 8080:8080 &
	kubectl port-forward -n $(NAMESPACE) service/grafana-service 3000:3000 &
	kubectl port-forward -n $(NAMESPACE) service/prometheus-service 9090:9090 &

# Сборка образов
build-images: ## 🏗️ Собрать все Docker образы
	@echo "$(GREEN)🏗️ Сборка Docker образов...$(NC)"
	docker build -t atlas-core:latest .
	docker build -t atlas-frontend:latest ./3d_helmet_viewer/
	docker build -t mcp-automation:latest -f Dockerfile.mcp-automation .
	docker build -t mcp-automator:latest -f Dockerfile.mcp-automator .

# Тестирование
test: ## 🧪 Запустить тесты
	@echo "$(GREEN)🧪 Запуск тестов...$(NC)"
	python test_basic.py
	python test_atlas.py

health: ## 🏥 Проверить здоровье всех сервисов
	@echo "$(BLUE)🏥 Проверка здоровья сервисов:$(NC)"
	@curl -s -f http://localhost:8000/health && echo "✅ Atlas Core: OK" || echo "❌ Atlas Core: FAIL"
	@curl -s -f http://localhost:8080/ && echo "✅ Frontend: OK" || echo "❌ Frontend: FAIL"
	@curl -s -f http://localhost:3000/ && echo "✅ Grafana: OK" || echo "❌ Grafana: FAIL"
	@curl -s -f http://localhost:9090/ && echo "✅ Prometheus: OK" || echo "❌ Prometheus: FAIL"
	@curl -s -f http://localhost:4002/health && echo "✅ MCP Automation: OK" || echo "❌ MCP Automation: FAIL"
	@curl -s -f http://localhost:4003/health && echo "✅ MCP Automator: OK" || echo "❌ MCP Automator: FAIL"
	@curl -s -f http://localhost:4004/health && echo "✅ MCP TTS: OK" || echo "❌ MCP TTS: FAIL"
	@curl -s -f http://localhost:4005/health && echo "✅ MCP Playwright: OK" || echo "❌ MCP Playwright: FAIL"

# Масштабирование
scale: ## ⚖️ Масштабировать сервисы (REPLICAS=N)
	@echo "$(YELLOW)⚖️ Масштабирование сервисов...$(NC)"
	kubectl scale deployment atlas-core -n $(NAMESPACE) --replicas=$(or $(REPLICAS),2)
	kubectl scale deployment atlas-frontend -n $(NAMESPACE) --replicas=$(or $(REPLICAS),3)

scale-frontend-dev: ## ⚖️ Масштабировать frontend в development (REPLICAS=N)
	$(K8S_SCRIPT) scale $(ENV_DEV) atlas-frontend $(or $(REPLICAS),3)

scale-frontend-prod: ## ⚖️ Масштабировать frontend в production (REPLICAS=N)
	$(K8S_SCRIPT) scale $(ENV_PROD) atlas-frontend $(or $(REPLICAS),5)

scale-core-dev: ## ⚖️ Масштабировать core в development (REPLICAS=N)
	$(K8S_SCRIPT) scale $(ENV_DEV) atlas-core $(or $(REPLICAS),2)

scale-core-prod: ## ⚖️ Масштабировать core в production (REPLICAS=N)
	$(K8S_SCRIPT) scale $(ENV_PROD) atlas-core $(or $(REPLICAS),3)

# Мониторинг
monitoring: ## 📊 Открыть мониторинг
	@echo "$(BLUE)📊 Открытие интерфейсов мониторинга...$(NC)"
	@echo "Grafana:    http://localhost:3000 (admin/atlas_admin)"
	@echo "Prometheus: http://localhost:9090"
	open http://localhost:3000 || true
	open http://localhost:9090 || true

monitoring-dev: ## 📊 Показать мониторинг development
	$(K8S_SCRIPT) monitoring $(ENV_DEV)

monitoring-prod: ## 📊 Показать мониторинг production
	$(K8S_SCRIPT) monitoring $(ENV_PROD)

# Диагностика и отладка
debug: ## 🔍 Показать подробную информацию для отладки
	@echo "$(BLUE)🔍 Диагностическая информация:$(NC)"
	@echo "$(YELLOW)Кластер:$(NC)"
	kubectl cluster-info
	@echo "$(YELLOW)Namespace $(NAMESPACE):$(NC)"
	kubectl get all -n $(NAMESPACE)
	@echo "$(YELLOW)События:$(NC)"
	kubectl get events -n $(NAMESPACE) --sort-by='.lastTimestamp' | tail -10
	@echo "$(YELLOW)Использование ресурсов:$(NC)"
	kubectl top pods -n $(NAMESPACE) || echo "Metrics server не доступен"

diagnose-dev: ## 🔍 Выполнить диагностику development
	$(K8S_SCRIPT) diagnose $(ENV_DEV)

diagnose-prod: ## 🔍 Выполнить диагностику production
	$(K8S_SCRIPT) diagnose $(ENV_PROD)

# Очистка
clean: ## 🧹 Полная очистка (удалить кластер и все данные)
	@echo "$(RED)⚠️  ВНИМАНИЕ: Это удалит весь кластер и все данные!$(NC)"
	@read -p "Введите 'YES' для подтверждения: " confirm && [ "$$confirm" = "YES" ] || exit 1
	$(DEPLOY_SCRIPT) clean

clean-dev: ## 🧹 Удалить development среду
	@echo "$(YELLOW)⚠️  ВНИМАНИЕ: Это удалит все ресурсы development среды!$(NC)"
	$(K8S_SCRIPT) uninstall $(ENV_DEV)

clean-prod: ## 🧹 Удалить production среду
	@echo "$(RED)⚠️  ВНИМАНИЕ: Это удалит все ресурсы production среды!$(NC)"
	$(K8S_SCRIPT) uninstall $(ENV_PROD)

# Резервное копирование
backup-dev: ## 💾 Создать резервную копию development
	$(K8S_SCRIPT) backup $(ENV_DEV)

backup-prod: ## 💾 Создать резервную копию production
	$(K8S_SCRIPT) backup $(ENV_PROD)

# Быстрые команды
dev: install-dev ## ⚡ Быстрая установка в development

prod: install-prod ## ⚡ Быстрая установка в production

up: deploy-full ## ⚡ Быстрый запуск (алиас для deploy-full)

down: clean ## ⚡ Быстрая остановка (алиас для clean)

# Утилиты
shell-atlas: ## 🐚 Подключиться к shell Atlas Core
	kubectl exec -it -n $(NAMESPACE) deployment/atlas-core -- /bin/bash

shell-frontend: ## 🐚 Подключиться к shell Frontend
	kubectl exec -it -n $(NAMESPACE) deployment/atlas-frontend -- /bin/sh

# Информация о системе
info: ## ℹ️ Показать информацию о системе
	@echo "$(BLUE)╔══════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║               Atlas MCP System Info                  ║$(NC)"
	@echo "$(BLUE)╚══════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)🌐 Доступные URL:$(NC)"
	@echo "  Atlas Web UI:     http://localhost:8000"
	@echo "  3D Frontend:      http://localhost:8080"
	@echo "  Grafana:          http://localhost:3000 (admin/atlas_admin)"
	@echo "  Prometheus:       http://localhost:9090"
	@echo "  MCP Automation:   http://localhost:4002"
	@echo "  MCP Automator:    http://localhost:4003"
	@echo "  MCP TTS:          http://localhost:4004"
	@echo "  MCP Playwright:   http://localhost:4005"
	@echo ""
	@echo "$(GREEN)🔧 Основные команды:$(NC)"
	@echo "  make deploy-full  # Полное развертывание"
	@echo "  make status       # Проверить статус"
	@echo "  make health       # Проверить здоровье сервисов"
	@echo "  make logs         # Показать логи"
	@echo "  make clean        # Полная очистка"
	@echo ""
	@echo "$(GREEN)📊 Статус кластера:$(NC)"
	@kubectl cluster-info --context kind-atlas-mcp-cluster 2>/dev/null || echo "  Кластер не запущен"

status: status-dev ## Швидкий статус development

logs: logs-dev ## Швидкі логи development

# Налаштування кластера
setup-cluster: ## Налаштувати кластер для Atlas MCP
	@echo "$(GREEN)Налаштування кластера...$(NC)"
	kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
	@echo "$(GREEN)Встановлення NGINX Ingress Controller...$(NC)"
	kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
	@echo "$(GREEN)Очікування готовності NGINX Ingress...$(NC)"
	kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=300s

# Порт-форвардинг
port-forward-grafana-dev: ## Перенаправлення порту Grafana development (localhost:3000)
	kubectl port-forward svc/grafana-service 3000:3000 -n atlas-mcp-dev

port-forward-grafana-prod: ## Перенаправлення порту Grafana production (localhost:3000)
	kubectl port-forward svc/grafana-service 3000:3000 -n atlas-mcp-prod

port-forward-prometheus-dev: ## Перенаправлення порту Prometheus development (localhost:9090)
	kubectl port-forward svc/prometheus-service 9090:9090 -n atlas-mcp-dev

port-forward-prometheus-prod: ## Перенаправлення порту Prometheus production (localhost:9090)
	kubectl port-forward svc/prometheus-service 9090:9090 -n atlas-mcp-prod

port-forward-atlas-dev: ## Перенаправлення порту Atlas development (localhost:8080)
	kubectl port-forward svc/atlas-frontend-service 8080:8080 -n atlas-mcp-dev

port-forward-atlas-prod: ## Перенаправлення порту Atlas production (localhost:8080)
	kubectl port-forward svc/atlas-frontend-service 8080:8080 -n atlas-mcp-prod

# Створення secrets
create-secrets-dev: ## Створити secrets для development
	@echo "$(GREEN)Створення secrets для development...$(NC)"
	kubectl create secret generic atlas-secrets \
		--from-literal=GOOGLE_TTS_API_KEY="" \
		--from-literal=GRAFANA_ADMIN_PASSWORD="dev_admin" \
		--namespace=atlas-mcp-dev \
		--dry-run=client -o yaml | kubectl apply -f -

create-secrets-prod: ## Створити secrets для production (потребує файли secrets/)
	@echo "$(GREEN)Створення secrets для production...$(NC)"
	@if [ ! -d "secrets" ]; then echo "$(YELLOW)Створіть директорію secrets/ з файлами секретів$(NC)"; exit 1; fi
	kubectl create secret generic atlas-secrets \
		--from-file=GOOGLE_TTS_API_KEY=secrets/google-tts-api-key.txt \
		--from-file=GRAFANA_ADMIN_PASSWORD=secrets/grafana-admin-password.txt \
		--namespace=atlas-mcp-prod \
		--dry-run=client -o yaml | kubectl apply -f -

# Тестування
test-dev: ## Виконати тести для development
	@echo "$(GREEN)Тестування Atlas MCP в development...$(NC)"
	kubectl run atlas-test --image=curlimages/curl --rm -it --restart=Never -- \
		curl -f http://atlas-frontend-service.atlas-mcp-dev.svc.cluster.local:8080/health

test-prod: ## Виконати тести для production
	@echo "$(GREEN)Тестування Atlas MCP в production...$(NC)"
	kubectl run atlas-test --image=curlimages/curl --rm -it --restart=Never -- \
		curl -f http://atlas-frontend-service.atlas-mcp-prod.svc.cluster.local:8080/health

# Очищення Docker образів
build-images: ## Побудувати всі Docker образи
	@echo "$(GREEN)Побудова Docker образів...$(NC)"
	docker build -t atlas-mcp/atlas-core:latest .
	docker build -t atlas-mcp/atlas-frontend:latest ./3d_helmet_viewer/
	docker build -t atlas-mcp/mcp-automation:latest -f Dockerfile.mcp-automation .
	docker build -t atlas-mcp/mcp-automator:latest -f Dockerfile.mcp-automator .
	docker build -t atlas-mcp/mcp-tts:latest ./services/tts_mcp_adapter/

push-images: ## Завантажити образи в registry (потребує REGISTRY змінну)
	@if [ -z "$(REGISTRY)" ]; then echo "$(YELLOW)Встановіть змінну REGISTRY$(NC)"; exit 1; fi
	@echo "$(GREEN)Завантаження образів в $(REGISTRY)...$(NC)"
	docker tag atlas-mcp/atlas-core:latest $(REGISTRY)/atlas-mcp/atlas-core:latest
	docker tag atlas-mcp/atlas-frontend:latest $(REGISTRY)/atlas-mcp/atlas-frontend:latest
	docker tag atlas-mcp/mcp-automation:latest $(REGISTRY)/atlas-mcp/mcp-automation:latest
	docker tag atlas-mcp/mcp-automator:latest $(REGISTRY)/atlas-mcp/mcp-automator:latest
	docker tag atlas-mcp/mcp-tts:latest $(REGISTRY)/atlas-mcp/mcp-tts:latest
	docker push $(REGISTRY)/atlas-mcp/atlas-core:latest
	docker push $(REGISTRY)/atlas-mcp/atlas-frontend:latest
	docker push $(REGISTRY)/atlas-mcp/mcp-automation:latest
	docker push $(REGISTRY)/atlas-mcp/mcp-automator:latest
	docker push $(REGISTRY)/atlas-mcp/mcp-tts:latest

# Швидкий деплой
quick-deploy-dev: build-images install-dev ## Побудувати образи та розгорнути в development

# Повний цикл
full-cycle-dev: build-images install-dev test-dev status-dev ## Повний цикл розгортання та тестування в development

# Дефолтна ціль
.DEFAULT_GOAL := help
