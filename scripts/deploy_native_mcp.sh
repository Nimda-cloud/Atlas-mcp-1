#!/bin/bash
set -euo pipefail

# Native MCP Stack Deployment Script
# Автоматическое развертывание полностью нативного MCP стека

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_STACK_DIR="$HOME/mcp-stack"
CURRENT_USER="$(whoami)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking system dependencies..."
    
    # Check Homebrew
    if ! command -v brew &> /dev/null; then
        log_error "Homebrew not found. Install from https://brew.sh"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_warning "Node.js not found. Installing..."
        brew install node@22
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_warning "Python 3 not found. Installing..."
        brew install python@3.12
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        log_error "Git not found. Install Xcode Command Line Tools"
        exit 1
    fi
    
    log_success "Dependencies check completed"
}

setup_directories() {
    log_info "Setting up directory structure..."
    
    mkdir -p "$MCP_STACK_DIR"/{applescript,automator,automation,playwright,tts,vnc,proxy}/{logs,config}
    mkdir -p "$MCP_STACK_DIR"/proxy/{keys,cache}
    mkdir -p "$MCP_STACK_DIR"/venvs
    mkdir -p "$MCP_STACK_DIR"/scripts
    mkdir -p "$MCP_STACK_DIR"/backups
    
    log_success "Directory structure created"
}

setup_ssh_keys() {
    log_info "Setting up SSH keys for AppleScript..."
    
    SSH_KEY="$HOME/.ssh/mcp_internal"
    if [[ ! -f "$SSH_KEY" ]]; then
        ssh-keygen -t ed25519 -f "$SSH_KEY" -N '' -C "mcp-internal-$(date +%s)"
        cat "${SSH_KEY}.pub" >> "$HOME/.ssh/authorized_keys"
        chmod 600 "$HOME/.ssh/authorized_keys"
        log_success "SSH keys created and authorized"
    else
        log_info "SSH keys already exist"
    fi
}

install_applescript_mcp() {
    log_info "Installing AppleScript MCP..."
    
    cd "$MCP_STACK_DIR/applescript"
    if [[ ! -f "package.json" ]]; then
        npm init -y
        npm install @peakmojo/applescript-mcp
        log_success "AppleScript MCP installed"
    else
        log_info "AppleScript MCP already installed"
    fi
}

install_automator_mcp() {
    log_info "Installing macOS Automator MCP..."
    
    if [[ ! -d "$MCP_STACK_DIR/automator/src" ]]; then
        cd "$MCP_STACK_DIR/automator"
        git clone https://github.com/steipete/macos-automator-mcp.git src
        
        python3 -m venv "$MCP_STACK_DIR/venvs/automator"
        source "$MCP_STACK_DIR/venvs/automator/bin/activate"
        pip install -r src/requirements.txt
        
        log_success "macOS Automator MCP installed"
    else
        log_info "macOS Automator MCP already installed"
    fi
}

install_automation_mcp() {
    log_info "Installing Automation MCP..."
    
    if [[ ! -d "$MCP_STACK_DIR/automation/src" ]]; then
        cd "$MCP_STACK_DIR/automation"
        git clone https://github.com/ashwwwin/automation-mcp.git src
        cd src && npm install
        
        log_success "Automation MCP installed"
    else
        log_info "Automation MCP already installed"
    fi
}

install_playwright_mcp() {
    log_info "Installing Playwright MCP..."
    
    if [[ ! -d "$MCP_STACK_DIR/playwright/src" ]]; then
        cd "$MCP_STACK_DIR/playwright"
        git clone https://github.com/microsoft/playwright-mcp.git src
        cd src && npm install
        npx playwright install
        
        log_success "Playwright MCP installed"
    else
        log_info "Playwright MCP already installed"
    fi
}

install_tts_mcp() {
    log_info "Installing TTS MCP with Ukrainian support..."
    
    if [[ ! -d "$MCP_STACK_DIR/tts/src" ]]; then
        cd "$MCP_STACK_DIR/tts"
        git clone https://github.com/blacktop/mcp-tts.git src
        
        python3 -m venv "$MCP_STACK_DIR/venvs/tts"
        source "$MCP_STACK_DIR/venvs/tts/bin/activate"
        pip install -r src/requirements.txt
        
        # Try to install Ukrainian TTS (may fail, that's ok)
        if pip install ukrainian-tts; then
            log_success "Ukrainian TTS installed"
        else
            log_warning "Ukrainian TTS installation failed, skipping"
        fi
        
        log_success "TTS MCP installed"
    else
        log_info "TTS MCP already installed"
    fi
}

