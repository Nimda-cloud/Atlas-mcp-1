#!/bin/bash
# Atlas MCP Master Setup Script
# Intelligent deployment with automatic firewall detection and mitigation

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SETUP_MODE="${SETUP_MODE:-auto}"  # auto, safe, full
SKIP_FIREWALL_CHECK="${SKIP_FIREWALL_CHECK:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅ $*${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] 📋 $*${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️  $*${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌ $*${NC}"
}

success() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')] 🎉 $*${NC}"
}

# Banner
show_banner() {
    echo -e "${PURPLE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     █████╗ ████████╗██╗      █████╗ ███████╗    ███╗   ███╗ ██████╗██████╗  ║
║    ██╔══██╗╚══██╔══╝██║     ██╔══██╗██╔════╝    ████╗ ████║██╔════╝██╔══██╗ ║
║    ███████║   ██║   ██║     ███████║███████╗    ██╔████╔██║██║     ██████╔╝ ║
║    ██╔══██║   ██║   ██║     ██╔══██║╚════██║    ██║╚██╔╝██║██║     ██╔═══╝  ║
║    ██║  ██║   ██║   ███████╗██║  ██║███████║    ██║ ╚═╝ ██║╚██████╗██║      ║
║    ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝    ╚═╝     ╚═╝ ╚═════╝╚═╝      ║
║                                                                              ║
║                        MASTER SETUP & AUTOMATION                            ║
║                    Intelligent • Firewall-Safe • Resilient                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo ""
    echo -e "${BLUE}🚀 Welcome to Atlas MCP Master Setup${NC}"
    echo -e "${BLUE}📍 Mode: $SETUP_MODE${NC}"
    echo -e "${BLUE}📁 Project: $PROJECT_ROOT${NC}"
    echo ""
}

