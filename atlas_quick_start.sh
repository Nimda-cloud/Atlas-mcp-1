#!/bin/bash

# Atlas MCP Quick Validation & Start Script
# ==========================================
# Універсальний скрипт для перевірки та запуску Atlas MCP системи
# Автоматично визначає найкращий метод розгортання та перевіряє готовність

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "============================================================"
    echo "🤖 $1"
    echo "============================================================"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${CYAN}📋 $1${NC}"
    echo -e "${CYAN}--------------------------------------------------${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    return 1
}

# Comprehensive system validation
validate_system() {
    print_section "System Validation"
    
    local validation_score=0
    local max_score=10
    
    # Check basic files
    if [ -f "atlas_core.py" ] && [ -f "mcp_automation_server.py" ] && [ -f "requirements.txt" ]; then
        print_success "Core files present"
        ((validation_score++))
    else
        print_error "Missing core files"
    fi
    
    # Check start script
    if [ -f "start_atlas.sh" ] && [ -x "start_atlas.sh" ]; then
        print_success "Start script ready"
        ((validation_score++))
    else
        print_warning "Start script issues"
    fi
    
    # Check Python
    if command_exists python3; then
        python_version=$(python3 --version | sed 's/Python //')
        print_success "Python available: $python_version"
        ((validation_score++))
        
        # Check virtual environment
        if [ -d "atlas_env" ]; then
            print_success "Virtual environment exists"
            ((validation_score++))
            
            # Check if dependencies installed
            if [ -f "atlas_env/.deps_installed" ]; then
                print_success "Dependencies likely installed"
                ((validation_score++))
            else
                print_warning "Dependencies may not be installed"
            fi
        else
            print_warning "Virtual environment not created"
        fi
    else
        print_error "Python3 not available"
    fi
    
    # Check Docker
    if command_exists docker; then
        if docker info >/dev/null 2>&1; then
            print_success "Docker available and running"
            ((validation_score++))
            
            # Check Docker Compose
            if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
                print_success "Docker Compose available"
                ((validation_score++))
                
                # Test compose config
                if docker compose config >/dev/null 2>&1; then
                    print_success "Docker Compose config valid"
                    ((validation_score++))
                else
                    print_warning "Docker Compose config issues"
                fi
            else
                print_warning "Docker Compose not available"
            fi
        else
            print_warning "Docker not running"
        fi
    else
        print_warning "Docker not available"
    fi
    
    # Check Kubernetes
    if command_exists kubectl; then
        print_success "kubectl available"
        ((validation_score++))
        
        if [ -d "k8s" ]; then
            print_success "Kubernetes configs present"
            ((validation_score++))
        else
            print_warning "Kubernetes configs not found"
        fi
    else
        print_info "kubectl not available (optional)"
    fi
    
    # Calculate readiness
    local readiness_percent=$((validation_score * 100 / max_score))
    
    echo ""
    print_info "System Readiness: $validation_score/$max_score ($readiness_percent%)"
    
    if [ $readiness_percent -ge 80 ]; then
        print_success "System is READY for deployment"
        return 0
    elif [ $readiness_percent -ge 60 ]; then
        print_warning "System is PARTIALLY ready"
        return 1
    else
        print_error "System NEEDS setup"
        return 2
    fi
}

# Determine best deployment method
determine_deployment_method() {
    print_section "Deployment Method Selection"
    
    # Check Python environment first
    if [ -d "atlas_env" ] && [ -f "atlas_env/.deps_installed" ]; then
        if command_exists python3; then
            print_success "Recommended: Local Python deployment"
            echo "local"
            return 0
        fi
    fi
    
    # Check Docker next
    if command_exists docker && docker info >/dev/null 2>&1; then
        if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
            print_success "Recommended: Docker deployment"
            echo "docker"
            return 0
        fi
    fi
    
    # Check Kubernetes
    if command_exists kubectl && [ -d "k8s" ]; then
        print_success "Available: Kubernetes deployment"
        echo "kubernetes"
        return 0
    fi
    
    # Nothing ready
    print_warning "No deployment method ready"
    echo "setup"
    return 1
}

