#!/bin/bash

# Atlas MCP Proxy Starter (Port 9090)
# Глобальна конфігурація для всіх Atlas MCP сервісів

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Запуск Atlas MCP Proxy (Порт 9090)..."

# Перевірка Go
if ! command -v go &> /dev/null; then
    echo "❌ Go не знайдено. Встановіть Go 1.23+ за допомогою:"
    echo "   brew install go"
    echo "   або завантажте з https://golang.org/dl/"
    exit 1
fi

GO_VERSION=$(go version | grep -o 'go[0-9.]*' | head -1)
echo "✅ Знайдено $GO_VERSION"

# Перевірка мінімальної версії (1.23)
if ! go version | grep -E 'go1\.(2[3-9]|[3-9][0-9])' &> /dev/null; then
    echo "⚠️  Потрібно Go 1.23+, поточна: $GO_VERSION"
    echo "   Оновіть Go для стабільної роботи"
fi

cd "$SCRIPT_DIR"

# Вибір конфігурації
if [[ "$1" == "--global" ]] || [[ "$ATLAS_MCP_USE_GLOBAL_CONFIG" == "true" ]]; then
    CONFIG_FILE="atlas-global-config.json"
    echo "📋 Використовуємо глобальну конфігурацію: $CONFIG_FILE"
else
    CONFIG_FILE="atlas-config.json" 
    echo "📋 Використовуємо базову конфігурацію: $CONFIG_FILE"
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "❌ Конфігурація не знайдена: $CONFIG_FILE"
    echo "💡 Доступні конфігурації:"
    ls -la *.json 2>/dev/null || echo "   Не знайдено JSON файлів"
    exit 1
fi

# Експорт змінних оточення
export ATLAS_MCP_PROXY_MODE=true
export ATLAS_MCP_PROXY_URL="http://localhost:9090"
export GO111MODULE=on

echo "🔧 Збірка mcp-proxy..."
if [[ ! -f "go.mod" ]]; then
    echo "❌ go.mod не знайдено. Ініціалізація..."
    go mod init mcp-proxy 2>/dev/null || true
    go mod tidy
fi

# Збірка
go build -v -o atlas-mcp-proxy . || {
    echo "❌ Помилка збірки. Спроба відновлення залежностей..."
    go mod download
    go mod tidy
    go build -v -o atlas-mcp-proxy .
}

echo "✅ Збірка завершена: atlas-mcp-proxy"

# Перевірка порту 9090
if lsof -i :9090 &> /dev/null; then
    echo "⚠️  Порт 9090 зайнято. Завершуємо процеси..."
    pkill -f "atlas-mcp-proxy" 2>/dev/null || true
    lsof -ti :9090 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo "🎯 Запуск Atlas MCP Proxy на порту 9090..."
echo "📋 Конфігурація: $CONFIG_FILE"
echo "🌐 URL: http://localhost:9090"
echo ""

# Запуск з автоматичним перезапуском у випадку збою
while true; do
    ./atlas-mcp-proxy --config "$CONFIG_FILE" || {
        echo "💥 Proxy завершився з помилкою. Перезапуск через 3 секунди..."
        sleep 3
        continue
    }
    break
done