# Display help
show_help() {
    cat << EOF
Atlas MCP Master Setup Script

USAGE:
    $0 [OPTIONS] [MODE]

MODES:
    auto        - Automatic setup with firewall detection (default)
    safe        - Firewall-safe mode (localhost only)
    full        - Full automation mode
    firewall    - Only run firewall detection
    help        - Show this help

OPTIONS:
    --skip-firewall-check    Skip firewall detection
    --cleanup               Clean up previous installations
    --verbose              Enable verbose output
    --artifacts-dir DIR     Custom artifacts directory

EXAMPLES:
    $0                      # Auto mode with firewall detection
    $0 safe                 # Safe mode for restricted environments
    $0 full                 # Full automation mode
    $0 --cleanup auto       # Clean up and run auto mode

ENVIRONMENT VARIABLES:
    SETUP_MODE              Setup mode (auto, safe, full)
    SKIP_FIREWALL_CHECK     Skip firewall detection (true/false)
    CLEANUP_ON_EXIT         Clean up on exit (true/false)
    ARTIFACTS_DIR          Custom artifacts directory

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-firewall-check)
                SKIP_FIREWALL_CHECK="true"
                shift
                ;;
            --cleanup)
                CLEANUP_PREVIOUS="true"
                shift
                ;;
            --verbose)
                set -x
                shift
                ;;
            --artifacts-dir)
                ARTIFACTS_DIR="$2"
                shift 2
                ;;
            help|--help|-h)
                show_help
                exit 0
                ;;
            auto|safe|full|firewall)
                SETUP_MODE="$1"
                shift
                ;;
            *)
                warn "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    local required_commands=("docker" "git")
    local optional_commands=("kubectl" "kind" "curl" "jq")
    local missing_required=()
    local missing_optional=()
    
    # Check required commands
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &>/dev/null; then
            missing_required+=("$cmd")
        else
            log "$cmd is available"
        fi
    done
    
    # Check optional commands
    for cmd in "${optional_commands[@]}"; do
        if ! command -v "$cmd" &>/dev/null; then
            missing_optional+=("$cmd")
        else
            log "$cmd is available"
        fi
    done
    
    # Handle missing required commands
    if [[ ${#missing_required[@]} -gt 0 ]]; then
        error "Missing required commands: ${missing_required[*]}"
        info "Please install the missing commands and try again"
        return 1
    fi
    
    # Handle missing optional commands
    if [[ ${#missing_optional[@]} -gt 0 ]]; then
        warn "Missing optional commands: ${missing_optional[*]}"
        info "Some features may not be available"
        
        # Try to install missing commands if possible
        for cmd in "${missing_optional[@]}"; do
            case "$cmd" in
                "jq")
                    info "Attempting to install jq..."
                    if command -v apt-get &>/dev/null; then
                        sudo apt-get update && sudo apt-get install -y jq || warn "Failed to install jq"
                    elif command -v brew &>/dev/null; then
                        brew install jq || warn "Failed to install jq"
                    fi
                    ;;
                "kubectl")
                    info "kubectl is required for Kubernetes operations"
                    warn "Please install kubectl manually"
                    ;;
                "kind")
                    info "Attempting to install kind..."
                    if [[ "$(uname -s)" == "Linux" ]]; then
                        curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64 2>/dev/null || warn "Failed to download kind"
                        chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind || warn "Failed to install kind"
                    fi
                    ;;
            esac
        done
    fi
    
    log "Prerequisites check completed"
}

# Run firewall detection if not skipped
run_firewall_detection() {
    if [[ "$SKIP_FIREWALL_CHECK" == "true" ]]; then
        info "Skipping firewall detection (--skip-firewall-check specified)"
        return 0
    fi
    
    info "Running firewall detection and mitigation..."
    
    if [[ -x "$SCRIPT_DIR/firewall-detection.sh" ]]; then
        "$SCRIPT_DIR/firewall-detection.sh" || warn "Firewall detection failed, continuing anyway"
        
        # Check if firewall report exists and analyze it
        local report_file="/tmp/atlas-firewall-mitigation.json"
        if [[ -f "$report_file" ]]; then
            local restrictions
            restrictions=$(jq -r '.detected_restrictions[]' "$report_file" 2>/dev/null || echo "")
            
            if [[ -n "$restrictions" ]]; then
                warn "Firewall restrictions detected:"
                echo "$restrictions" | while read -r restriction; do
                    warn "  - $restriction"
                done
                
                # Adjust setup mode based on restrictions
                if echo "$restrictions" | grep -q "all_private_networks"; then
                    if [[ "$SETUP_MODE" == "auto" ]]; then
                        warn "Switching to safe mode due to firewall restrictions"
                        SETUP_MODE="safe"
                    fi
                fi
            else
                log "No major firewall restrictions detected"
            fi
        fi
    else
        warn "Firewall detection script not found, skipping"
    fi
}

# Clean up previous installations
cleanup_previous() {
    if [[ "${CLEANUP_PREVIOUS:-false}" == "true" ]]; then
        info "Cleaning up previous installations..."
        
        # Stop and remove any existing containers
        docker stop $(docker ps -q --filter "label=atlas-mcp" 2>/dev/null) 2>/dev/null || true
        docker rm $(docker ps -aq --filter "label=atlas-mcp" 2>/dev/null) 2>/dev/null || true
        
        # Remove Atlas Kind clusters
        if command -v kind &>/dev/null; then
            kind get clusters | grep "atlas-mcp" | while read -r cluster; do
                warn "Deleting existing cluster: $cluster"
                kind delete cluster --name "$cluster" || true
            done
        fi
        
        # Clean up artifacts directories
        for dir in "automation-artifacts" "k8s-artifacts" "firewall-configs"; do
            if [[ -d "$PROJECT_ROOT/$dir" ]]; then
                warn "Removing $dir"
                rm -rf "$PROJECT_ROOT/$dir"
            fi
        done
        
        log "Cleanup completed"
    fi
}

# Choose and execute setup mode
execute_setup() {
    cd "$PROJECT_ROOT"
    
    case "$SETUP_MODE" in
        "auto")
            info "Executing automatic setup with intelligent firewall handling..."
            if [[ -x "$SCRIPT_DIR/full-automation-setup.sh" ]]; then
                CLEANUP_ON_EXIT="${CLEANUP_ON_EXIT:-false}" "$SCRIPT_DIR/full-automation-setup.sh"
            else
                error "Full automation script not found"
                return 1
            fi
            ;;
        "safe")
            info "Executing firewall-safe setup..."
            execute_safe_setup
            ;;
        "full")
            info "Executing full automation setup..."
            if [[ -x "$SCRIPT_DIR/full-automation-setup.sh" ]]; then
                SKIP_FIREWALL_CHECK="true" "$SCRIPT_DIR/full-automation-setup.sh"
            else
                error "Full automation script not found"
                return 1
            fi
            ;;
        "firewall")
            info "Running only firewall detection..."
            SKIP_FIREWALL_CHECK="false"
            run_firewall_detection
            return 0
            ;;
        *)
            error "Unknown setup mode: $SETUP_MODE"
            show_help
            return 1
            ;;
    esac
}

# Execute safe setup for firewall-restricted environments
execute_safe_setup() {
    info "Setting up Atlas MCP in firewall-safe mode..."
    
    # Use Docker Compose for local setup
    if [[ -f "docker-compose.yml" ]]; then
        info "Starting services with Docker Compose..."
        
        # Create firewall-safe override if configs exist
        local override_file=""
        if [[ -f "firewall-configs/docker-compose.firewall-safe.yml" ]]; then
            override_file="-f firewall-configs/docker-compose.firewall-safe.yml"
            info "Using firewall-safe configuration"
        fi
        
        # Start services
        docker compose $override_file up -d --build || warn "Some services failed to start"
        
        # Wait for services to be ready
        info "Waiting for services to start..."
        sleep 30
        
        # Test services
        test_services_local
        
    else
        warn "docker-compose.yml not found, trying alternative setup..."
        execute_minimal_setup
    fi
}

