#!/bin/bash

# Neo4j Setup Script for Atlas MCP
# Ініціалізація та налаштування Neo4j для Task Orchestrator

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🗄️ Neo4j Setup for Atlas MCP${NC}"
echo "==============================="

# Перевірка чи встановлений Neo4j
if ! command -v neo4j &> /dev/null; then
    echo -e "${RED}❌ Neo4j не знайдено${NC}"
    echo -e "${YELLOW}Встановлюємо Neo4j...${NC}"
    brew install neo4j
fi

echo -e "${GREEN}✅ Neo4j знайдено: $(which neo4j)${NC}"

# Запуск Neo4j якщо не працює
if ! brew services list | grep neo4j | grep -q started; then
    echo -e "${YELLOW}🚀 Запускаємо Neo4j...${NC}"
    brew services start neo4j
    
    echo -e "${YELLOW}⏳ Очікування запуску Neo4j (30 секунд)...${NC}"
    sleep 30
else
    echo -e "${GREEN}✅ Neo4j вже працює${NC}"
fi

# Перевірка підключення
echo -e "${YELLOW}🔍 Перевірка підключення до Neo4j...${NC}"
if lsof -i :7687 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Neo4j слухає на порту 7687${NC}"
else
    echo -e "${RED}❌ Neo4j не доступний на порту 7687${NC}"
    echo "Перевіряємо логи Neo4j..."
    brew services info neo4j
    exit 1
fi

# Тестування підключення через cypher-shell
echo -e "${YELLOW}🧪 Тестування підключення...${NC}"
if command -v cypher-shell &> /dev/null; then
    # Спроба підключення з стандартними налаштуваннями
    if echo "RETURN 'Neo4j connection test' as message;" | cypher-shell -u neo4j -p neo4j --non-interactive 2>/dev/null; then
        echo -e "${GREEN}✅ Neo4j підключення працює з стандартними налаштуваннями${NC}"
    else
        echo -e "${YELLOW}⚠️ Потрібно налаштувати пароль Neo4j${NC}"
        echo -e "${BLUE}Налаштовуємо початковий пароль...${NC}"
        
        # Налаштування початкового паролю
        neo4j-admin dbms set-initial-password atlas123 2>/dev/null || {
            echo -e "${YELLOW}Можливо пароль вже встановлений${NC}"
        }
        
        # Повторна перевірка
        if echo "RETURN 'Neo4j connection test' as message;" | cypher-shell -u neo4j -p atlas123 --non-interactive 2>/dev/null; then
            echo -e "${GREEN}✅ Neo4j підключення працює з паролем atlas123${NC}"
        else
            echo -e "${RED}❌ Не вдалося підключитися до Neo4j${NC}"
            echo "Спробуйте вручну:"
            echo "  neo4j-admin dbms set-initial-password <your_password>"
            echo "  cypher-shell -u neo4j -p <your_password>"
        fi
    fi
else
    echo -e "${RED}❌ cypher-shell не знайдено${NC}"
    echo "Встановіть: brew install cypher-shell"
fi

# Створення тестової схеми для Task Orchestrator
echo -e "${YELLOW}📋 Створення тестової схеми...${NC}"
cat > /tmp/neo4j_test_schema.cyql << 'EOF'
// Test schema for Atlas Task Orchestrator
CREATE CONSTRAINT atlas_task_id IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT atlas_session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE;
CREATE INDEX atlas_task_status IF NOT EXISTS FOR (t:Task) ON (t.status);
CREATE INDEX atlas_task_created IF NOT EXISTS FOR (t:Task) ON (t.created_at);

// Test data
MERGE (s:Session {id: "test_session", created_at: datetime()})
MERGE (t:Task {id: "test_task", name: "Test Task", status: "completed", created_at: datetime()})
MERGE (s)-[:HAS_TASK]->(t);

RETURN "Atlas Neo4j schema initialized" as result;
EOF

# Виконання схеми
if cypher-shell -u neo4j -p neo4j < /tmp/neo4j_test_schema.cyql 2>/dev/null || \
   cypher-shell -u neo4j -p atlas123 < /tmp/neo4j_test_schema.cyql 2>/dev/null; then
    echo -e "${GREEN}✅ Тестова схема створена успішно${NC}"
else
    echo -e "${YELLOW}⚠️ Не вдалося створити тестову схему (можливо, уже існує)${NC}"
fi

# Очистка
rm -f /tmp/neo4j_test_schema.cyql

echo ""
echo -e "${GREEN}🎉 Neo4j налаштовано для Atlas MCP!${NC}"
echo ""
echo "📋 Інформація для підключення:"
echo "  URL: neo4j://localhost:7687"
echo "  Username: neo4j"
echo "  Password: neo4j або atlas123"
echo ""
echo "🔧 Корисні команди:"
echo "  brew services start neo4j    # Запуск"
echo "  brew services stop neo4j     # Зупинка"
echo "  brew services restart neo4j  # Перезапуск"
echo "  cypher-shell -u neo4j         # Підключення до CLI"
