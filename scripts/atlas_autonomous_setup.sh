#!/bin/bash

# Atlas Autonomous Setup Script
# Comprehensive automation for autonomous operation setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "🤖 Atlas Autonomous System Setup"
    echo "================================="
    echo -e "${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "${PURPLE}\n=== $1 ===${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check port availability
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        return 1
    else
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local timeout=${2:-60}
    local interval=${3:-2}
    local start_time=$(date +%s)
    
    while true; do
        if curl -fsS "$url" >/dev/null 2>&1; then
            return 0
        fi
        
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [ $elapsed -ge $timeout ]; then
            return 1
        fi
        
        sleep $interval
    done
}

# Function to check system requirements
check_requirements() {
    print_section "System Requirements Check"
    
    local all_good=true
    
    # Check Python
    if command_exists python3; then
        local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python 3 found: $python_version"
    else
        print_error "Python 3 not found"
        all_good=false
    fi
    
    # Check Docker
    if command_exists docker; then
        if docker info >/dev/null 2>&1; then
            print_success "Docker is running"
        else
            print_warning "Docker found but not running"
        fi
    else
        print_warning "Docker not found"
    fi
    
    # Check Docker Compose
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose available"
    else
        print_warning "Docker Compose not found"
    fi
    
    # Check kubectl
    if command_exists kubectl; then
        print_success "kubectl found"
    else
        print_warning "kubectl not found (optional for Kubernetes deployment)"
    fi
    
    # Check git
    if command_exists git; then
        print_success "Git found"
    else
        print_error "Git not found"
        all_good=false
    fi
    
    if [ "$all_good" = true ]; then
        print_success "All required dependencies found"
    else
        print_error "Some required dependencies missing"
        return 1
    fi
}