# Test services running locally
test_services_local() {
    info "Testing locally running services..."
    
    local services=(
        "atlas-core:8000:/status"
        "atlas-frontend:8080:/health"
        "mcp-automation:4002:/health"
    )
    
    local success_count=0
    local total_count=${#services[@]}
    
    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name service_port health_path <<< "$service_config"
        
        info "Testing $service_name on port $service_port..."
        
        if curl -s --connect-timeout 5 --max-time 10 "http://localhost:$service_port$health_path" >/dev/null 2>&1; then
            log "$service_name is responding"
            ((success_count++))
        else
            warn "$service_name is not responding"
        fi
    done
    
    if [[ $success_count -eq $total_count ]]; then
        success "All services are running successfully! ($success_count/$total_count)"
    else
        warn "Some services are not responding ($success_count/$total_count)"
    fi
    
    # Display access information
    info "Service access URLs:"
    info "  🌐 Atlas Core: http://localhost:8000"
    info "  🎨 Atlas Frontend: http://localhost:8080"
    info "  🔧 MCP Automation: http://localhost:4002"
}

# Execute minimal setup as fallback
execute_minimal_setup() {
    info "Setting up minimal Atlas MCP installation..."
    
    # Try to run atlas_core directly
    if [[ -f "atlas_core.py" ]]; then
        info "Starting Atlas Core directly..."
        
        # Check if virtual environment exists
        if [[ ! -d "atlas_env" ]]; then
            info "Creating Python virtual environment..."
            python3 -m venv atlas_env
        fi
        
        # Activate virtual environment
        source atlas_env/bin/activate
        
        # Install minimal requirements
        if [[ -f "requirements.minimal.txt" ]]; then
            pip install -r requirements.minimal.txt || warn "Failed to install some packages"
        else
            pip install fastapi uvicorn || warn "Failed to install basic packages"
        fi
        
        # Start Atlas Core
        info "Starting Atlas Core on port 8000..."
        python atlas_core.py &
        
        # Wait and test
        sleep 10
        test_services_local
        
    else
        error "Unable to find Atlas Core files"
        return 1
    fi
}

# Generate final report
generate_final_report() {
    info "Generating final setup report..."
    
    local report_dir="$PROJECT_ROOT/setup-report"
    mkdir -p "$report_dir"
    
    local report_file="$report_dir/atlas-setup-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# Atlas MCP Setup Report

**Setup Mode:** $SETUP_MODE
**Timestamp:** $(date -Iseconds)
**Project Root:** $PROJECT_ROOT

## Setup Summary

### Mode Details
- **Selected Mode:** $SETUP_MODE
- **Firewall Check:** $(if [[ "$SKIP_FIREWALL_CHECK" == "true" ]]; then echo "Skipped"; else echo "Executed"; fi)
- **Cleanup:** $(if [[ "${CLEANUP_PREVIOUS:-false}" == "true" ]]; then echo "Executed"; else echo "Skipped"; fi)

### Environment
- **Platform:** $(uname -s)
- **Architecture:** $(uname -m)
- **Docker:** $(docker --version | head -1)
- **Kubectl:** $(kubectl version --client --short 2>/dev/null || echo "Not available")
- **Kind:** $(kind version 2>/dev/null || echo "Not available")

### Service Status
EOF
    
    # Test current service status and add to report
    if curl -s --connect-timeout 3 "http://localhost:8000/status" >/dev/null 2>&1; then
        echo "- ✅ Atlas Core: Running (http://localhost:8000)" >> "$report_file"
    else
        echo "- ❌ Atlas Core: Not responding" >> "$report_file"
    fi
    
    if curl -s --connect-timeout 3 "http://localhost:8080/health" >/dev/null 2>&1; then
        echo "- ✅ Atlas Frontend: Running (http://localhost:8080)" >> "$report_file"
    else
        echo "- ❌ Atlas Frontend: Not responding" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

### Next Steps
1. **Access Services:**
   - Atlas Core: http://localhost:8000
   - Atlas Frontend: http://localhost:8080
   - MCP Services: Check individual port configurations

2. **Troubleshooting:**
   - Check logs in setup-report directory
   - Review firewall detection results if available
   - Use Docker Compose logs for service debugging

3. **Advanced Usage:**
   - Kubernetes deployment: Use scripts/full-automation-setup.sh
   - Firewall-safe mode: Use firewall-configs/
   - Development mode: Use start_atlas.sh

### Generated Files
$(ls -la "$PROJECT_ROOT" | grep -E "(automation-artifacts|k8s-artifacts|firewall-configs|setup-report)" || echo "No additional artifacts")

---
*Generated by Atlas MCP Master Setup Script*
EOF
    
    success "Setup report generated: $report_file"
    echo ""
    echo -e "${GREEN}📊 Setup completed successfully!${NC}"
    echo -e "${BLUE}📄 Report: $report_file${NC}"
    echo -e "${BLUE}🌐 Atlas Core: http://localhost:8000${NC}"
    echo -e "${BLUE}🎨 Frontend: http://localhost:8080${NC}"
}

# Main execution
main() {
    show_banner
    
    # Parse arguments
    parse_args "$@"
    
    # Execute setup pipeline
    check_prerequisites
    cleanup_previous
    run_firewall_detection
    execute_setup
    generate_final_report
    
    success "Atlas MCP setup completed!"
}

# Run main function
main "$@"