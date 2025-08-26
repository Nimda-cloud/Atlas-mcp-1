#!/bin/bash

# Local GitHub Actions Test Runner
# Імітує виконання GitHub Actions workflow локально

set -e

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

echo "🚀 Local GitHub Actions Test Runner"
echo "=================================="
echo ""

# Крок 1: Setup Environment
echo_info "Setting up environment..."
if [ ! -d "atlas_venv" ]; then
    python3 -m venv atlas_venv
fi
source atlas_venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo_success "Environment ready"

# Крок 2: Validate System Architecture
echo_info "Validating system architecture..."

# Atlas Core (8000)
if curl -f http://localhost:8000/status > /dev/null 2>&1; then
    echo_success "Atlas Core (8000) - працює"
else 
    echo_warning "Atlas Core (8000) - недоступний"
fi

# Task Orchestrator (4006)
if curl -f http://localhost:4006/health > /dev/null 2>&1; then
    echo_success "Task Orchestrator (4006) - працює"
else
    echo_warning "Task Orchestrator (4006) - недоступний"  
fi

# MCP Proxy (9090)
if curl -f http://localhost:9090/health > /dev/null 2>&1; then
    echo_success "MCP Proxy (9090) - працює"
else
    echo_warning "MCP Proxy (9090) - недоступний"
fi

# Крок 3: Count Available Tools
echo_info "Counting available tools..."

if curl -f http://localhost:8000/status > /dev/null 2>&1; then
    total_tools=$(curl -s http://localhost:8000/status | jq '.mcp.tools | to_entries | map(.value | length) | add' 2>/dev/null || echo "0")
    echo_success "Total tools available: $total_tools"
    
    echo ""
    echo "Tools by category:"
    curl -s http://localhost:8000/status | jq -r '.mcp.tools | to_entries[] | "  ✅ \(.key): \(.value | length) tools"' 2>/dev/null || echo "  ❌ Could not get detailed statistics"
else
    echo_error "Atlas Core unavailable for tool counting"
fi

# Крок 4: Test TTS Components  
echo_info "Testing TTS components..."

# Enhanced TTS
if python -c "import enhanced_tts" 2>/dev/null; then
    echo_success "Enhanced TTS module available"
else
    echo_warning "Enhanced TTS module unavailable"
fi

# System say
if command -v say >/dev/null 2>&1; then
    echo_success "macOS system say available"
else
    echo_warning "macOS system say unavailable"
fi

# Pygame
if python -c "import pygame" 2>/dev/null; then
    echo_success "Pygame available"  
else
    echo_warning "Pygame unavailable"
fi

# Крок 5: Validate Configuration
echo_info "Validating configuration..."

# config.yaml
if [ -f "config.yaml" ]; then
    echo_success "config.yaml exists"
    if python -c "import yaml; yaml.safe_load(open('config.yaml'))" 2>/dev/null; then
        echo_success "config.yaml is valid"
    else
        echo_warning "config.yaml has issues"
    fi
else
    echo_warning "config.yaml missing"
fi

# requirements.txt
if [ -f "requirements.txt" ]; then
    deps_count=$(wc -l < requirements.txt)
    echo_success "requirements.txt exists ($deps_count dependencies)"
else
    echo_warning "requirements.txt missing"
fi

# Documentation
if [ -f "LOGIC.md" ]; then
    echo_success "LOGIC.md exists"
else
    echo_warning "LOGIC.md missing"
fi

if [ -f "FLOWCHARTS.md" ]; then
    echo_success "FLOWCHARTS.md exists"
else
    echo_warning "FLOWCHARTS.md missing"
fi

# Крок 6: Quick System Test
echo_info "Running quick system test..."

if curl -f http://localhost:8000/status > /dev/null 2>&1; then
    echo_info "Sending test request..."
    
    response=$(curl -s -X POST http://localhost:8000/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "Тест системи", "voice": "test"}' \
        --max-time 10 2>/dev/null || echo "TIMEOUT")
    
    if [ "$response" != "TIMEOUT" ] && [ "$response" != "" ]; then
        echo_success "Test request processed"
    else
        echo_warning "Test request failed or timeout"
    fi
else
    echo_warning "Atlas Core unavailable for testing"
fi

# Крок 7: Run Comprehensive Tests
echo_info "Running comprehensive tool tests..."

if [ -f "comprehensive_atlas_tool_tester.py" ]; then
    echo_info "Running comprehensive_atlas_tool_tester.py..."
    python comprehensive_atlas_tool_tester.py --quiet || echo_warning "Some tests failed"
else
    echo_warning "comprehensive_atlas_tool_tester.py not found"
fi

# Крок 8: Generate Report
echo_info "Generating report..."
timestamp=$(date "+%Y-%m-%d_%H-%M-%S")
report_file="local_test_report_${timestamp}.txt"

cat > "$report_file" << EOF
Local GitHub Actions Test Report
===============================
Generated: $(date)
Hostname: $(hostname)
Branch: $(git branch --show-current)
Commit: $(git rev-parse --short HEAD)

System Status:
EOF

if curl -f http://localhost:8000/status > /dev/null 2>&1; then
    curl -s http://localhost:8000/status >> "$report_file" 2>/dev/null || echo "Status unavailable" >> "$report_file"
else
    echo "Atlas Core unavailable" >> "$report_file"
fi

echo_success "Report saved: $report_file"

echo ""
echo "🎉 Local test execution completed!"
echo "📄 Check the report: $report_file"
echo ""
echo "Next steps:"
echo "  1. Address any warnings above"
echo "  2. Run './manage_github_runner.sh status' to check runner"
echo "  3. Push changes to trigger actual GitHub Actions"