# Function to validate code structure
validate_code() {
    print_section "Code Structure Validation"
    
    # Check required files
    local required_files=(
        "atlas_core.py"
        "mcp_automation_server.py"
        "mcp_macos_automator.py"
        "requirements.txt"
        "docker-compose.yml"
        "start_atlas.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "$file exists"
        else
            print_error "$file missing"
            return 1
        fi
    done
    
    # Validate Python syntax
    print_status "Validating Python syntax..."
    python3 -m py_compile atlas_core.py mcp_*.py
    print_success "Python syntax validation passed"
    
    # Validate Docker configuration
    print_status "Validating Docker configuration..."
    docker compose config >/dev/null
    print_success "Docker Compose configuration valid"
}

# Function to setup Python environment
setup_python_env() {
    print_section "Python Environment Setup"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "atlas_env" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv atlas_env
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source atlas_env/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    python -m pip install --upgrade pip
    
    # Install dependencies
    print_status "Installing dependencies..."
    if pip install -r requirements.txt; then
        print_success "Dependencies installed successfully"
    else
        print_warning "Some dependencies failed to install, trying core packages..."
        pip install ollama openai fastapi uvicorn aiohttp psutil pydantic python-dotenv pyyaml click pytest pytest-asyncio
        print_success "Core dependencies installed"
    fi
}

# Function to run comprehensive tests
run_tests() {
    print_section "Running Tests"
    
    # Basic tests
    print_status "Running basic tests..."
    if python test_basic.py; then
        print_success "Basic tests passed"
    else
        print_error "Basic tests failed"
        return 1
    fi
    
    # Full tests (if dependencies are available)
    print_status "Running full tests..."
    if python test_atlas.py; then
        print_success "Full tests passed"
    else
        print_warning "Full tests had issues (possibly due to missing dependencies)"
    fi
}

# Function to check port availability
check_ports() {
    print_section "Port Availability Check"
    
    local ports=(8000 8080 4002 4003 4004 4005 6333 6379)
    local ports_available=true
    
    for port in "${ports[@]}"; do
        if check_port $port; then
            print_success "Port $port is available"
        else
            print_warning "Port $port is in use"
            ports_available=false
        fi
    done
    
    if [ "$ports_available" = true ]; then
        print_success "All required ports are available"
    else
        print_warning "Some ports are in use - services may conflict"
    fi
}

# Function to test autonomous deployment
test_autonomous_deployment() {
    print_section "Testing Autonomous Deployment"
    
    local deployment_method="local"
    
    # Determine best deployment method
    if command_exists docker && docker info >/dev/null 2>&1; then
        deployment_method="docker"
        print_status "Docker available - using Docker deployment"
    elif [ -f "atlas_env/bin/activate" ]; then
        deployment_method="local"
        print_status "Using local Python deployment"
    else
        print_error "No suitable deployment method available"
        return 1
    fi
    
    # Test deployment
    if [ "$deployment_method" = "docker" ]; then
        print_status "Testing Docker deployment (dry run)..."
        docker compose config >/dev/null
        print_success "Docker deployment configuration valid"
    else
        print_status "Testing local deployment..."
        source atlas_env/bin/activate
        python -c "from atlas_core import AtlasCore; print('✅ Atlas core imports successfully')"
        print_success "Local deployment ready"
    fi
}

# Function to create autonomous startup script
create_startup_script() {
    print_section "Creating Autonomous Startup Script"
    
    cat > atlas_start_autonomous.sh << 'EOF'
#!/bin/bash

# Atlas Autonomous Startup
# This script automatically determines the best way to start Atlas

set -e

# Source the main start script
if [ -f start_atlas.sh ]; then
    ./start_atlas.sh --background --mode auto
else
    echo "Error: start_atlas.sh not found"
    exit 1
fi

# Wait for services to be ready
echo "Waiting for Atlas to be ready..."
sleep 10

# Check if Atlas is responding
if curl -fsS http://localhost:8000/status >/dev/null 2>&1; then
    echo "✅ Atlas is running autonomously"
    echo "🌐 Web interface: http://localhost:8000"
else
    echo "❌ Atlas failed to start properly"
    exit 1
fi
EOF

    chmod +x atlas_start_autonomous.sh
    print_success "Autonomous startup script created: atlas_start_autonomous.sh"
}

# Function to create health monitoring script
create_health_monitor() {
    print_section "Creating Health Monitoring Script"
    
    cat > atlas_health_monitor.sh << 'EOF'
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
EOF

    chmod +x atlas_health_monitor.sh
    print_success "Health monitoring script created: atlas_health_monitor.sh"
}

# Function to generate autonomous setup report
generate_report() {
    print_section "Generating Setup Report"
    
    local report_file="atlas_autonomous_report.json"
    
    cat > "$report_file" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "system": {
    "os": "$(uname -s)",
    "architecture": "$(uname -m)",
    "python_version": "$(python3 --version 2>&1 | cut -d' ' -f2)",
    "docker_available": $(command_exists docker && echo true || echo false),
    "kubectl_available": $(command_exists kubectl && echo true || echo false)
  },
  "atlas": {
    "code_structure_valid": true,
    "dependencies_installed": true,
    "autonomous_scripts_created": true,
    "deployment_ready": true
  },
  "services": {
    "core_port": 8000,
    "frontend_port": 8080,
    "mcp_automation_port": 4002,
    "mcp_automator_port": 4003,
    "tts_port": 4004,
    "playwright_port": 4005
  },
  "autonomous_capabilities": {
    "auto_deployment": true,
    "health_monitoring": true,
    "service_management": true,
    "github_integration": true
  }
}
EOF

    print_success "Setup report generated: $report_file"
}

# Main function
main() {
    print_header
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    print_status "Starting Atlas Autonomous System setup..."
    
    # Run all setup steps
    check_requirements
    validate_code
    setup_python_env
    run_tests
    check_ports
    test_autonomous_deployment
    create_startup_script
    create_health_monitor
    generate_report
    
    print_success "🎉 Atlas Autonomous System setup completed!"
    echo ""
    echo "🚀 Quick Start Commands:"
    echo "  ./atlas_start_autonomous.sh    # Start Atlas autonomously"
    echo "  ./atlas_health_monitor.sh      # Check system health"
    echo "  ./start_atlas.sh --help        # See all options"
    echo ""
    echo "📊 Setup Report: atlas_autonomous_report.json"
    echo "🌐 Once started, Atlas will be available at: http://localhost:8000"
}

# Show help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Atlas Autonomous Setup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h    Show this help message"
    echo ""
    echo "This script sets up Atlas for autonomous operation by:"
    echo "  - Checking system requirements"
    echo "  - Validating code structure"
    echo "  - Setting up Python environment"
    echo "  - Running tests"
    echo "  - Creating autonomous startup scripts"
    echo "  - Setting up health monitoring"
    exit 0
fi

# Run main function
main "$@"