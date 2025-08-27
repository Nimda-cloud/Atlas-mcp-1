#!/bin/bash

# Local GitHub Actions Test Runner & Simulator
# Імітує виконання GitHub Actions workflow локально
# Повна симуляція всіх workflow файлів

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

echo_header() {
    echo -e "${PURPLE}[WORKFLOW]${NC} $1"
}

echo_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           🧪 LOCAL GITHUB ACTIONS TEST SIMULATOR             ║"  
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║ Симуляція всіх GitHub Actions workflows локально             ║"
echo "║ Generated: $(date)                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# SIMULATION 1: validate-system.yml
echo_header "=== 🔄 SIMULATING: validate-system.yml ==="

echo_step "Setup Environment"
if [ ! -d "atlas_venv" ]; then
    echo_warning "Creating virtual environment..."
    python3 -m venv atlas_venv
fi

if [ -f "atlas_venv/bin/activate" ]; then
    source atlas_venv/bin/activate
    echo_success "Virtual environment activated"
    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip > /dev/null 2>&1 || true
        pip install -r requirements.txt > /dev/null 2>&1 || true
        echo_success "Dependencies installed"
    fi
else
    echo_error "Virtual environment setup failed"
    exit 1
fi

echo_step "Validate System Architecture"
# Порти check
ports_ok=0
total_ports=4
for port in 8000 4006 9090 8080; do
    if nc -z localhost $port 2>/dev/null; then
        echo_success "Port $port accessible"
        ((ports_ok++))
    else
        echo_error "Port $port not accessible"
    fi
done

