#!/bin/bash

# Atlas Diagnostic Script
# Автоматична діагностика системи Atlas-mcp
# Дата: $(date)

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║               🔍 ATLAS SYSTEM DIAGNOSTIC TOOL                ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║ Automated system health check and troubleshooting            ║"
echo "║ Generated: $(date)                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 1. Системна інформація
echo_info "=== 🖥️  SYSTEM INFORMATION ==="
echo "Hostname: $(hostname)"
echo "Platform: $(uname -s)"
echo "Architecture: $(uname -m)"
echo "Uptime: $(uptime)"
echo "Date: $(date)"
echo ""

# 2. Перевірка портів
echo_info "=== 🌐 SERVICE PORT CHECK ==="
ports=("8000:Atlas Core" "4006:Task Orchestrator" "9090:MCP Proxy" "8080:3D Viewer" "7687:Neo4j")

for port_info in "${ports[@]}"; do
    port=$(echo $port_info | cut -d: -f1)
    service=$(echo $port_info | cut -d: -f2)
    
    if lsof -i :$port > /dev/null 2>&1; then
        echo_success "Port $port ($service) - ACTIVE"
    else
        echo_warning "Port $port ($service) - NOT ACTIVE"
    fi
done
echo ""

# 3. Neo4j перевірка
echo_info "=== 🗄️ NEO4J DATABASE CHECK ==="
if command -v neo4j &> /dev/null; then
    echo_success "Neo4j binary found: $(which neo4j)"
    
    # Перевірка сервісу Neo4j
    if brew services list | grep neo4j | grep -q started; then
        echo_success "Neo4j service - RUNNING"
        
        # Тест підключення
        if command -v cypher-shell &> /dev/null; then
            echo_info "Testing Neo4j connectivity..."
            if cypher-shell -u neo4j -p neo4j "MATCH (n) RETURN count(n) as node_count" 2>/dev/null; then
                echo_success "Neo4j connectivity - OK"
            else
                echo_warning "Neo4j connectivity - Failed (may need password setup)"
            fi
        else
            echo_warning "cypher-shell not found - cannot test connectivity"
        fi
    else
        echo_warning "Neo4j service - NOT RUNNING"
        echo_info "To start: brew services start neo4j"
    fi
else
    echo_error "Neo4j not installed"
    echo_info "To install: brew install neo4j"
fi
echo ""

for port_info in "${ports[@]}"; do
    port=$(echo $port_info | cut -d':' -f1)
    service=$(echo $port_info | cut -d':' -f2)
    
    if nc -z localhost $port 2>/dev/null; then
        echo_success "Port $port ($service) - LISTENING"
    else
        echo_error "Port $port ($service) - NOT AVAILABLE"
    fi
done
echo ""

# 3. HTTP endpoints тестування
echo_info "=== 🔗 HTTP ENDPOINTS CHECK ==="
endpoints=(
    "http://localhost:8000/status|Atlas Core Status"
    "http://localhost:4006/health|Task Orchestrator Health"
    "http://localhost:9090/health|MCP Proxy Health"
    "http://localhost:8080|3D Viewer"
)

for endpoint_info in "${endpoints[@]}"; do
    endpoint=$(echo $endpoint_info | cut -d'|' -f1)
    name=$(echo $endpoint_info | cut -d'|' -f2)
    
    response=$(curl -s -w "%{http_code}" "$endpoint" -o /dev/null --max-time 5)
    
    if [ "$response" = "200" ]; then
        echo_success "$name - HTTP 200 OK"
    elif [ "$response" = "404" ]; then
        echo_warning "$name - HTTP 404 Not Found"
    elif [ "$response" = "000" ]; then
        echo_error "$name - Connection Failed"
    else
        echo_warning "$name - HTTP $response"
    fi
done
echo ""

# 4. Процеси Atlas
echo_info "=== 🔄 ATLAS PROCESSES ==="
if ps aux | grep -E "(atlas|python.*atlas)" | grep -v grep | head -10; then
    echo_success "Atlas processes found"
else
    echo_warning "No Atlas processes found"
fi
echo ""

# 5. Віртуальне середовище
echo_info "=== 🐍 PYTHON ENVIRONMENT ==="
if [ -d "atlas_venv" ]; then
    echo_success "Virtual environment exists: atlas_venv"
    
    # Активуємо та перевіряємо залежності
    if [ -f "atlas_venv/bin/activate" ]; then
        source atlas_venv/bin/activate
        echo "Python version: $(python --version 2>/dev/null || echo 'Not available')"
        echo "Pip version: $(pip --version 2>/dev/null || echo 'Not available')"
        
        if [ -f "requirements.txt" ]; then
            echo "Dependencies check:"
            pip check 2>/dev/null || echo_warning "Some dependency issues found"
        fi
    else
        echo_warning "Virtual environment activation script not found"
    fi
else
    echo_error "Virtual environment not found: atlas_venv"
fi
echo ""

# 6. Файли конфігурації
echo_info "=== 📄 CONFIGURATION FILES ==="
config_files=("config.yaml" "requirements.txt" "start_atlas.sh" "stop_atlas.sh")

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo_success "$file - EXISTS"
    else
        echo_error "$file - MISSING"
    fi
done
echo ""

# 7. Логи
echo_info "=== 📝 LOG FILES ==="
if [ -d "logs" ]; then
    echo_success "Logs directory exists"
    log_count=$(find logs -name "*.log" | wc -l)
    echo "Log files found: $log_count"
    
    if [ -f "logs/atlas.log" ]; then
        echo "Recent log entries (last 5 lines):"
        tail -5 logs/atlas.log
    fi
else
    echo_warning "Logs directory not found"
fi
echo ""

# 8. Дискове простір
echo_info "=== 💾 DISK USAGE ==="
echo "Current directory size:"
du -sh . 2>/dev/null
echo "Available disk space:"
df -h . 2>/dev/null
echo ""

# 9. Мережеві з'єднання
echo_info "=== 🌐 NETWORK CONNECTIONS ==="
echo "Active connections on Atlas ports:"
netstat -an 2>/dev/null | grep -E "(8000|4006|9090|8080)" | grep LISTEN || echo "No active connections found"
echo ""

# 10. GitHub Runner статус
echo_info "=== 🚀 GITHUB ACTIONS RUNNER ==="
if launchctl list | grep -q "actions.runner"; then
    echo_success "GitHub Actions Runner is running"
    launchctl list | grep "actions.runner"
else
    echo_warning "GitHub Actions Runner not found"
fi
echo ""

# 11. Рекомендації
echo_info "=== 💡 RECOMMENDATIONS ==="
echo "• To start all services: ./start_atlas.sh"
echo "• To stop all services: ./stop_atlas.sh"
echo "• To check GitHub runner: ./manage_github_runner.sh status"
echo "• To run tests: python comprehensive_atlas_tool_tester.py"
echo "• To view logs: tail -f logs/atlas.log"
echo ""

echo_info "Diagnostic complete. Check above for any issues that need attention."
