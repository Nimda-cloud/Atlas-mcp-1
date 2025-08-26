#!/bin/bash

# Atlas MCP Proxy Installer
# Встановлення та збірка TBXark/mcp-proxy для Atlas екосистеми

set -e

echo "🚀 Atlas MCP Proxy Installer"
echo "=============================="

# Перевірка Go
if ! command -v go &> /dev/null; then
    echo "❌ Go не знайдено!"
    echo ""
    echo "📋 Варіанти встановлення Go:"
    echo "   macOS:   brew install go"
    echo "   Linux:   sudo apt install golang-go"
    echo "   Manual:  https://golang.org/dl/"
    echo ""
    exit 1
fi

GO_VERSION=$(go version | grep -o 'go[0-9.]*' | head -1)
echo "✅ Знайдено $GO_VERSION"

# Перевірка версії
if ! go version | grep -E 'go1\.(2[3-9]|[3-9][0-9])' &> /dev/null; then
    echo "⚠️  Рекомендовано Go 1.23+, поточна: $GO_VERSION"
fi

# Директорії
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$SCRIPT_DIR"

echo ""
echo "📦 Варіанти встановлення mcp-proxy:"
echo "   1. Збірка з локального коду (рекомендовано)"
echo "   2. go install з GitHub (остання версія)"
echo "   3. Стабільна версія з GitHub"
echo ""

read -p "Оберіть варіант (1-3) [1]: " choice
choice=${choice:-1}

case $choice in
    1)
        echo ""
        echo "🔧 Збірка з локального коду..."
        
        if [[ ! -f "go.mod" ]]; then
            echo "📋 Ініціалізація Go модуля..."
            go mod init mcp-proxy
        fi
        
        # Оновлення залежностей
        echo "📥 Оновлення залежностей..."
        go mod tidy
        go mod download
        
        # Збірка
        echo "🔨 Збірка atlas-mcp-proxy..."
        go build -v -ldflags="-s -w" -o atlas-mcp-proxy .
        
        echo "✅ Збірка завершена: atlas-mcp-proxy"
        ;;
        
    2)
        echo ""
        echo "📥 Встановлення latest версії з GitHub..."
        go install github.com/TBXark/mcp-proxy@latest
        
        # Копіювання в локальну директорію
        GOBIN=${GOBIN:-$(go env GOPATH)/bin}
        if [[ -f "$GOBIN/mcp-proxy" ]]; then
            cp "$GOBIN/mcp-proxy" ./atlas-mcp-proxy
            echo "✅ Встановлено: atlas-mcp-proxy (latest)"
        else
            echo "❌ Не вдалося знайти встановлений mcp-proxy"
            exit 1
        fi
        ;;
        
    3)
        echo ""
        echo "📥 Встановлення стабільної версії з GitHub..."
        go install github.com/TBXark/mcp-proxy
        
        # Копіювання в локальну директорію
        GOBIN=${GOBIN:-$(go env GOPATH)/bin}
        if [[ -f "$GOBIN/mcp-proxy" ]]; then
            cp "$GOBIN/mcp-proxy" ./atlas-mcp-proxy
            echo "✅ Встановлено: atlas-mcp-proxy (stable)"
        else
            echo "❌ Не вдалося знайти встановлений mcp-proxy"
            exit 1
        fi
        ;;
        
    *)
        echo "❌ Невірний вибір"
        exit 1
        ;;
esac

# Права на виконання
chmod +x atlas-mcp-proxy
chmod +x start-atlas-proxy.sh

echo ""
echo "🎯 Перевірка встановлення..."

# Тест запуску
if ./atlas-mcp-proxy --help &> /dev/null; then
    echo "✅ atlas-mcp-proxy працює"
else
    echo "⚠️  atlas-mcp-proxy може мати проблеми"
fi

# Перевірка конфігурацій
echo ""
echo "📋 Доступні конфігурації:"
for config in *.json; do
    if [[ -f "$config" ]]; then
        echo "   ✓ $config"
    fi
done

echo ""
echo "🚀 Встановлення завершено!"
echo ""
echo "🔧 Наступні кроки:"
echo "   1. Запуск базової конфігурації:"
echo "      ./start-atlas-proxy.sh"
echo ""
echo "   2. Запуск глобальної конфігурації:"
echo "      ./start-atlas-proxy.sh --global"
echo ""
echo "   3. Інтеграція з Atlas:"
echo "      cd .. && ./start_atlas.sh"
echo ""
echo "🌐 Порт: http://localhost:9090"
