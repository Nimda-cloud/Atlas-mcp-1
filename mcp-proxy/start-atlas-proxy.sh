#!/bin/bash
# Запуск MCP Proxy для Atlas
set -euo pipefail

# Перевірка середовища Go
if ! command -v go &> /dev/null; then
    echo "❌ Go не встановлено. Встановіть Go 1.23+ для запуску MCP Proxy"
    exit 1
fi

# Перевірка версії Go
GO_VERSION=$(go version | grep -o 'go[0-9]\+\.[0-9]\+' | head -1)
if [[ "$GO_VERSION" < "go1.23" ]]; then
    echo "❌ Потрібна версія Go 1.23+, встановлена: $GO_VERSION"
    exit 1
fi

# Папка проекту
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 Налаштування MCP Proxy для Atlas..."

# Встановлення залежностей
echo "📦 Встановлення Go залежностей..."
go mod tidy

# Білдування
echo "🔨 Збірка MCP Proxy..."
go build -o mcp-proxy .

# Запуск з Atlas конфігом
CONFIG_FILE="${1:-atlas-config.json}"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "❌ Конфіг файл не знайдено: $CONFIG_FILE"
    echo "Використання: $0 [config-file]"
    echo "За замовчуванням: atlas-config.json"
    exit 1
fi

echo "🚀 Запуск MCP Proxy з конфігом: $CONFIG_FILE"
echo "📍 Proxy буде доступний на: http://localhost:4010"
echo "🛑 Для зупинки натисніть Ctrl+C"
echo

# Запуск з логуванням
./mcp-proxy -config "$CONFIG_FILE"
