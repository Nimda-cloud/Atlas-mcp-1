#!/bin/bash

# Atlas MCP + Neo4j Integration Test
# Тестування інтеграції Atlas з Neo4j після налаштування

set -e

echo "🧪 Atlas + Neo4j Integration Test"
echo "=================================="

# Простий тест створення файлу через пряму команду
echo "🔧 Тест 1: Пряме створення файлу через echo"
echo "Neo4j integration test successful - $(date)" > neo4j_integration_test.txt
if [[ -f "neo4j_integration_test.txt" ]]; then
    echo "✅ Файл створено успішно"
    echo "📄 Вміст: $(cat neo4j_integration_test.txt)"
else
    echo "❌ Файл не створено"
fi

echo ""
echo "🔧 Тест 2: Перевірка Neo4j підключення"
if lsof -i :7687 > /dev/null 2>&1; then
    echo "✅ Neo4j працює на порту 7687"
else
    echo "❌ Neo4j не доступний"
fi

echo ""
echo "🔧 Тест 3: Тест cypher-shell"
if command -v cypher-shell &> /dev/null; then
    echo "✅ cypher-shell знайдено"
    
    # Тест підключення з різними паролями
    for password in "neo4j" "atlas123" ""; do
        echo "   Тестування пароль: '$password'"
        if echo "RETURN 'test' as result;" | cypher-shell -u neo4j -p "$password" --non-interactive 2>/dev/null; then
            echo "   ✅ Підключення з паролем '$password' успішне"
            break
        else
            echo "   ❌ Підключення з паролем '$password' не вдалося"
        fi
    done
else
    echo "❌ cypher-shell не знайдено"
fi

echo ""
echo "🔧 Тест 4: Atlas API тест"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Atlas Core доступний"
else
    echo "❌ Atlas Core не доступний"
fi

if curl -s http://localhost:4006/health > /dev/null 2>&1; then
    echo "✅ Task Orchestrator доступний"
else
    echo "❌ Task Orchestrator не доступний"
fi

echo ""
echo "🔧 Тест 5: MCP Tools через Atlas"
tools_count=$(curl -s http://localhost:8000/tools | jq -r '.total_tools // 0' 2>/dev/null || echo "0")
echo "📊 Доступно інструментів: $tools_count"

if [[ "$tools_count" -gt 100 ]]; then
    echo "✅ Інструменти доступні ($tools_count)"
else
    echo "⚠️ Мало інструментів ($tools_count), можливі проблеми з MCP Proxy"
fi

echo ""
echo "🎯 Рекомендації:"
echo "1. Якщо Neo4j має проблеми з підключенням - перевірте файл конфігурації"
echo "2. Якщо Task Orchestrator не може знайти subtask - це проблема бази даних"
echo "3. Якщо MCP інструментів мало - проблема з MCP Proxy маршрутизацією"

echo ""
echo "🔧 Наступні кроки:"
echo "   - Налаштувати змінні середовища Neo4j"
echo "   - Виправити Task Orchestrator database URI"
echo "   - Протестувати MCP Proxy ендпоінти"
