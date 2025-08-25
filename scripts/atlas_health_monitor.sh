#!/bin/bash

# Atlas Health Monitor
# Continuously monitors Atlas services and reports status

check_service() {
    local name=$1
    local url=$2
    local timeout=${3:-5}
    
    if timeout $timeout curl -fsS "$url" >/dev/null 2>&1; then
        echo "✅ $name: OK"
        return 0
    else
        echo "❌ $name: FAILED"
        return 1
    fi
}

echo "🏥 Atlas Health Monitor"
echo "====================="

# Check core services
check_service "Atlas Core" "http://localhost:8000/status"
check_service "Frontend" "http://localhost:8080/health"
check_service "MCP Automation" "http://localhost:4002/health"
check_service "MCP Automator" "http://localhost:4003/health"
check_service "TTS Service" "http://localhost:4004/health"
check_service "Playwright MCP" "http://localhost:4005/mcp"

echo ""
echo "🔍 System Status:"
echo "  Atlas Core API: http://localhost:8000/docs"
echo "  Web Interface: http://localhost:8000"
echo "  3D Frontend: http://localhost:8080"