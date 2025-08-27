#!/bin/bash

# Atlas MCP Inspector - детальна діагностика MCP інструментів
# Використовує офіційний MCP Inspector для аналізу проблем

set -e

echo "🔍 Atlas MCP Inspector"
echo "====================="
echo "Timestamp: $(date)"
echo ""

# Перевірка чи встановлений MCP Inspector
if ! command -v mcp-inspector &> /dev/null; then
    echo "❌ MCP Inspector не знайдено. Встановлюємо..."
    npm install -g @modelcontextprotocol/inspector
fi

echo "✅ MCP Inspector готовий"
echo ""

# Функція для інспекції окремого сервісу
inspect_mcp_service() {
    local service_name="$1"
    local config_path="$2"
    
    echo "🔍 Інспекція сервісу: $service_name"
    echo "Конфігурація: $config_path"
    echo "----------------------------------------"
    
    if [[ -f "$config_path" ]]; then
        echo "📋 Конфігурація знайдена"
        
        # Запускаємо інспектор для цього сервісу
        timeout 30 mcp-inspector "$config_path" 2>&1 || {
            echo "❌ Помилка інспекції або timeout для $service_name"
            return 1
        }
    else
        echo "❌ Конфігурація не знайдена: $config_path"
        return 1
    fi
    
    echo ""
}

# Функція для перевірки живих процесів MCP
check_live_mcp_processes() {
    echo "🔄 Перевірка активних MCP процесів"
    echo "================================="
    
    # Перевірка Atlas Core
    if curl -s http://localhost:8000/tools > /dev/null; then
        echo "✅ Atlas Core (:8000) - працює"
        echo "📊 Кількість інструментів: $(curl -s http://localhost:8000/tools | jq -r '.total_tools // 0')"
        echo "📋 Сервіси: $(curl -s http://localhost:8000/tools | jq -r '.services[]?' | tr '\n' ', ' | sed 's/,$//')"
    else
        echo "❌ Atlas Core (:8000) - не доступний"
    fi
    
    # Перевірка Task Orchestrator
    if curl -s http://localhost:4006/health > /dev/null; then
        echo "✅ Task Orchestrator (:4006) - працює"
        echo "📊 Статус: $(curl -s http://localhost:4006/health | jq -r '.status // "unknown"')"
    else
        echo "❌ Task Orchestrator (:4006) - не доступний"
    fi
    
    # Перевірка MCP Proxy
    if curl -s -m 5 http://localhost:9090 2>&1 | grep -q "404\|page not found"; then
        echo "⚠️ MCP Proxy (:9090) - працює, але віддає 404"
        echo "🔍 Потребує детальної діагностики ендпоінтів"
    elif curl -s -m 5 http://localhost:9090 > /dev/null; then
        echo "✅ MCP Proxy (:9090) - працює"
    else
        echo "❌ MCP Proxy (:9090) - не доступний"
    fi
    
    echo ""
}

# Функція для тестування конкретних ендпоінтів MCP Proxy
test_mcp_proxy_endpoints() {
    echo "🎯 Тестування ендпоінтів MCP Proxy"
    echo "================================="
    
    local endpoints=(
        "/atlas-applescript-mcp/"
        "/atlas-playwright-better/"
        "/atlas-automation-mcp/"
        "/atlas-task-orchestrator/"
        "/atlas-tts-ukrainian/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        echo -n "Тестування $endpoint: "
        
        response=$(curl -s -w "%{http_code}" -H "Authorization: Bearer atlas-default-token" \
                   "http://localhost:9090$endpoint" -o /dev/null 2>/dev/null || echo "ERROR")
        
        case "$response" in
            200) echo "✅ OK" ;;
            401) echo "🔐 Unauthorized (потрібна авторизація)" ;;
            404) echo "❌ Not Found" ;;
            500) echo "💥 Server Error" ;;
            ERROR) echo "❌ Connection Failed" ;;
            *) echo "⚠️ HTTP $response" ;;
        esac
    done
    
    echo ""
}

# Функція для експорту діагностичної інформації
export_diagnostic_info() {
    echo "📊 Експорт діагностичної інформації"
    echo "==================================="
    
    local report_file="mcp_diagnostic_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== Atlas MCP Diagnostic Report ==="
        echo "Generated: $(date)"
        echo "System: $(uname -a)"
        echo ""
        
        echo "=== Process Status ==="
        ps aux | grep -E "(atlas|mcp|task_orchestrator)" | grep -v grep
        echo ""
        
        echo "=== Port Status ==="
        netstat -an | grep -E "(8000|4006|9090|8080)" || lsof -i -P | grep -E "(8000|4006|9090|8080)"
        echo ""
        
        echo "=== Atlas Core Tools ==="
        curl -s http://localhost:8000/tools 2>/dev/null | jq . || echo "Failed to get tools"
        echo ""
        
        echo "=== Task Orchestrator Health ==="
        curl -s http://localhost:4006/health 2>/dev/null | jq . || echo "Failed to get health"
        echo ""
        
        echo "=== Recent Logs ==="
        echo "--- Atlas Core ---"
        tail -20 /tmp/atlas_core.log 2>/dev/null || echo "No atlas core log"
        echo ""
        echo "--- Task Orchestrator ---"
        tail -20 /tmp/task_orchestrator.log 2>/dev/null || echo "No task orchestrator log"
        echo ""
        echo "--- MCP Proxy ---"
        tail -20 /tmp/mcp_proxy.log 2>/dev/null || echo "No mcp proxy log"
        
    } > "$report_file"
    
    echo "✅ Звіт збережено: $report_file"
    echo ""
}

# Основна функція
main() {
    echo "🚀 Початок діагностики Atlas MCP системи"
    echo ""
    
    check_live_mcp_processes
    test_mcp_proxy_endpoints
    
    # Інспекція конфігурації MCP Proxy
    if [[ -f "mcp-proxy/atlas-global-config.json" ]]; then
        echo "🔍 Аналіз глобальної конфігурації MCP"
        echo "====================================="
        
        # Показуємо конфігурацію сервісів
        echo "📋 Налаштовані сервіси:"
        jq -r '.mcpServers | keys[]' mcp-proxy/atlas-global-config.json 2>/dev/null || echo "❌ Помилка читання конфігурації"
        echo ""
        
        # Перевіряємо кожен сервіс
        while IFS= read -r service; do
            echo "🔧 Сервіс: $service"
            jq -r ".mcpServers[\"$service\"] | to_entries | .[] | \"  \(.key): \(.value)\"" mcp-proxy/atlas-global-config.json 2>/dev/null | head -5
            echo ""
        done < <(jq -r '.mcpServers | keys[]' mcp-proxy/atlas-global-config.json 2>/dev/null)
    fi
    
    export_diagnostic_info
    
    echo "🎯 Рекомендації для виправлення:"
    echo "1. Перевірити логи на помилки аутентифікації"
    echo "2. Переконатися що всі MCP сервіси запущені"
    echo "3. Перевірити правильність URL ендпоінтів"
    echo "4. Тестувати прямі виклики до MCP сервісів"
}

# Запуск
main "$@"
