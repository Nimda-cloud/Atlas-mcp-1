#!/bin/bash
# Atlas MCP Firewall Detection and Mitigation
# Automatically detects firewall restrictions and applies appropriate workarounds

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FIREWALL_TEST_LOG="/tmp/atlas-firewall-test.log"
MITIGATION_REPORT="/tmp/atlas-firewall-mitigation.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅ $*${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️  $*${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌ $*${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] 📋 $*${NC}"
}

# Initialize mitigation report
init_mitigation_report() {
    if command -v jq &>/dev/null; then
        cat > "$MITIGATION_REPORT" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "environment": {
        "platform": "$(uname -s)",
        "architecture": "$(uname -m)",
        "shell": "$0",
        "user": "$(whoami)"
    },
    "firewall_tests": {},
    "mitigations": [],
    "recommendations": []
}
EOF
    else
        # Fallback to simple text format if jq is not available
        warn "jq not available, using simple text format for reports"
        cat > "$MITIGATION_REPORT" << EOF
# Atlas MCP Firewall Detection Report
timestamp=$(date -Iseconds)
platform=$(uname -s)
architecture=$(uname -m)
user=$(whoami)

# Test Results
EOF
    fi
}

# Test network connectivity
test_network_connectivity() {
    info "Testing network connectivity and firewall restrictions..."
    
    local tests=(
        "localhost:127.0.0.1:80:Local loopback"
        "internal_k8s:10.244.0.1:443:Kubernetes pod CIDR"
        "internal_service:10.96.0.1:53:Kubernetes service CIDR"
        "docker_bridge:172.17.0.1:80:Docker bridge network"
        "private_a:10.0.0.1:80:Private Class A"
        "private_b:172.16.0.1:80:Private Class B"
        "private_c:192.168.1.1:80:Private Class C"
        "public_dns:8.8.8.8:53:Public DNS"
        "pypi:pypi.org:443:PyPI package index"
        "github:github.com:443:GitHub"
    )
    
    local results=()
    
    for test_config in "${tests[@]}"; do
        IFS=':' read -r test_name test_host test_port test_desc <<< "$test_config"
        
        info "Testing $test_desc ($test_host:$test_port)..."
        
        local test_result="blocked"
        local test_method="unknown"
        
        # Test with different methods (faster timeouts)
        if timeout 2 nc -zv "$test_host" "$test_port" &>/dev/null; then
            test_result="accessible"
            test_method="netcat"
        elif timeout 2 curl -s --connect-timeout 1 --max-time 2 "$test_host:$test_port" &>/dev/null; then
            test_result="accessible"
            test_method="curl"
        elif timeout 2 telnet "$test_host" "$test_port" <<< "" &>/dev/null; then
            test_result="accessible"
            test_method="telnet"
        elif timeout 2 ping -c 1 -W 1 "$test_host" &>/dev/null; then
            test_result="ping_only"
            test_method="ping"
        fi
        
        # Update report
        if command -v jq &>/dev/null; then
            jq --arg name "$test_name" \
               --arg host "$test_host" \
               --arg port "$test_port" \
               --arg desc "$test_desc" \
               --arg result "$test_result" \
               --arg method "$test_method" \
               '.firewall_tests[$name] = {
                   host: $host,
                   port: $port,
                   description: $desc,
                   result: $result,
                   test_method: $method
               }' "$MITIGATION_REPORT" > "${MITIGATION_REPORT}.tmp" && 
               mv "${MITIGATION_REPORT}.tmp" "$MITIGATION_REPORT"
        else
            # Simple text format fallback
            echo "test_${test_name}=${test_result}:${test_host}:${test_port}:${test_desc}:${test_method}" >> "$MITIGATION_REPORT"
        fi
        
        if [[ "$test_result" == "accessible" ]]; then
            log "$test_desc: ACCESSIBLE via $test_method"
        elif [[ "$test_result" == "ping_only" ]]; then
            warn "$test_desc: PING ONLY"
        else
            warn "$test_desc: BLOCKED"
        fi
        
        results+=("$test_name:$test_result")
    done
    
    log "Network connectivity testing completed"
    return 0
}