install_vnc_mcp() {
    log_info "Installing VNC MCP..."
    
    cd "$MCP_STACK_DIR/vnc"
    if [[ ! -f "package.json" ]]; then
        npm init -y
        npm install @hrrrsn/mcp-vnc
        log_success "VNC MCP installed"
    else
        log_info "VNC MCP already installed"
    fi
}

install_mcp_proxy() {
    log_info "Installing MCP Proxy..."
    
    if [[ ! -d "$MCP_STACK_DIR/proxy/src" ]]; then
        cd "$MCP_STACK_DIR/proxy"
        git clone https://github.com/TBXark/mcp-proxy.git src
        cd src && npm install && npm run build
        
        log_success "MCP Proxy installed"
    else
        log_info "MCP Proxy already installed"
    fi
}

create_proxy_config() {
    log_info "Creating proxy configuration..."
    
    CONFIG_FILE="$MCP_STACK_DIR/proxy/config/native-stdio.json"
    
    cat > "$CONFIG_FILE" << EOF
{
  "description": "Полностью нативный MCP стек - только stdio процессы",
  "servers": [
    {
      "name": "applescript",
      "type": "stdio",
      "command": "npx",
      "args": ["@peakmojo/applescript-mcp"],
      "cwd": "$MCP_STACK_DIR/applescript",
      "env": {
        "SSH_IDENTITY_FILE": "$HOME/.ssh/mcp_internal",
        "REMOTE_HOST": "127.0.0.1",
        "REMOTE_USER": "$CURRENT_USER"
      },
      "namespace": "as",
      "restart": true,
      "timeout": 30000
    },
    {
      "name": "automator", 
      "type": "stdio",
      "command": "$MCP_STACK_DIR/venvs/automator/bin/python",
      "args": ["$MCP_STACK_DIR/automator/src/main.py"],
      "namespace": "macos",
      "restart": true
    },
    {
      "name": "automation",
      "type": "stdio", 
      "command": "node",
      "args": ["index.js"],
      "cwd": "$MCP_STACK_DIR/automation/src",
      "namespace": "sys",
      "restart": true
    },
    {
      "name": "playwright",
      "type": "stdio",
      "command": "node", 
      "args": ["dist/index.js"],
      "cwd": "$MCP_STACK_DIR/playwright/src",
      "namespace": "browser",
      "restart": true,
      "timeout": 45000
    },
    {
      "name": "tts",
      "type": "stdio",
      "command": "$MCP_STACK_DIR/venvs/tts/bin/python",
      "args": ["$MCP_STACK_DIR/tts/src/main.py"],
      "namespace": "voice",
      "restart": true,
      "optional": true
    },
    {
      "name": "vnc_local",
      "type": "stdio",
      "command": "npx",
      "args": ["@hrrrsn/mcp-vnc"],
      "cwd": "$MCP_STACK_DIR/vnc",
      "env": {
        "VNC_HOST": "127.0.0.1",
        "VNC_PORT": "5900"
      },
      "namespace": "vnc",
      "restart": true,
      "optional": true
    }
  ],
  "proxy": {
    "port": 4010,
    "host": "127.0.0.1",
    "logLevel": "info",
    "maxConcurrentCalls": 12,
    "requestTimeoutMs": 60000
  },
  "features": {
    "namespacing": true,
    "toolAlias": {
      "browser.screenshot": "page_screenshot",
      "vnc.vnc_screenshot": "desktop_screenshot",
      "voice.tts_ukrainian": "speak_ukrainian"
    },
    "fallback": {
      "enabled": true,
      "order": ["as", "macos", "browser", "vnc_local"]
    },
    "auditLog": {
      "enabled": true,
      "path": "$MCP_STACK_DIR/proxy/logs/audit.log",
      "rotation": {
        "maxSize": "10MB",
        "maxFiles": 5
      }
    }
  }
}
EOF
    
    log_success "Proxy configuration created"
}

