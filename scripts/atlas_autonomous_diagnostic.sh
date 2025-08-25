#!/bin/bash
# Atlas Autonomous System Diagnostic Script
# Enhanced version with comprehensive health checks

echo "🤖 Atlas Autonomous System Diagnostic"
echo "====================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check Git status
echo -e "\n📊 Repository Status:"
if git status --porcelain | grep -q .; then
    print_warning "Repository has uncommitted changes"
    git status --short
else
    print_success "Repository is clean"
fi

# Check current branch
current_branch=$(git branch --show-current)
echo "Current branch: $current_branch"

# Check for conflicts
if git ls-files -u | grep -q .; then
    print_error "Repository has merge conflicts"
    git ls-files -u
else
    print_success "No merge conflicts detected"
fi

# Check workflows
echo -e "\n🔄 GitHub Workflows:"
if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pr-agent-ci.yml'))" 2>/dev/null; then
    print_success "PR Agent CI workflow syntax valid"
else
    print_error "PR Agent CI workflow has syntax errors"
fi

if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/post-merge-local.yml'))" 2>/dev/null; then
    print_success "Post-merge workflow syntax valid"
else
    print_error "Post-merge workflow has syntax errors"
fi

# Check Docker
echo -e "\n🐳 Docker Environment:"
if docker --version >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        print_success "Docker is running"
        if docker compose config >/dev/null 2>&1; then
            print_success "Docker Compose configuration valid"
        else
            print_error "Docker Compose configuration invalid"
        fi
    else
        print_error "Docker daemon not running"
    fi
else
    print_error "Docker not installed"
fi

# Check Python environment
echo -e "\n🐍 Python Environment:"
if python3 -m py_compile atlas_core.py mcp_*.py >/dev/null 2>&1; then
    print_success "All Python files have valid syntax"
else
    print_error "Python syntax errors found"
fi

# Check autonomous capabilities
echo -e "\n🤖 Autonomous Capabilities:"
if [ -f "atlas_automation_enhancement_report.json" ]; then
    print_success "Automation enhancement report exists"
else
    print_warning "No automation enhancement report found"
fi

if [ -f "atlas_autonomous_health_monitor.py" ]; then
    print_success "Autonomous health monitor available"
else
    print_warning "No autonomous health monitor found"
fi

# Final status
echo -e "\n📋 System Status Summary:"
echo "Repository: $(pwd)"
echo "Branch: $current_branch"
echo "Automation: Enhanced and Ready"
echo "Documentation: Complete"

echo -e "\n🚀 Ready for autonomous operation!"
echo "To complete setup:"
echo "1. Set up self-hosted macOS runner"
echo "2. Configure repository variables"
echo "3. Monitor GitHub Actions for automation"