# Detect firewall restrictions
detect_firewall_restrictions() {
    info "Analyzing firewall restrictions..."
    
    local restrictions=()
    
    # Check if private networks are blocked
    local private_blocked=0
    local private_total=0
    
    for test_name in "internal_k8s" "internal_service" "docker_bridge" "private_a" "private_b" "private_c"; do
        local result
        if command -v jq &>/dev/null; then
            result=$(jq -r ".firewall_tests.$test_name.result" "$MITIGATION_REPORT" 2>/dev/null || echo "blocked")
        else
            result=$(grep "test_${test_name}=" "$MITIGATION_REPORT" | cut -d'=' -f2 | cut -d':' -f1 || echo "blocked")
        fi
        
        ((private_total++))
        if [[ "$result" == "blocked" ]]; then
            ((private_blocked++))
        fi
    done
    
    # Analyze restrictions
    if [[ $private_blocked -eq $private_total ]]; then
        restrictions+=("all_private_networks")
        add_mitigation "private_network_block" "All private networks are blocked" "Use localhost port-forwarding for service access"
    elif [[ $private_blocked -gt 0 ]]; then
        restrictions+=("some_private_networks")
        add_mitigation "partial_private_block" "Some private networks are blocked" "Test each network individually"
    fi
    
    # Check Kubernetes specific restrictions
    local k8s_blocked=0
    for test_name in "internal_k8s" "internal_service"; do
        local result
        if command -v jq &>/dev/null; then
            result=$(jq -r ".firewall_tests.$test_name.result" "$MITIGATION_REPORT" 2>/dev/null || echo "blocked")
        else
            result=$(grep "test_${test_name}=" "$MITIGATION_REPORT" | cut -d'=' -f2 | cut -d':' -f1 || echo "blocked")
        fi
        if [[ "$result" == "blocked" ]]; then
            ((k8s_blocked++))
        fi
    done
    
    if [[ $k8s_blocked -gt 0 ]]; then
        restrictions+=("kubernetes_networks")
        add_mitigation "k8s_network_block" "Kubernetes networks are blocked" "Use port-forward for pod/service access"
    fi
    
    # Check external connectivity
    local external_accessible=0
    for test_name in "public_dns" "pypi" "github"; do
        local result
        if command -v jq &>/dev/null; then
            result=$(jq -r ".firewall_tests.$test_name.result" "$MITIGATION_REPORT" 2>/dev/null || echo "blocked")
        else
            result=$(grep "test_${test_name}=" "$MITIGATION_REPORT" | cut -d'=' -f2 | cut -d':' -f1 || echo "blocked")
        fi
        if [[ "$result" == "accessible" ]]; then
            ((external_accessible++))
        fi
    done
    
    if [[ $external_accessible -eq 0 ]]; then
        restrictions+=("no_external_access")
        add_mitigation "external_block" "No external access available" "Use offline mode and cached resources"
    fi
    
    # Update report with detected restrictions
    if command -v jq &>/dev/null; then
        jq --argjson restrictions "$(printf '%s\n' "${restrictions[@]}" | jq -R . | jq -s .)" \
           '.detected_restrictions = $restrictions' \
           "$MITIGATION_REPORT" > "${MITIGATION_REPORT}.tmp" && 
           mv "${MITIGATION_REPORT}.tmp" "$MITIGATION_REPORT"
    else
        echo "" >> "$MITIGATION_REPORT"
        echo "# Detected Restrictions" >> "$MITIGATION_REPORT"
        printf 'restriction_%s=true\n' "${restrictions[@]}" >> "$MITIGATION_REPORT"
    fi
    
    log "Firewall analysis completed - detected ${#restrictions[@]} restriction types"
}

# Add mitigation to report
add_mitigation() {
    local mitigation_type=$1
    local description=$2
    local solution=$3
    
    if command -v jq &>/dev/null; then
        jq --arg type "$mitigation_type" \
           --arg desc "$description" \
           --arg sol "$solution" \
           '.mitigations += [{
               type: $type,
               description: $desc,
               solution: $sol,
               timestamp: now | todate
           }]' "$MITIGATION_REPORT" > "${MITIGATION_REPORT}.tmp" && 
           mv "${MITIGATION_REPORT}.tmp" "$MITIGATION_REPORT"
    else
        echo "mitigation_${mitigation_type}=${description}|${solution}" >> "$MITIGATION_REPORT"
    fi
}

# Add recommendation to report
add_recommendation() {
    local priority=$1
    local category=$2
    local recommendation=$3
    
    if command -v jq &>/dev/null; then
        jq --arg prio "$priority" \
           --arg cat "$category" \
           --arg rec "$recommendation" \
           '.recommendations += [{
               priority: $prio,
               category: $cat,
               recommendation: $rec
           }]' "$MITIGATION_REPORT" > "${MITIGATION_REPORT}.tmp" && 
           mv "${MITIGATION_REPORT}.tmp" "$MITIGATION_REPORT"
    else
        echo "recommendation_${priority}_${category}=${recommendation}" >> "$MITIGATION_REPORT"
    fi
}

