# Atlas MCP Makefile
# ==================
# Простий інтерфейс для управління Atlas системою

.PHONY: help deploy update start stop status tools clean

# Default goal
.DEFAULT_GOAL := help

help: ## Показати цю довідку
	@echo "🚀 Atlas MCP Management"
	@echo "======================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

deploy: ## Повне розгортання Atlas з нуля
	@echo "🚀 Deploying Atlas..."
	./deploy_atlas.sh

deploy-quick: ## Швидке розгортання (мінімум компонентів)
	@echo "⚡ Quick deployment..."
	./deploy_atlas.sh --quick

update: ## Оновити Atlas компоненти
	@echo "🔄 Updating Atlas..."
	./update_atlas.sh

update-mcp: ## Оновити тільки MCP компоненти
	@echo "🔄 Updating MCP components..."
	./update_atlas.sh --mcp-only

start: ## Запустити Atlas
	@echo "▶️ Starting Atlas..."
	./start_atlas.sh

start-viewer: ## Запустити Atlas з 3D viewer
	@echo "▶️ Starting Atlas with viewer..."
	./start_atlas.sh --viewer

start-no-proxy: ## Запустити Atlas без MCP proxy
	@echo "▶️ Starting Atlas (direct mode)..."
	./start_atlas.sh --no-proxy

stop: ## Зупинити Atlas
	@echo "⏹️ Stopping Atlas..."
	./stop_atlas.sh

restart: stop start ## Перезапустити Atlas
	@echo "🔄 Atlas restarted"

status: ## Показати статус Atlas
	@echo "📊 Atlas Status:"
	@curl -s http://localhost:8000/ | jq '.' 2>/dev/null || echo "❌ Atlas not running"

health: ## Перевірити здоров'я системи
	@echo "🏥 Health Check:"
	@curl -s http://localhost:8000/health 2>/dev/null || echo "❌ Atlas not responding"
	@echo ""
	@curl -s http://localhost:9090/health 2>/dev/null || echo "❌ MCP Proxy not responding"

tools: ## Показати список доступних інструментів
	@echo "🛠️ Available Tools:"
	@curl -s http://localhost:8000/tools | jq '.total_tools, .tools' 2>/dev/null || echo "❌ Cannot fetch tools"

tools-count: ## Показати кількість інструментів по сервісах
	@echo "📊 Tools by Service:"
	@curl -s http://localhost:8000/ | jq '.mcp_tools' 2>/dev/null || echo "❌ Cannot fetch tool counts"

logs: ## Показати логи Atlas
	@echo "📄 Atlas Logs:"
	@tail -f /tmp/atlas_core.log

logs-orchestrator: ## Показати логи Task Orchestrator
	@echo "📄 Task Orchestrator Logs:"
	@tail -f /tmp/task_orchestrator.log

ps: ## Показати запущені процеси Atlas
	@echo "🔍 Atlas Processes:"
	@ps aux | grep -E "(atlas_core|task_orchestrator|mcp-proxy|better-playwright)" | grep -v grep || echo "No Atlas processes found"

ports: ## Показати зайняті порти Atlas
	@echo "🌐 Atlas Ports:"
	@lsof -i :8000,:9090,:4006,:8080 2>/dev/null || echo "No Atlas ports active"

test: ## Тестування основних компонентів
	@echo "🧪 Testing Atlas Components:"
	@echo -n "Atlas Core (8000): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
	@echo ""
	@echo -n "MCP Proxy (9090): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/health
	@echo ""
	@echo -n "Task Orchestrator (4006): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:4006/health
	@echo ""

clean: ## Очистити тимчасові файли
	@echo "🧹 Cleaning up..."
	@rm -f deployment.log
	@rm -f logs/atlas.log
	@rm -f /tmp/atlas_core.log
	@rm -f /tmp/task_orchestrator.log
	@echo "✅ Cleanup complete"

clean-all: clean ## Повне очищення (включно з venv)
	@echo "💥 Deep cleaning..."
	@rm -rf atlas_venv
	@rm -f .atlas_deployed
	@echo "✅ Deep cleanup complete"

install-deps: ## Встановити системні залежності
	@echo "📦 Installing system dependencies..."
	@brew install python@3.11 node go || echo "Please install Homebrew first"

validate: ## Валідація установки
	@echo "✅ Validating Atlas installation..."
	@test -f ./deploy_atlas.sh && echo "✅ Deployment script found" || echo "❌ Deployment script missing"
	@test -f ./start_atlas.sh && echo "✅ Start script found" || echo "❌ Start script missing"
	@test -d atlas_venv && echo "✅ Python environment found" || echo "❌ Python environment missing"
	@test -f mcp-proxy/atlas-global-config.json && echo "✅ MCP config found" || echo "❌ MCP config missing"
	@test -d applescript-mcp-server && echo "✅ AppleScript MCP found" || echo "❌ AppleScript MCP missing"

validate-mcp: ## Валідація MCP серверів
	@echo "🔍 Validating MCP Servers:"
	@test -f mcp_tts_ukrainian/mcp_tts_server.py && echo "✅ TTS Server" || echo "❌ TTS Server missing"
	@test -f mcp-task-orchestrator/mcp_task_orchestrator/server.py && echo "✅ Task Orchestrator" || echo "❌ Task Orchestrator missing"
	@test -f applescript-mcp-server/dist/index.js && echo "✅ AppleScript MCP" || echo "❌ AppleScript MCP missing"
	@which better-playwright-mcp >/dev/null 2>&1 && echo "✅ Better Playwright MCP" || echo "❌ Better Playwright MCP missing"
	@test -f mcp-proxy/atlas-mcp-proxy && echo "✅ MCP Proxy" || echo "❌ MCP Proxy missing"

backup: ## Створити backup конфігурацій
	@echo "💾 Creating backup..."
	@tar -czf atlas-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		mcp-proxy/*.json \
		*.sh \
		requirements*.txt \
		.env \
		DEPLOYMENT_GUIDE.md
	@echo "✅ Backup created"

info: ## Показати інформацію про систему
	@echo "ℹ️  Atlas System Information:"
	@echo "Working Directory: $(PWD)"
	@echo "Python: $(shell python3 --version 2>/dev/null || echo 'Not found')"
	@echo "Node.js: $(shell node --version 2>/dev/null || echo 'Not found')"
	@echo "Go: $(shell go version 2>/dev/null || echo 'Not found')"
	@echo "NPM Global MCP: $(shell npm list -g --depth=0 2>/dev/null | grep -c mcp || echo '0') packages"
	@test -f .atlas_deployed && echo "Status: ✅ Deployed" || echo "Status: ❌ Not deployed"

# Aliases for convenience
deploy-all: deploy ## Alias for deploy
up: start ## Alias for start  
down: stop ## Alias for stop
refresh: restart ## Alias for restart
