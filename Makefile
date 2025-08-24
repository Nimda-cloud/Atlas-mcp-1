# Atlas MCP Kubernetes Makefile

.PHONY: help install-dev install-prod update-dev update-prod status-dev status-prod logs scale restart backup monitoring diagnose clean

# Змінні
SCRIPT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
K8S_SCRIPT := $(SCRIPT_DIR)/k8s-manage.sh
ENV_DEV := development
ENV_PROD := production

# Кольори для виводу
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

# Допомога
help: ## Показати цю допомогу
	@echo "$(GREEN)Atlas MCP Kubernetes Management$(NC)"
	@echo ""
	@echo "Доступні команди:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Встановлення
install-dev: ## Встановити в development середовище
	@echo "$(GREEN)Встановлення Atlas MCP в development середовище...$(NC)"
	$(K8S_SCRIPT) install $(ENV_DEV)

install-prod: ## Встановити в production середовище
	@echo "$(GREEN)Встановлення Atlas MCP в production середовище...$(NC)"
	$(K8S_SCRIPT) install $(ENV_PROD)

# Оновлення
update-dev: ## Оновити development середовище
	@echo "$(GREEN)Оновлення Atlas MCP в development середовище...$(NC)"
	$(K8S_SCRIPT) update $(ENV_DEV)

update-prod: ## Оновити production середовище
	@echo "$(GREEN)Оновлення Atlas MCP в production середовище...$(NC)"
	$(K8S_SCRIPT) update $(ENV_PROD)

# Статус
status-dev: ## Показати статус development середовища
	$(K8S_SCRIPT) status $(ENV_DEV)

status-prod: ## Показати статус production середовища
	$(K8S_SCRIPT) status $(ENV_PROD)

# Логи
logs-dev: ## Показати логи Atlas Core в development
	$(K8S_SCRIPT) logs $(ENV_DEV) atlas-core

logs-prod: ## Показати логи Atlas Core в production
	$(K8S_SCRIPT) logs $(ENV_PROD) atlas-core

logs-frontend-dev: ## Показати логи Frontend в development
	$(K8S_SCRIPT) logs $(ENV_DEV) atlas-frontend

logs-frontend-prod: ## Показати логи Frontend в production
	$(K8S_SCRIPT) logs $(ENV_PROD) atlas-frontend

# Скалювання
scale-frontend-dev: ## Скалювати frontend в development (використайте REPLICAS=N)
	$(K8S_SCRIPT) scale $(ENV_DEV) atlas-frontend $(or $(REPLICAS),3)

scale-frontend-prod: ## Скалювати frontend в production (використайте REPLICAS=N)
	$(K8S_SCRIPT) scale $(ENV_PROD) atlas-frontend $(or $(REPLICAS),5)

scale-core-dev: ## Скалювати core в development (використайте REPLICAS=N)
	$(K8S_SCRIPT) scale $(ENV_DEV) atlas-core $(or $(REPLICAS),2)

scale-core-prod: ## Скалювати core в production (використайте REPLICAS=N)
	$(K8S_SCRIPT) scale $(ENV_PROD) atlas-core $(or $(REPLICAS),3)

# Перезапуск
restart-dev: ## Перезапустити всі сервіси в development
	$(K8S_SCRIPT) restart $(ENV_DEV)

restart-prod: ## Перезапустити всі сервіси в production
	$(K8S_SCRIPT) restart $(ENV_PROD)

# Резервне копіювання
backup-dev: ## Створити резервну копію development
	$(K8S_SCRIPT) backup $(ENV_DEV)

backup-prod: ## Створити резервну копію production
	$(K8S_SCRIPT) backup $(ENV_PROD)

# Моніторинг
monitoring-dev: ## Показати моніторинг development
	$(K8S_SCRIPT) monitoring $(ENV_DEV)

monitoring-prod: ## Показати моніторинг production
	$(K8S_SCRIPT) monitoring $(ENV_PROD)

# Діагностика
diagnose-dev: ## Виконати діагностику development
	$(K8S_SCRIPT) diagnose $(ENV_DEV)

diagnose-prod: ## Виконати діагностику production
	$(K8S_SCRIPT) diagnose $(ENV_PROD)

# Очищення
clean-dev: ## Видалити development середовище
	@echo "$(YELLOW)УВАГА: Це видалить всі ресурси development середовища!$(NC)"
	$(K8S_SCRIPT) uninstall $(ENV_DEV)

clean-prod: ## Видалити production середовище
	@echo "$(YELLOW)УВАГА: Це видалить всі ресурси production середовища!$(NC)"
	$(K8S_SCRIPT) uninstall $(ENV_PROD)

# Швидкі команди
dev: install-dev ## Швидке встановлення в development

prod: install-prod ## Швидке встановлення в production

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
