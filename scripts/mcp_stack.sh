#!/bin/bash
# MCP Stack Management Utility

set -euo pipefail

MCP_STACK_DIR="$HOME/mcp-stack"
PROXY_PID_FILE="$MCP_STACK_DIR/proxy/proxy.pid"
PROXY_CONFIG="$MCP_STACK_DIR/proxy/config/native-stdio.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_proxy_running() {
    if [[ -f "$PROXY_PID_FILE" ]]; then
        local pid=$(cat "$PROXY_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PROXY_PID_FILE"
            return 1
        fi
    fi
    return 1
}

start_proxy() {
    if check_proxy_running; then
        log_warning "MCP Proxy already running (PID: $(cat $PROXY_PID_FILE))"
        return 0
    fi
    
    log_info "Starting MCP Proxy..."
    
    if [[ ! -f "$PROXY_CONFIG" ]]; then
        log_error "Proxy config not found: $PROXY_CONFIG"
        log_info "Run: ./deploy_native_mcp.sh first"
        return 1
    fi
    
    cd "$MCP_STACK_DIR/proxy/src"
    nohup node dist/index.js --config ../config/native-stdio.json > ../logs/stdout.log 2> ../logs/stderr.log &
    local pid=$!
    echo "$pid" > "$PROXY_PID_FILE"
    
    # Wait a bit and check if it's still running
    sleep 3
    if kill -0 "$pid" 2>/dev/null; then
        log_success "MCP Proxy started (PID: $pid)"
        return 0
    else
        log_error "MCP Proxy failed to start. Check logs:"
        tail -10 "$MCP_STACK_DIR/proxy/logs/stderr.log"
        rm -f "$PROXY_PID_FILE"
        return 1
    fi
}

stop_proxy() {
    if ! check_proxy_running; then
        log_warning "MCP Proxy not running"
        return 0
    fi
    
    local pid=$(cat "$PROXY_PID_FILE")
    log_info "Stopping MCP Proxy (PID: $pid)..."
    
    kill "$pid"
    sleep 2
    
    if kill -0 "$pid" 2>/dev/null; then
        log_warning "Proxy still running, force killing..."
        kill -9 "$pid"
        sleep 1
    fi
    
    rm -f "$PROXY_PID_FILE"
    log_success "MCP Proxy stopped"
}

restart_proxy() {
    stop_proxy
    sleep 1
    start_proxy
}

status_proxy() {
    if check_proxy_running; then
        local pid=$(cat "$PROXY_PID_FILE")
        log_success "MCP Proxy is running (PID: $pid)"
        
        # Test health
        if python3 "$MCP_STACK_DIR/scripts/health_check.py" 2>/dev/null; then
            log_success "Health check passed"
        else
            log_warning "Health check failed"
        fi
    else
        log_error "MCP Proxy is not running"
        return 1
    fi
}

show_logs() {
    local log_type="${1:-stdout}"
    local lines="${2:-50}"
    
    case "$log_type" in
        "stdout"|"out")
            tail -"$lines" "$MCP_STACK_DIR/proxy/logs/stdout.log"
            ;;
        "stderr"|"err"|"error")
            tail -"$lines" "$MCP_STACK_DIR/proxy/logs/stderr.log"
            ;;
        "audit")
            tail -"$lines" "$MCP_STACK_DIR/proxy/logs/audit.log" 2>/dev/null || echo "No audit log found"
            ;;
        *)
            echo "Available logs: stdout, stderr, audit"
            ;;
    esac
}

test_tools() {
    log_info "Testing MCP tools..."
    
    if ! check_proxy_running; then
        log_error "Proxy not running. Start it first."
        return 1
    fi
    
    # Test list_tools
    local response=$(curl -s -X POST http://127.0.0.1:4010 \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":"test","method":"list_tools"}' \
        2>/dev/null || echo '{"error":"curl_failed"}')
    
    if echo "$response" | grep -q '"result"'; then
        local tool_count=$(echo "$response" | jq '.result.tools | length' 2>/dev/null || echo "unknown")
        log_success "list_tools works: $tool_count tools available"
        
        # Show namespaces
        local namespaces=$(echo "$response" | jq -r '.result.tools[].name' 2>/dev/null | cut -d. -f1 | sort -u | tr '\n' ' ' || echo "unknown")
        log_info "Available namespaces: $namespaces"
    else
        log_error "list_tools failed"
        echo "Response: $response"
        return 1
    fi
}

show_tools() {
    if ! check_proxy_running; then
        log_error "Proxy not running. Start it first."
        return 1
    fi
    
    log_info "Fetching available tools..."
    
    curl -s -X POST http://127.0.0.1:4010 \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":"tools","method":"list_tools"}' \
        2>/dev/null | jq '.result.tools[] | {name: .name, description: .description}' 2>/dev/null || {
        log_error "Failed to fetch tools"
        return 1
    }
}

load_service() {
    local plist="$HOME/Library/LaunchAgents/com.atlas.mcp-proxy.plist"
    
    if [[ ! -f "$plist" ]]; then
        log_error "Service plist not found. Run deployment script first."
        return 1
    fi
    
    if launchctl list | grep -q "com.atlas.mcp-proxy"; then
        log_warning "Service already loaded"
    else
        launchctl load "$plist"
        log_success "Service loaded into launchd"
    fi
}

unload_service() {
    if launchctl list | grep -q "com.atlas.mcp-proxy"; then
        launchctl unload "$HOME/Library/LaunchAgents/com.atlas.mcp-proxy.plist"
        log_success "Service unloaded from launchd"
    else
        log_warning "Service not loaded"
    fi
}

show_usage() {
    echo "MCP Stack Management Utility"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  start          Start MCP proxy"
    echo "  stop           Stop MCP proxy"
    echo "  restart        Restart MCP proxy"
    echo "  status         Show proxy status"
    echo "  logs [type]    Show logs (stdout, stderr, audit)"
    echo "  test           Test basic functionality"
    echo "  tools          List available tools"
    echo "  load-service   Load into launchd"
    echo "  unload-service Unload from launchd"
    echo "  help           Show this help"
    echo
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs stderr"
    echo "  $0 test"
}

main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    local command="$1"
    shift || true
    
    case "$command" in
        "start")
            start_proxy
            ;;
        "stop")
            stop_proxy
            ;;
        "restart")
            restart_proxy
            ;;
        "status")
            status_proxy
            ;;
        "logs")
            show_logs "$@"
            ;;
        "test")
            test_tools
            ;;
        "tools")
            show_tools
            ;;
        "load-service")
            load_service
            ;;
        "unload-service")
            unload_service
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