create_health_check() {
    log_info "Creating health check script..."
    
    cat > "$MCP_STACK_DIR/scripts/health_check.py" << 'EOF'
#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import sys

async def check_proxy_health():
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"jsonrpc": "2.0", "id": "health", "method": "list_tools"}
            async with session.post("http://127.0.0.1:4010", json=payload, timeout=10) as resp:
                if resp.status != 200:
                    return False, f"HTTP {resp.status}"
                
                result = await resp.json()
                tools = result.get('result', {}).get('tools', [])
                
                namespaces = set()
                for tool in tools:
                    if '.' in tool['name']:
                        namespaces.add(tool['name'].split('.')[0])
                
                expected = {'as', 'macos', 'sys', 'browser'}
                missing = expected - namespaces
                
                if missing:
                    return False, f"Missing critical namespaces: {missing}"
                
                return True, f"OK: {len(tools)} tools, namespaces: {sorted(namespaces)}"
                
    except Exception as e:
        return False, f"Error: {e}"

async def main():
    success, message = await check_proxy_health()
    print(f"MCP Proxy Health: {message}")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    chmod +x "$MCP_STACK_DIR/scripts/health_check.py"
    log_success "Health check script created"
}

create_launchd_service() {
    log_info "Creating launchd service..."
    
    PLIST_FILE="$HOME/Library/LaunchAgents/com.atlas.mcp-proxy.plist"
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.atlas.mcp-proxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>node</string>
        <string>dist/index.js</string>
        <string>--config</string>
        <string>../config/native-stdio.json</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$MCP_STACK_DIR/proxy/src</string>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$MCP_STACK_DIR/proxy/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$MCP_STACK_DIR/proxy/logs/stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
EOF
    
    log_success "launchd service created (not loaded yet)"
}

create_start_script() {
    log_info "Creating start script..."
    
    cat > "$MCP_STACK_DIR/scripts/start_proxy.sh" << EOF
#!/bin/bash
cd "$MCP_STACK_DIR/proxy/src"
node dist/index.js --config ../config/native-stdio.json
EOF
    
    chmod +x "$MCP_STACK_DIR/scripts/start_proxy.sh"
    log_success "Start script created"
}

run_basic_tests() {
    log_info "Running basic installation tests..."
    
    # Test if key components are installed
    if [[ -f "$MCP_STACK_DIR/applescript/package.json" ]] && \
       [[ -d "$MCP_STACK_DIR/automator/src" ]] && \
       [[ -d "$MCP_STACK_DIR/proxy/src/dist" ]]; then
        log_success "All components installed successfully"
    else
        log_error "Some components missing. Check installation logs."
        return 1
    fi
}

show_next_steps() {
    log_info "Installation completed! Next steps:"
    echo
    echo "1. Enable Screen Sharing (for VNC):"
    echo "   System Settings → General → Sharing → Screen Sharing"
    echo
    echo "2. Grant Accessibility permissions:"
    echo "   System Settings → Privacy & Security → Accessibility"
    echo "   Add Terminal/iTerm and grant access"
    echo
    echo "3. Start the MCP proxy:"
    echo "   $MCP_STACK_DIR/scripts/start_proxy.sh"
    echo
    echo "4. Test the installation:"
    echo "   python3 $MCP_STACK_DIR/scripts/health_check.py"
    echo
    echo "5. Load as system service (optional):"
    echo "   launchctl load ~/Library/LaunchAgents/com.atlas.mcp-proxy.plist"
    echo
    echo "6. Update Atlas configuration:"
    echo "   ATLAS_MCP_PROXY_MODE=true"
    echo "   ATLAS_MCP_PROXY_URL=http://127.0.0.1:4010"
    echo
    log_success "Setup complete! MCP stack ready for native deployment."
}

main() {
    log_info "Starting Native MCP Stack deployment..."
    
    check_dependencies
    setup_directories
    setup_ssh_keys
    install_applescript_mcp
    install_automator_mcp
    install_automation_mcp
    install_playwright_mcp
    install_tts_mcp
    install_vnc_mcp
    install_mcp_proxy
    create_proxy_config
    create_health_check
    create_launchd_service
    create_start_script
    run_basic_tests
    show_next_steps
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