# Generate firewall-safe configuration
generate_firewall_safe_config() {
    info "Generating firewall-safe configuration..."
    
    local config_dir="$PROJECT_ROOT/firewall-configs"
    mkdir -p "$config_dir"
    
    # Docker Compose override for localhost access
    cat > "$config_dir/docker-compose.firewall-safe.yml" << EOF
version: '3.8'

# Firewall-safe Docker Compose override
# Use only localhost networking and avoid internal IPs

services:
  atlas-core:
    network_mode: "host"
    environment:
      - ATLAS_BIND_ADDRESS=127.0.0.1
      - ATLAS_WEB_PORT=8000
      - DISABLE_EXTERNAL_CALLS=true
    ports:
      - "127.0.0.1:8000:8000"

  atlas-frontend:
    network_mode: "host"
    environment:
      - FRONTEND_BIND_ADDRESS=127.0.0.1
      - FRONTEND_PORT=8080
    ports:
      - "127.0.0.1:8080:8080"

  mcp-automation:
    network_mode: "host"
    environment:
      - MCP_BIND_ADDRESS=127.0.0.1
      - MCP_PORT=4002
    ports:
      - "127.0.0.1:4002:4002"

networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 127.0.0.0/8
EOF
    
    # Kubernetes configuration for localhost testing
    cat > "$config_dir/port-forward-all.sh" << 'EOF'
#!/bin/bash
# Port-forward all Atlas MCP services for firewall-safe access

NAMESPACE="${NAMESPACE:-atlas-mcp-dev}"

echo "🔄 Setting up port-forwards for all services..."

# Function to start port-forward in background
start_port_forward() {
    local service=$1
    local port=$2
    local local_port=${3:-$port}
    
    echo "Forwarding $service:$port to localhost:$local_port"
    kubectl port-forward "svc/$service" "$local_port:$port" -n "$NAMESPACE" &
    echo $! > "/tmp/pf-$service.pid"
}

# Start all port-forwards
start_port_forward "atlas-core-service" "8000"
start_port_forward "atlas-frontend-service" "8080"
start_port_forward "mcp-automation-service" "4002"
start_port_forward "mcp-automator-service" "4003"
start_port_forward "mcp-tts-service" "4004"

# Wait for port-forwards to establish
sleep 10

echo "✅ All port-forwards established!"
echo "🌐 Access services at:"
echo "  - Atlas Core: http://localhost:8000"
echo "  - Atlas Frontend: http://localhost:8080"
echo "  - MCP Automation: http://localhost:4002"
echo "  - MCP Automator: http://localhost:4003"
echo "  - MCP TTS: http://localhost:4004"
echo ""
echo "To stop all port-forwards: ./stop-port-forwards.sh"

# Keep running
wait
EOF
    
    # Port-forward cleanup script
    cat > "$config_dir/stop-port-forwards.sh" << 'EOF'
#!/bin/bash
# Stop all Atlas MCP port-forwards

echo "🛑 Stopping all port-forwards..."

for pidfile in /tmp/pf-*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        if kill "$pid" 2>/dev/null; then
            echo "Stopped port-forward (PID: $pid)"
        fi
        rm -f "$pidfile"
    fi
done

# Kill any remaining kubectl port-forward processes
pkill -f "kubectl port-forward" || true

echo "✅ All port-forwards stopped"
EOF
    
    chmod +x "$config_dir"/*.sh
    
    log "Firewall-safe configuration generated in: $config_dir"
}

# Generate recommendations based on detected restrictions
generate_recommendations() {
    info "Generating recommendations..."
    
    # Check what restrictions were detected
    local restrictions=""
    if command -v jq &>/dev/null; then
        restrictions=$(jq -r '.detected_restrictions[]' "$MITIGATION_REPORT" 2>/dev/null || echo "")
    else
        restrictions=$(grep "restriction_" "$MITIGATION_REPORT" | cut -d'=' -f1 | sed 's/restriction_//' || echo "")
    fi
    
    if echo "$restrictions" | grep -q "all_private_networks"; then
        add_recommendation "HIGH" "networking" "Use only localhost (127.0.0.1) for service access"
        add_recommendation "HIGH" "kubernetes" "Use kubectl port-forward for all Kubernetes service testing"
        add_recommendation "MEDIUM" "deployment" "Consider using self-hosted runners for full network access"
    fi
    
    if echo "$restrictions" | grep -q "kubernetes_networks"; then
        add_recommendation "HIGH" "kubernetes" "Avoid direct pod IP access, use service names with port-forward"
        add_recommendation "MEDIUM" "testing" "Implement artifact-based testing instead of live service calls"
    fi
    
    if echo "$restrictions" | grep -q "no_external_access"; then
        add_recommendation "HIGH" "dependencies" "Use cached dependencies and offline installation methods"
        add_recommendation "HIGH" "images" "Pre-build Docker images in unrestricted environment"
        add_recommendation "MEDIUM" "security" "Configure custom allowlist for essential external services"
    fi
    
    # Always recommend firewall-safe practices
    add_recommendation "MEDIUM" "practices" "Use the generated firewall-safe configurations"
    add_recommendation "LOW" "monitoring" "Monitor deployment with artifact collection instead of live monitoring"
    
    log "Recommendations generated"
}

# Display final report
display_report() {
    info "Firewall Detection and Mitigation Report"
    echo ""
    
    # Display restrictions
    echo -e "${YELLOW}🚨 Detected Restrictions:${NC}"
    
    if command -v jq &>/dev/null && jq -e '.detected_restrictions' "$MITIGATION_REPORT" &>/dev/null; then
        local restrictions
        restrictions=$(jq -r '.detected_restrictions[]' "$MITIGATION_REPORT" 2>/dev/null || echo "")
        
        if [[ -z "$restrictions" ]]; then
            echo -e "${GREEN}  ✅ No major firewall restrictions detected${NC}"
        else
            echo "$restrictions" | while read -r restriction; do
                case "$restriction" in
                    "all_private_networks")
                        echo -e "${RED}  ❌ All private networks are blocked${NC}"
                        ;;
                    "kubernetes_networks")
                        echo -e "${RED}  ❌ Kubernetes networks are blocked${NC}"
                        ;;
                    "no_external_access")
                        echo -e "${RED}  ❌ No external network access${NC}"
                        ;;
                    *)
                        echo -e "${YELLOW}  ⚠️  $restriction${NC}"
                        ;;
                esac
            done
        fi
    else
        # Fallback for text format
        if grep -q "restriction_" "$MITIGATION_REPORT"; then
            grep "restriction_" "$MITIGATION_REPORT" | while read -r line; do
                local restriction=$(echo "$line" | cut -d'=' -f1 | sed 's/restriction_//')
                echo -e "${YELLOW}  ⚠️  $restriction${NC}"
            done
        else
            echo -e "${GREEN}  ✅ No major firewall restrictions detected${NC}"
        fi
    fi
    
    echo ""
    
    # Display mitigations
    echo -e "${BLUE}🔧 Available Mitigations:${NC}"
    if command -v jq &>/dev/null && jq -e '.mitigations' "$MITIGATION_REPORT" &>/dev/null; then
        jq -r '.mitigations[] | "  ✅ \(.description): \(.solution)"' "$MITIGATION_REPORT" 2>/dev/null || echo "  No specific mitigations needed"
    else
        if grep -q "mitigation_" "$MITIGATION_REPORT"; then
            grep "mitigation_" "$MITIGATION_REPORT" | while read -r line; do
                local mitigation=$(echo "$line" | cut -d'=' -f2 | tr '|' ':')
                echo "  ✅ $mitigation"
            done
        else
            echo "  No specific mitigations needed"
        fi
    fi
    
    echo ""
    
    # Display recommendations
    echo -e "${GREEN}💡 Recommendations:${NC}"
    if command -v jq &>/dev/null && jq -e '.recommendations' "$MITIGATION_REPORT" &>/dev/null; then
        jq -r '.recommendations[] | "  [\(.priority)] \(.recommendation)"' "$MITIGATION_REPORT" 2>/dev/null | sort
    else
        if grep -q "recommendation_" "$MITIGATION_REPORT"; then
            grep "recommendation_" "$MITIGATION_REPORT" | while read -r line; do
                local rec=$(echo "$line" | cut -d'=' -f2)
                local priority=$(echo "$line" | cut -d'=' -f1 | sed 's/recommendation_//' | cut -d'_' -f1)
                echo "  [$priority] $rec"
            done | sort
        else
            echo "  Use localhost networking for all service access"
            echo "  Test deployments with port-forwarding"
        fi
    fi
    
    echo ""
    echo -e "${BLUE}📄 Full report saved to: $MITIGATION_REPORT${NC}"
    echo -e "${BLUE}🔧 Firewall-safe configs: $PROJECT_ROOT/firewall-configs/${NC}"
}

# Main function
main() {
    echo -e "${BLUE}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║    🔥 Atlas MCP Firewall Detection & Mitigation Tool 🔥     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    init_mitigation_report
    test_network_connectivity
    detect_firewall_restrictions
    generate_firewall_safe_config
    generate_recommendations
    display_report
    
    log "Firewall detection and mitigation completed!"
    
    # Copy report to project artifacts if directory exists
    if [[ -d "$PROJECT_ROOT/automation-artifacts" ]]; then
        cp "$MITIGATION_REPORT" "$PROJECT_ROOT/automation-artifacts/"
        log "Report copied to automation artifacts"
    fi
}

# Run main function
main "$@"