# Setup Python environment
setup_python_env() {
    print_section "Setting up Python Environment"
    
    if [ ! -d "atlas_env" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv atlas_env
        print_success "Virtual environment created"
    fi
    
    source atlas_env/bin/activate
    
    print_info "Upgrading pip..."
    pip install --upgrade pip >/dev/null 2>&1
    
    print_info "Installing dependencies (this may take a few minutes)..."
    if timeout 600 pip install -r requirements.txt >/dev/null 2>&1; then
        touch atlas_env/.deps_installed
        print_success "Dependencies installed successfully"
        return 0
    else
        print_warning "Dependency installation failed (network issues)"
        print_info "Trying essential packages only..."
        if pip install ollama fastapi uvicorn aiohttp psutil pydantic python-dotenv pyyaml click >/dev/null 2>&1; then
            touch atlas_env/.deps_installed
            print_success "Essential packages installed"
            return 0
        else
            print_error "Failed to install essential packages"
            return 1
        fi
    fi
}

# Quick health check
health_check() {
    local method=$1
    print_section "Health Check"
    
    case $method in
        "local")
            if port_in_use 8000; then
                print_success "Atlas appears to be running on port 8000"
                if wait_for_service "http://localhost:8000/status"; then
                    print_success "Atlas health check passed"
                    return 0
                else
                    print_warning "Atlas not responding to health checks"
                    return 1
                fi
            else
                print_info "Atlas not currently running"
                return 1
            fi
            ;;
        "docker")
            if docker ps | grep atlas-autonomous-system >/dev/null 2>&1; then
                print_success "Atlas Docker container running"
                if wait_for_service "http://localhost:8000/status"; then
                    print_success "Atlas health check passed"
                    return 0
                else
                    print_warning "Atlas not responding to health checks"
                    return 1
                fi
            else
                print_info "Atlas Docker container not running"
                return 1
            fi
            ;;
        *)
            print_info "Health check not available for this method"
            return 1
            ;;
    esac
}

# Start Atlas using best method
start_atlas() {
    local method=$1
    print_section "Starting Atlas MCP System"
    
    case $method in
        "local")
            if [ ! -f "atlas_env/.deps_installed" ]; then
                print_info "Dependencies not installed. Setting up..."
                if ! setup_python_env; then
                    print_error "Failed to setup Python environment"
                    return 1
                fi
            fi
            
            print_info "Starting Atlas locally..."
            ./start_atlas.sh --local --background
            ;;
        "docker")
            print_info "Starting Atlas with Docker..."
            docker compose --profile monitoring --profile mcp up -d
            ;;
        "kubernetes")
            print_info "Starting Atlas with Kubernetes..."
            if command_exists make; then
                make install-dev
            else
                ./k8s-manage.sh install development
            fi
            ;;
        "setup")
            print_info "System needs setup. Attempting automatic setup..."
            if command_exists python3; then
                if ! setup_python_env; then
                    print_error "Python setup failed"
                    return 1
                fi
                print_info "Retrying with local deployment..."
                ./start_atlas.sh --local --background
            else
                print_error "No suitable deployment method available"
                print_info "Please install Python 3.11+ or Docker"
                return 1
            fi
            ;;
        *)
            print_error "Unknown deployment method: $method"
            return 1
            ;;
    esac
}

# Show usage information
show_usage() {
    print_header "Atlas MCP Quick Start & Validation"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  validate    - Validate system readiness (default)"
    echo "  start       - Start Atlas using best available method"
    echo "  health      - Check if Atlas is running and healthy"
    echo "  setup       - Setup Python environment"
    echo "  status      - Show system status"
    echo "  stop        - Stop all Atlas services"
    echo "  help        - Show this help"
    echo ""
    echo "Options:"
    echo "  --force-local    - Force local Python deployment"
    echo "  --force-docker   - Force Docker deployment"  
    echo "  --quiet          - Reduce output"
    echo ""
    echo "Examples:"
    echo "  $0                    # Validate system"
    echo "  $0 start             # Auto-start with best method"
    echo "  $0 start --force-docker  # Force Docker deployment"
    echo "  $0 health            # Check if running"
    echo ""
}

