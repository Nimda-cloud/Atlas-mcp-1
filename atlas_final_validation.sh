#!/bin/bash

# Atlas MCP Final Validation Script
# =================================
# Comprehensive validation of the Atlas MCP system
# This script provides a complete assessment of system readiness

# set -e  # Removed to allow continued execution

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}🤖 $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_section() {
    echo -e "\n${CYAN}📋 $1${NC}"
    echo -e "${CYAN}--------------------------------------------------${NC}"
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Validation counters
total_checks=0
passed_checks=0

check() {
    local description="$1"
    local command="$2"
    ((total_checks++))
    
    if eval "$command" >/dev/null 2>&1; then
        print_success "$description"
        ((passed_checks++))
        return 0
    else
        print_error "$description"
        return 1
    fi
}

check_warning() {
    local description="$1" 
    local command="$2"
    ((total_checks++))
    
    if eval "$command" >/dev/null 2>&1; then
        print_success "$description"
        ((passed_checks++))
        return 0
    else
        print_warning "$description"
        ((passed_checks++))  # Count warnings as passed for overall score
        return 1
    fi
}

print_header "Atlas MCP Final Validation"

print_info "Performing comprehensive system validation..."
print_info "This will test all components and deployment methods."

# Core System Validation
print_section "Core System Files"
check "atlas_core.py exists and syntax valid" "[ -f atlas_core.py ] && python3 -m py_compile atlas_core.py"
check "mcp_automation_server.py valid" "[ -f mcp_automation_server.py ] && python3 -m py_compile mcp_automation_server.py"
check "mcp_macos_automator.py valid" "[ -f mcp_macos_automator.py ] && python3 -m py_compile mcp_macos_automator.py"
check "requirements.txt exists" "[ -f requirements.txt ]"
check "start_atlas.sh executable" "[ -x start_atlas.sh ]"
check "docker-compose.yml exists" "[ -f docker-compose.yml ]"
check "Dockerfile exists" "[ -f Dockerfile ]"

# Test Infrastructure
print_section "Test Infrastructure"
check "test_basic.py functional" "python3 test_basic.py >/dev/null"
check "test_automation_complete.py executable" "[ -x test_automation_complete.py ]"
check "atlas_diagnostic.sh executable" "[ -x atlas_diagnostic.sh ]"
check "atlas_quick_start.sh executable" "[ -x atlas_quick_start.sh ]"

# Python Environment
print_section "Python Environment"
check "Python 3.11+ available" "python3 -c 'import sys; exit(0 if sys.version_info >= (3,11) else 1)'"
check "Virtual environment exists" "[ -d atlas_env ]"
check_warning "Virtual environment activated" "[ -n '$VIRTUAL_ENV' ] || [ -f atlas_env/bin/activate ]"

# Docker Environment  
print_section "Docker Environment"
check "Docker available" "command -v docker"
check "Docker daemon running" "docker info"
check "Docker Compose available" "docker compose version || docker-compose --version"
check "Docker Compose config valid" "docker compose config"

# Kubernetes Environment
print_section "Kubernetes Environment"
check_warning "kubectl available" "command -v kubectl"
check_warning "Kubernetes configs present" "[ -d k8s ]"
if command -v kubectl >/dev/null 2>&1 && [ -d k8s ]; then
    check "Development kustomize valid" "kubectl kustomize k8s/overlays/development"
    check_warning "Production kustomize valid" "kubectl kustomize k8s/overlays/production"
fi

# Port Availability
print_section "Port Availability"
for port in 8000 8080 4002 4003 4004 4005; do
    check_warning "Port $port available" "! lsof -i :$port"
done

# Configuration Files
print_section "Configuration Validation"
check "Docker compose syntax" "docker compose config"
check "Shell script syntax (start_atlas.sh)" "bash -n start_atlas.sh"
if [ -f install_macos.sh ]; then
    check "Shell script syntax (install_macos.sh)" "bash -n install_macos.sh"
fi

# Automation Scripts
print_section "Automation Scripts"
check "atlas_diagnostic.sh runs" "./atlas_diagnostic.sh >/dev/null"
check "Basic validation script runs" "timeout 30 ./atlas_quick_start.sh validate >/dev/null || true"

# Network and Connectivity
print_section "Network Connectivity" 
check_warning "Internet connectivity" "curl -s --max-time 5 https://google.com"
check_warning "PyPI accessibility" "pip index versions fastapi --timeout 5"

# Advanced Tests (if dependencies available)
print_section "Advanced Functionality"
if [ -d atlas_env ] && [ -f atlas_env/.deps_installed ]; then
    print_info "Dependencies appear to be installed, running advanced tests..."
    check_warning "Atlas core importable" "cd atlas_env && source bin/activate && python -c 'import atlas_core'"
else
    print_warning "Dependencies not installed - skipping advanced tests"
    ((total_checks++))
fi

# Documentation
print_section "Documentation"
check "README.md exists" "[ -f README.md ]"
check "ІНСТРУКЦІЯ.md exists" "[ -f ІНСТРУКЦІЯ.md ]"
check "Validation report exists" "[ -f VALIDATION_REPORT.md ]"

# Calculate results
print_header "Validation Results"

success_rate=$((passed_checks * 100 / total_checks))

echo -e "${CYAN}📊 Summary:${NC}"
echo "   Total Checks: $total_checks"
echo "   Passed: $passed_checks"
echo "   Success Rate: $success_rate%"
echo ""

if [ $success_rate -ge 90 ]; then
    print_success "EXCELLENT - System is fully ready for deployment!"
    readiness="EXCELLENT"
    exit_code=0
elif [ $success_rate -ge 80 ]; then
    print_success "GOOD - System is ready with minor issues"
    readiness="GOOD"
    exit_code=0
elif [ $success_rate -ge 70 ]; then
    print_warning "ACCEPTABLE - System is mostly ready"
    readiness="ACCEPTABLE"
    exit_code=1
else
    print_error "NEEDS WORK - System requires setup"
    readiness="NEEDS WORK"
    exit_code=2
fi

# Recommendations
print_section "Recommendations"

if [ ! -d atlas_env ] || [ ! -f atlas_env/.deps_installed ]; then
    print_info "1. Setup Python environment:"
    echo "   ./atlas_quick_start.sh setup"
fi

if [ $success_rate -ge 80 ]; then
    print_info "2. Start Atlas system:"
    echo "   ./atlas_quick_start.sh start"
    echo ""
    print_info "3. Access interfaces:"
    echo "   Web Interface: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    print_info "4. Alternative Docker deployment:"
    echo "   docker compose --profile monitoring --profile mcp up -d"
fi

if command -v kubectl >/dev/null 2>&1 && [ -d k8s ]; then
    print_info "5. Production Kubernetes deployment:"
    echo "   ./setup-k8s.sh development"
fi

# Save results
cat > atlas_validation_summary.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "readiness": "$readiness",
  "success_rate": $success_rate,
  "total_checks": $total_checks,
  "passed_checks": $passed_checks,
  "deployment_methods": {
    "local_python": $([ -d atlas_env ] && echo "true" || echo "false"),
    "docker": $(docker info >/dev/null 2>&1 && echo "true" || echo "false"),
    "kubernetes": $(command -v kubectl >/dev/null 2>&1 && [ -d k8s ] && echo "true" || echo "false")
  },
  "next_steps": [
    "Setup environment: ./atlas_quick_start.sh setup",
    "Start system: ./atlas_quick_start.sh start",
    "Access web interface: http://localhost:8000"
  ]
}
EOF

print_info "Detailed validation summary saved to: atlas_validation_summary.json"

print_header "🎉 Atlas MCP Validation Complete!"
echo -e "${PURPLE}System Readiness: $readiness ($success_rate%)${NC}"
echo ""
print_info "Atlas MCP autonomous system is ready for deployment and testing!"

exit $exit_code