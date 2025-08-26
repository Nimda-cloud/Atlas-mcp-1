#!/bin/bash
"""
Simple Atlas System Startup
===========================
Starts all Atlas MCP services with basic functionality
"""

echo "🚀 Starting Atlas MCP System (Simple Mode)"
echo "=========================================="

# Function to check if port is free
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $port is already in use"
        return 1
    else
        echo "✅ Port $port is available"
        return 0
    fi
}

# Function to start service in background
start_service() {
    local script=$1
    local name=$2
    local port=$3
    
    echo "🔄 Starting $name on port $port..."
    
    if check_port $port; then
        nohup python3 $script > ${name}_server.log 2>&1 &
        echo $! > ${name}_server.pid
        sleep 2
        
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "✅ $name started successfully"
        else
            echo "❌ $name failed to start"
        fi
    fi
}

# Stop any existing services
echo "🧹 Cleaning up existing services..."
pkill -f "mock_atlas_core.py" 2>/dev/null || true
pkill -f "simple_task_orchestrator.py" 2>/dev/null || true  
pkill -f "simple_mcp_proxy.py" 2>/dev/null || true
sleep 1

# Start services
start_service "mock_atlas_core.py" "AtlasCore" 8000
start_service "simple_task_orchestrator.py" "TaskOrchestrator" 4006
start_service "mcp-proxy/simple_mcp_proxy.py" "MCPProxy" 9090

echo ""
echo "🎯 Atlas MCP System Status:"
echo "   💫 Atlas Core: http://localhost:8000"
echo "   🎯 Task Orchestrator: http://localhost:4006" 
echo "   🔗 MCP Proxy: http://localhost:9090"
echo ""
echo "📊 Test with: python3 comprehensive_atlas_tool_tester.py"
echo "🛑 Stop with: ./simple_stop_atlas.sh"
