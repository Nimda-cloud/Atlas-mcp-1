#!/bin/bash
echo "🛑 Stopping Atlas MCP System..."

# Stop services
pkill -f "mock_atlas_core.py" 2>/dev/null || true
pkill -f "simple_task_orchestrator.py" 2>/dev/null || true
pkill -f "simple_mcp_proxy.py" 2>/dev/null || true

# Clean up PID files
rm -f *_server.pid 2>/dev/null || true

echo "✅ Atlas MCP System stopped"