# Main script logic
main() {
    local command="${1:-validate}"
    local force_method=""
    local quiet=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force-local)
                force_method="local"
                shift
                ;;
            --force-docker)
                force_method="docker"
                shift
                ;;
            --quiet)
                quiet=true
                shift
                ;;
            -h|--help|help)
                show_usage
                exit 0
                ;;
            validate|start|health|setup|status|stop)
                command="$1"
                shift
                ;;
            *)
                if [ -z "$command" ]; then
                    command="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Show header unless quiet
    if [ "$quiet" = false ]; then
        print_header "Atlas MCP Quick Start & Validation"
    fi
    
    case $command in
        "validate")
            validate_system
            local validation_result=$?
            
            if [ "$quiet" = false ]; then
                echo ""
                print_info "Next steps:"
                if [ $validation_result -eq 0 ]; then
                    print_info "System ready! Run: $0 start"
                elif [ $validation_result -eq 1 ]; then
                    print_info "Setup needed. Run: $0 setup"
                else
                    print_info "Major setup required. Check README.md"
                fi
            fi
            
            exit $validation_result
            ;;
        "start")
            # Validate first
            if ! validate_system >/dev/null 2>&1; then
                print_warning "System validation failed, attempting setup..."
            fi
            
            # Determine method
            if [ -n "$force_method" ]; then
                method="$force_method"
                print_info "Using forced deployment method: $method"
            else
                method=$(determine_deployment_method)
            fi
            
            # Start Atlas
            if start_atlas "$method"; then
                print_success "Atlas MCP system starting..."
                print_info "Web Interface: http://localhost:8000"
                print_info "API Docs: http://localhost:8000/docs"
                
                # Wait a moment and check health
                sleep 5
                if health_check "$method"; then
                    print_success "Atlas MCP is running and healthy!"
                else
                    print_warning "Atlas started but health check pending..."
                    print_info "Give it a few more seconds to fully initialize"
                fi
            else
                print_error "Failed to start Atlas MCP"
                exit 1
            fi
            ;;
        "health")
            method=$(determine_deployment_method)
            if health_check "$method"; then
                print_success "Atlas MCP is healthy"
                exit 0
            else
                print_warning "Atlas MCP health check failed"
                exit 1
            fi
            ;;
        "setup")
            if setup_python_env; then
                print_success "Python environment setup complete"
                print_info "You can now run: $0 start --force-local"
            else
                print_error "Setup failed"
                exit 1
            fi
            ;;
        "status")
            validate_system
            determine_deployment_method >/dev/null
            for method in local docker kubernetes; do
                health_check "$method" 2>/dev/null && print_info "$method deployment appears active"
            done
            ;;
        "stop")
            print_section "Stopping Atlas Services"
            
            # Stop Docker
            if docker ps | grep atlas >/dev/null 2>&1; then
                print_info "Stopping Docker services..."
                docker compose down
                print_success "Docker services stopped"
            fi
            
            # Stop local
            if [ -f "data/atlas.pid" ]; then
                print_info "Stopping local Atlas..."
                kill $(cat data/atlas.pid) 2>/dev/null && print_success "Local Atlas stopped"
                rm -f data/atlas.pid
            fi
            
            # Stop Kubernetes
            if command_exists kubectl && kubectl get pods | grep atlas >/dev/null 2>&1; then
                print_info "Stopping Kubernetes deployment..."
                if command_exists make; then
                    make clean-dev
                else
                    ./k8s-manage.sh clean development
                fi
                print_success "Kubernetes deployment stopped"
            fi
            
            print_success "All Atlas services stopped"
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"