#!/bin/bash

# Atlas Quick Diagnostic Script
# Fast validation of system readiness for autonomous operation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[CHECK]${NC} $1"; }
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }

# Quick checks
check_files() {
    local files=(
        "atlas_core.py:Atlas core module"
        "mcp_automation_server.py:MCP automation server"
        "mcp_macos_automator.py:macOS automator"
        "requirements.txt:Python dependencies"
        "docker-compose.yml:Docker configuration"
        "start_atlas.sh:Startup script"
        ".github/workflows/pr-agent-ci.yml:PR CI workflow"
        ".github/workflows/post-merge-local.yml:Post-merge workflow"
    )
    
    echo "📁 File Structure:"
    for item in "${files[@]}"; do
        local file="${item%:*}"
        local desc="${item#*:}"
        if [ -f "$file" ]; then
            print_success "$desc ($file)"
        else
            print_error "$desc missing ($file)"
            return 1
        fi
    done
}

check_syntax() {
    echo -e "\n🐍 Python Syntax:"
    if python3 -m py_compile atlas_core.py mcp_*.py >/dev/null 2>&1; then
        print_success "All Python files have valid syntax"
    else
        print_error "Python syntax errors found"
        return 1
    fi
}

check_docker() {
    echo -e "\n🐳 Docker Environment:"
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            print_success "Docker running"
        else
            print_warning "Docker installed but not running"
        fi
        
        if docker compose config >/dev/null 2>&1; then
            print_success "Docker Compose configuration valid"
        else
            print_error "Docker Compose configuration invalid"
            return 1
        fi
    else
        print_warning "Docker not installed"
    fi
}

check_kubernetes() {
    echo -e "\n☸️  Kubernetes Environment:"
    if command -v kubectl >/dev/null 2>&1; then
        print_success "kubectl available"
        if [ -d "k8s" ]; then
            if kubectl kustomize k8s/overlays/development >/dev/null 2>&1; then
                print_success "Kubernetes manifests valid"
            else
                print_warning "Kubernetes manifests have issues"
            fi
        else
            print_warning "k8s directory not found"
        fi
    else
        print_warning "kubectl not available (optional)"
    fi
}

check_ports() {
    echo -e "\n🔌 Port Availability:"
    local ports=(8000 8080 4002 4003 4004 4005)
    local available=0
    
    for port in "${ports[@]}"; do
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            available=$((available + 1))
        fi
    done
    
    if [ $available -eq ${#ports[@]} ]; then
        print_success "All required ports (${ports[*]}) available"
    else
        print_warning "$available/${#ports[@]} ports available"
    fi
}

check_github_workflows() {
    echo -e "\n🔄 GitHub Workflows:"
    
    # Check PR Agent CI workflow
    if python3 -c "
try:
    import yaml
    with open('.github/workflows/pr-agent-ci.yml', 'r') as f:
        yaml.safe_load(f)
    print('valid')
except ImportError:
    # YAML module not available, basic validation
    with open('.github/workflows/pr-agent-ci.yml', 'r') as f:
        content = f.read()
    if content.strip() and 'name:' in content and 'jobs:' in content:
        print('valid')
    else:
        print('invalid')
except Exception:
    print('invalid')
" 2>/dev/null | grep -q "valid"; then
        print_success "PR Agent CI workflow valid"
    else
        print_error "PR Agent CI workflow invalid"
        return 1
    fi
    
    # Check Post-merge workflow
    if python3 -c "
try:
    import yaml
    with open('.github/workflows/post-merge-local.yml', 'r') as f:
        yaml.safe_load(f)
    print('valid')
except ImportError:
    # YAML module not available, basic validation
    with open('.github/workflows/post-merge-local.yml', 'r') as f:
        content = f.read()
    if content.strip() and 'name:' in content and 'jobs:' in content:
        print('valid')
    else:
        print('invalid')
except Exception:
    print('invalid')
" 2>/dev/null | grep -q "valid"; then
        print_success "Post-merge workflow valid"
    else
        print_error "Post-merge workflow invalid"
        return 1
    fi
}

# Main diagnostic
main() {
    echo "🤖 Atlas Quick Diagnostic"
    echo "========================="
    
    local checks_passed=0
    local total_checks=6
    
    # Run all checks
    check_files && checks_passed=$((checks_passed + 1))
    check_syntax && checks_passed=$((checks_passed + 1))
    check_docker && checks_passed=$((checks_passed + 1))
    check_kubernetes && checks_passed=$((checks_passed + 1))
    check_ports && checks_passed=$((checks_passed + 1))
    check_github_workflows && checks_passed=$((checks_passed + 1))
    
    echo -e "\n📊 Summary:"
    echo "Checks passed: $checks_passed/$total_checks"
    
    if [ $checks_passed -eq $total_checks ]; then
        print_success "System ready for autonomous operation!"
        echo -e "\n🚀 Next steps:"
        echo "  ./atlas_autonomous_setup.sh    # Full setup"
        echo "  ./start_atlas.sh --local       # Start locally"
        echo "  docker compose up -d            # Start with Docker"
        return 0
    else
        print_warning "Some checks failed - see details above"
        echo -e "\n🔧 Run atlas_autonomous_setup.sh for detailed setup"
        return 1
    fi
}

# Change to script directory
cd "$(dirname "$0")"

# Run diagnostic
main "$@"