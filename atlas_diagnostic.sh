#!/bin/bash

# Simple Atlas MCP System Diagnostic
# ==================================

echo "🤖 Atlas MCP System Diagnostic"
echo "=============================="

# Basic file check
echo ""
echo "📁 File Structure Check:"
for file in atlas_core.py mcp_automation_server.py mcp_macos_automator.py requirements.txt start_atlas.sh docker-compose.yml Dockerfile; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
    fi
done

# Python check
echo ""
echo "🐍 Python Environment:"
if command -v python3 >/dev/null 2>&1; then
    echo "✅ Python3: $(python3 --version)"
else
    echo "❌ Python3 not available"
fi

if [ -d "atlas_env" ]; then
    echo "✅ Virtual environment exists"
    if [ -f "atlas_env/.deps_installed" ]; then
        echo "✅ Dependencies marker found"
    else
        echo "⚠️  Dependencies may not be installed"
    fi
else
    echo "⚠️  Virtual environment not created"
fi

# Docker check
echo ""
echo "🐳 Docker Environment:"
if command -v docker >/dev/null 2>&1; then
    echo "✅ Docker available"
    if docker info >/dev/null 2>&1; then
        echo "✅ Docker daemon running"
    else
        echo "❌ Docker daemon not running"
    fi
else
    echo "❌ Docker not available"
fi

if command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then
    echo "✅ Docker Compose available"
    if docker compose config >/dev/null 2>&1; then
        echo "✅ Docker Compose config valid"
    else
        echo "❌ Docker Compose config invalid"
    fi
else
    echo "❌ Docker Compose not available"
fi

# Kubernetes check
echo ""
echo "☸️  Kubernetes Environment:"
if command -v kubectl >/dev/null 2>&1; then
    echo "✅ kubectl available"
    if [ -d "k8s" ]; then
        echo "✅ Kubernetes configs found"
    else
        echo "⚠️  Kubernetes configs not found"
    fi
else
    echo "⚠️  kubectl not available (optional)"
fi

# Port availability
echo ""
echo "🔌 Port Availability:"
for port in 8000 8080 4002 4003 4004 4005; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠️  Port $port in use"
    else
        echo "✅ Port $port available"
    fi
done

# Test basic Python syntax
echo ""
echo "🧪 Python Syntax Check:"
for file in atlas_core.py mcp_automation_server.py mcp_macos_automator.py; do
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "✅ $file syntax valid"
    else
        echo "❌ $file syntax error"
    fi
done

echo ""
echo "📊 Recommended next steps:"
echo ""

# Provide recommendations
if [ ! -d "atlas_env" ]; then
    echo "1. Create virtual environment: python3 -m venv atlas_env"
fi

if [ ! -f "atlas_env/.deps_installed" ]; then
    echo "2. Install dependencies: source atlas_env/bin/activate && pip install -r requirements.txt"
fi

if docker info >/dev/null 2>&1 && docker compose config >/dev/null 2>&1; then
    echo "3. Try Docker deployment: docker compose up -d"
fi

echo "4. Run full test suite: python test_automation_complete.py"
echo "5. Start Atlas: ./start_atlas.sh"

echo ""
echo "✨ Diagnostic complete!"