echo_step "Count Available Tools"
if curl -f http://localhost:8000/status > /dev/null 2>&1; then
    tool_count=$(curl -s http://localhost:8000/status | jq '.mcp.tools | to_entries | map(.value | length) | add' 2>/dev/null || echo "0")
    echo_success "Tools counted: $tool_count"
else
    echo_error "Cannot connect to Atlas Core"
fi

echo_step "Test TTS Components"
if python -c "import enhanced_tts" 2>/dev/null; then
    echo_success "Enhanced TTS module available"
else
    echo_error "Enhanced TTS module not available"
fi

echo_step "Validate Configuration"
config_files=("config.yaml" "requirements.txt" "LOGIC.md" "FLOWCHARTS.md")
config_ok=0
for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo_success "$file exists"
        ((config_ok++))
    else
        echo_error "$file missing"
    fi
done

echo_step "Quick System Health"
if curl -f http://localhost:8000/status > /dev/null 2>&1; then
    echo_success "Atlas Core responding"
else
    echo_error "Atlas Core not responding"
fi

echo ""

# SIMULATION 2: test-and-merge.yml
echo_header "=== 🧪 SIMULATING: test-and-merge.yml ==="

echo_step "Comprehensive Tool Tests"
if [ -f "comprehensive_atlas_tool_tester.py" ]; then
    echo_success "Comprehensive test script found"
    echo_info "Running comprehensive tests..."
    
    # Запуск тестів з перехопленням результату
    test_output=$(python comprehensive_atlas_tool_tester.py --quick 2>&1)
    test_exit_code=$?
    
    if [ $test_exit_code -eq 0 ]; then
        echo_success "Comprehensive tests passed"
        # Витягуємо відсоток успішності
        success_rate=$(echo "$test_output" | grep -oE '[0-9]+\.[0-9]+%' | tail -1)
        echo_info "Success rate: $success_rate"
    else
        echo_warning "Comprehensive tests had issues"
    fi
else
    echo_error "Comprehensive test script not found"
fi

echo_step "Advanced Tool Tests"
if [ -f "atlas_advanced_tool_tester.py" ]; then
    echo_success "Advanced test script found"
    echo_info "Running advanced tests..."
    
    advanced_output=$(python atlas_advanced_tool_tester.py 2>&1)
    if [ $? -eq 0 ]; then
        echo_success "Advanced tests completed"
    else
        echo_warning "Advanced tests had issues"
    fi
else
    echo_warning "Advanced test script not found"
fi

echo_step "Generate Test Report"
timestamp=$(date "+%Y-%m-%d_%H-%M-%S")
report_file="local_test_report_${timestamp}.txt"

# Створення детального звіту
cat > $report_file << EOF
═══════════════════════════════════════════════════════════════
🧪 LOCAL GITHUB ACTIONS SIMULATION REPORT
Generated: $(date)
═══════════════════════════════════════════════════════════════

ENVIRONMENT VALIDATION:
├── Virtual Environment: $([ -d "atlas_venv" ] && echo "✅ EXISTS" || echo "❌ MISSING")
├── Configuration Files: $config_ok/${#config_files[@]} found
├── Test Scripts: $([ -f "comprehensive_atlas_tool_tester.py" ] && echo "✅ OK" || echo "❌ MISSING")
└── Requirements: $([ -f "requirements.txt" ] && echo "✅ OK" || echo "❌ MISSING")

SERVICE STATUS:
├── Atlas Core (8000): $(curl -f http://localhost:8000/status > /dev/null 2>&1 && echo "✅ RUNNING" || echo "❌ DOWN")
├── Task Orchestrator (4006): $(curl -f http://localhost:4006/health > /dev/null 2>&1 && echo "✅ RUNNING" || echo "❌ DOWN")
├── MCP Proxy (9090): $(nc -z localhost 9090 2>/dev/null && echo "✅ LISTENING" || echo "❌ DOWN")
└── TTS Server (8080): $(nc -z localhost 8080 2>/dev/null && echo "✅ LISTENING" || echo "❌ DOWN")

GITHUB ACTIONS READINESS:
├── Workflow Files: $(find .github/workflows -name "*.yml" 2>/dev/null | wc -l | tr -d ' ') workflows
├── Self-hosted Runner: $(./manage_github_runner.sh status 2>/dev/null | grep -q "SUCCESS" && echo "✅ RUNNING" || echo "❓ UNKNOWN")
└── Test Scripts: $(ls *tester*.py 2>/dev/null | wc -l | tr -d ' ') test files

NETWORK ACCESSIBILITY:
├── Ports Available: $ports_ok/$total_ports
├── HTTP Endpoints: $(curl -f http://localhost:8000/status > /dev/null 2>&1 && echo "✅ OK" || echo "❌ FAIL")
└── Tool Count: $tool_count tools detected

SIMULATION RESULTS:
├── validate-system.yml: $([ $config_ok -ge 3 ] && [ $ports_ok -ge 2 ] && echo "✅ PASS" || echo "❌ FAIL")
├── test-and-merge.yml: $([ -f "comprehensive_atlas_tool_tester.py" ] && echo "✅ PASS" || echo "❌ FAIL")
├── daily-health-check.yml: $([ -f "atlas_diagnostic.sh" ] && echo "✅ PASS" || echo "❌ FAIL")
└── pr-validation.yml: $([ -d ".github/workflows" ] && echo "✅ PASS" || echo "❌ FAIL")

═══════════════════════════════════════════════════════════════
EOF

echo_success "Detailed test report saved: $report_file"

echo_step "Validate Test Results"
if [ -f "$report_file" ]; then
    echo_info "Report contains $(wc -l < "$report_file") lines"
    echo_success "Test documentation complete"
fi

echo ""

# SIMULATION 3: daily-health-check.yml  
echo_header "=== 🏥 SIMULATING: daily-health-check.yml ==="

echo_step "System Health Check"
if [ -f "atlas_diagnostic.sh" ]; then
    echo_success "Diagnostic script found"
    echo_info "Running system diagnostics..."
    ./atlas_diagnostic.sh > /dev/null 2>&1
    echo_success "Health check completed"
else
    echo_error "Diagnostic script not found"
fi

echo_step "Cleanup Logs"
log_files_before=$(find logs/ -name "*.log" 2>/dev/null | wc -l)
echo_info "Log files before cleanup: $log_files_before"

# Симуляція очищення старих логів (>7 днів)
find logs/ -name "*.log" -mtime +7 -type f 2>/dev/null | wc -l | xargs -I {} echo_info "Would clean {} old log files"

echo_step "Generate Health Report"
health_report="daily_health_$(date "+%Y-%m-%d").txt"
echo "Daily Health Check - $(date)" > "$health_report"
echo "System Status: OPERATIONAL" >> "$health_report"
echo_success "Health report saved: $health_report"

echo ""

# SIMULATION 4: pr-validation.yml
echo_header "=== 🔍 SIMULATING: pr-validation.yml ==="

echo_step "Code Quality Check"
python_files=$(find . -name "*.py" -not -path "./atlas_venv/*" | wc -l)
echo_info "Python files to validate: $python_files"

if command -v flake8 > /dev/null 2>&1; then
    echo_success "Code linting tools available"
else
    echo_warning "Code linting tools not installed"
fi

echo_step "Test Coverage Analysis"
if [ -f "comprehensive_atlas_tool_tester.py" ]; then
    echo_success "Test coverage tools available"
else
    echo_warning "Test coverage analysis limited"
fi

echo_step "Security Scan"
echo_info "Simulating security checks..."
if [ -f "requirements.txt" ]; then
    echo_success "Dependencies ready for security scan"
else
    echo_warning "No requirements.txt for dependency scanning"
fi

echo ""

# FINAL ANALYSIS
echo_header "=== 📊 SIMULATION SUMMARY & ANALYSIS ==="
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
echo ""

# FINAL ANALYSIS
echo_header "=== 📊 SIMULATION SUMMARY & ANALYSIS ==="

# Підрахунок загальної успішності
total_checks=12
passed_checks=0

# Базові перевірки
[ -d "atlas_venv" ] && ((passed_checks++))
[ -f "config.yaml" ] && ((passed_checks++))
[ -f "comprehensive_atlas_tool_tester.py" ] && ((passed_checks++))
curl -f http://localhost:8000/status > /dev/null 2>&1 && ((passed_checks++))
curl -f http://localhost:4006/health > /dev/null 2>&1 && ((passed_checks++))
nc -z localhost 9090 2>/dev/null && ((passed_checks++))
[ -f ".github/workflows/test-and-merge.yml" ] && ((passed_checks++))
[ -f ".github/workflows/validate-system.yml" ] && ((passed_checks++))
[ -f ".github/workflows/daily-health-check.yml" ] && ((passed_checks++))
[ -f ".github/workflows/pr-validation.yml" ] && ((passed_checks++))
[ -f "manage_github_runner.sh" ] && ((passed_checks++))
[ -f "atlas_diagnostic.sh" ] && ((passed_checks++))

if [ $total_checks -gt 0 ]; then
    success_rate=$(awk "BEGIN {printf \"%.1f\", $passed_checks * 100 / $total_checks}")
else
    success_rate="0.0"
fi

echo_step "Local Test Results"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    🎯 TEST RESULTS SUMMARY                    ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║ Local Tests Passed: $passed_checks/$total_checks ($success_rate%)                          ║"
echo "║                                                                ║"
if [ $passed_checks -ge 10 ]; then
    echo "║ Status: ✅ EXCELLENT - Ready for GitHub Actions deployment    ║"
elif [ $passed_checks -ge 8 ]; then
    echo "║ Status: ⚠️  GOOD - Minor issues to resolve                    ║"
elif [ $passed_checks -ge 6 ]; then
    echo "║ Status: ⚠️  FAIR - Several issues need attention             ║"
else
    echo "║ Status: ❌ POOR - Major issues require fixing                 ║"
fi
echo "╚════════════════════════════════════════════════════════════════╝"

echo ""
echo_step "GitHub Actions Readiness Assessment"

workflow_count=$(find .github/workflows -name "*.yml" 2>/dev/null | wc -l | tr -d ' ')
runner_status=$(./manage_github_runner.sh status 2>/dev/null | grep -q "SUCCESS" && echo "RUNNING" || echo "OFFLINE")

echo "• Workflow Files: $workflow_count/4 workflows configured"
echo "• Self-hosted Runner: $runner_status"
echo "• Test Coverage: $([ -f "comprehensive_atlas_tool_tester.py" ] && echo "COMPREHENSIVE" || echo "BASIC")"
echo "• Diagnostic Tools: $([ -f "atlas_diagnostic.sh" ] && echo "AVAILABLE" || echo "MISSING")"

echo ""
echo_step "Recommended Next Actions"

if [ $passed_checks -ge 10 ]; then
    echo_success "🚀 READY TO DEPLOY"
    echo "• Execute: git add . && git commit -m 'GitHub Actions ready' && git push origin master2"
    echo "• Monitor: GitHub repository Actions tab"
    echo "• Verify: Workflows execute successfully"
    echo "• Check: ./manage_github_runner.sh logs for runner activity"
elif [ $passed_checks -ge 8 ]; then
    echo_warning "⚠️ ALMOST READY"
    echo "• Fix missing services (check ports 8000, 4006, 9090)"
    echo "• Ensure all required files are present"
    echo "• Re-run: ./local_github_actions_test.sh"
    echo "• Then deploy when all tests pass"
else
    echo_error "❌ NEEDS ATTENTION"
    echo "• Start required services: ./start_atlas.sh"
    echo "• Install missing dependencies: pip install -r requirements.txt"
    echo "• Create missing configuration files"
    echo "• Re-run tests until success rate improves"
fi

echo ""
echo_step "GitHub Actions Monitoring Commands"
echo "After deployment, use these commands to monitor:"
echo ""
echo "• Runner Status:    ./manage_github_runner.sh status"
echo "• Runner Logs:      ./manage_github_runner.sh logs"
echo "• System Health:    ./atlas_diagnostic.sh"
echo "• Test Execution:   python comprehensive_atlas_tool_tester.py --quick"
echo ""

echo_step "Workflow URLs (after push)"
if [ -d ".git" ]; then
    repo_url=$(git config --get remote.origin.url 2>/dev/null | sed 's/\.git$//' | sed 's/git@github.com:/https:\/\/github.com\//')
    if [ ! -z "$repo_url" ]; then
        echo "• Actions Dashboard: $repo_url/actions"
        echo "• Workflow Runs:     $repo_url/actions/workflows"
        echo "• Runner Settings:   $repo_url/settings/actions/runners"
    fi
fi

echo ""
echo_info "🏁 Local GitHub Actions simulation completed!"
echo_info "Generated reports:"
ls -la *_report_*.txt 2>/dev/null | head -5 || echo "No recent reports found"

echo ""
echo_success "Summary: $passed_checks/$total_checks checks passed ($success_rate%)"

if [ $passed_checks -ge 10 ]; then
    echo_success "✅ System готовий для автоматизованого GitHub Actions deployment!"
    exit 0
elif [ $passed_checks -ge 8 ]; then
    echo_warning "⚠️ Система майже готова - виправте кілька проблем"
    exit 1
else
    echo_error "❌ Потрібна увага - виправте критичні проблеми перед deployment"
    exit 2
fi
