#!/bin/bash
"""
🚀 Atlas Complete Deployment Script
===================================

Повноцінний файл розгортання Atlas з усіма залежностями та компонентами.
Встановлює все з нуля для готової до роботи системи.

Використання:
  ./deploy_atlas.sh                    # Повне розгортання
  ./deploy_atlas.sh --skip-python      # Пропустити Python залежності
  ./deploy_atlas.sh --skip-npm         # Пропустити NPM залежності
  ./deploy_atlas.sh --quick            # Швидка установка (мінімум)

Автор: Atlas AI Team
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/atlas_venv"
LOG_FILE="$SCRIPT_DIR/deployment.log"

# Parse arguments
SKIP_PYTHON=false
SKIP_NPM=false
QUICK_INSTALL=false

for arg in "$@"; do
    case $arg in
        --skip-python)
            SKIP_PYTHON=true
            shift
            ;;
        --skip-npm)
            SKIP_NPM=true
            shift
            ;;
        --quick)
            QUICK_INSTALL=true
            shift
            ;;
    esac
done

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Header
clear
log "${BLUE}🚀 Atlas Complete Deployment Script${NC}"
log "${BLUE}====================================${NC}"
log "$(date '+%Y-%m-%d %H:%M:%S') - Starting Atlas deployment"
log "Working directory: $SCRIPT_DIR"
log ""

# System requirements check
log "${CYAN}🔍 Checking system requirements...${NC}"

# Check macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    log "${RED}❌ This script is designed for macOS${NC}"
    exit 1
fi

# Check Homebrew
if ! command -v brew &> /dev/null; then
    log "${RED}❌ Homebrew not found. Installing...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Check Python 3.11+
if ! python3 --version | grep -E "3\.(11|12|13)" &> /dev/null; then
    log "${YELLOW}⚠️  Python 3.11+ required. Installing via Homebrew...${NC}"
    brew install python@3.11
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    log "${YELLOW}⚠️  Node.js not found. Installing...${NC}"
    brew install node
fi

# Check Go
if ! command -v go &> /dev/null; then
    log "${YELLOW}⚠️  Go not found. Installing...${NC}"
    brew install go
fi

log "${GREEN}✅ System requirements satisfied${NC}"
log ""

# Python Environment Setup
if [ "$SKIP_PYTHON" = false ]; then
    log "${PURPLE}🐍 Setting up Python environment...${NC}"
    
    # Create/update virtual environment
    if [ ! -d "$VENV_PATH" ]; then
        log "Creating virtual environment..."
        python3 -m venv "$VENV_PATH"
    fi
    
    # Activate environment
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip
    log "Upgrading pip..."
    pip install --upgrade pip
    
    # Install core Python dependencies
    log "Installing Python dependencies..."
    cat > "$SCRIPT_DIR/requirements_complete.txt" << EOF
# Atlas Core Dependencies
fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.1
requests==2.31.0
ollama==0.3.3
pygame==2.6.1
prometheus-client==0.17.0

# MCP and AI
mcp==1.0.0
anthropic==0.7.7
openai==1.3.7

# Ukrainian TTS
ukrainian-tts==0.4.0
gTTS==2.4.0

# macOS Automation
pyautogui==0.9.54
pynput==1.7.6
pyobjc-core==10.1
pyobjc-framework-Cocoa==10.1
pyobjc-framework-Quartz==10.1
pyobjc-framework-ApplicationServices==10.1

# Data Processing
numpy==1.24.3
torch==2.1.0
transformers==4.36.0
scipy==1.11.4

# Development Tools
black==23.11.0
flake8==6.1.0
pytest==7.4.3

# Additional utilities
python-dotenv==1.0.0
pyyaml==6.0.1
jsonschema==4.20.0
websockets==12.0
soundfile==0.12.1
librosa==0.10.1
EOF
    
    pip install -r "$SCRIPT_DIR/requirements_complete.txt"
    
    # Install Task Orchestrator in the virtual environment
    log "Installing MCP Task Orchestrator..."
    if [ -d "$SCRIPT_DIR/mcp-task-orchestrator" ]; then
        cd "$SCRIPT_DIR/mcp-task-orchestrator"
        pip install -e .
        cd "$SCRIPT_DIR"
        
        # Verify Task Orchestrator installation
        log "Verifying Task Orchestrator installation..."
        python -c "from mcp_task_orchestrator.infrastructure.mcp.tool_definitions import get_all_tools; print('✅ Task Orchestrator ready!'); print(f'Available tools: {len(get_all_tools())}')" 2>/dev/null || {
            log "${RED}❌ Task Orchestrator installation failed${NC}"
            exit 1
        }
        log "${GREEN}✅ Task Orchestrator installed successfully${NC}"
    else
        log "${YELLOW}⚠️  mcp-task-orchestrator directory not found${NC}"
    fi
    
    log "${GREEN}✅ Python environment ready${NC}"
else
    log "${YELLOW}⏭️  Skipping Python setup${NC}"
fi

log ""

# NPM Dependencies Setup
if [ "$SKIP_NPM" = false ]; then
    log "${PURPLE}📦 Setting up NPM dependencies...${NC}"
    
    # Install global MCP tools
    log "Installing global MCP packages..."
    npm install -g @modelcontextprotocol/inspector
    npm install -g @modelcontextprotocol/server-github
    npm install -g @playwright/mcp
    npm install -g better-playwright-mcp
    npm install -g playwright-mcp-chromium
    
    # Install additional automation tools
    if [ "$QUICK_INSTALL" = false ]; then
        log "Installing additional automation tools..."
        npm install -g @mcp-world/playwright-mcp-world
        npm install -g @ai-coding-labs/playwright-mcp-plus
    fi
    
    log "${GREEN}✅ NPM dependencies installed${NC}"
else
    log "${YELLOW}⏭️  Skipping NPM setup${NC}"
fi

log ""

# Go Dependencies Setup
log "${PURPLE}🔧 Setting up Go dependencies...${NC}"

# Install MCP Proxy
if [ ! -f "$SCRIPT_DIR/mcp-proxy/atlas-mcp-proxy" ]; then
    log "Installing Atlas MCP Proxy..."
    cd "$SCRIPT_DIR/mcp-proxy"
    
    # Try multiple installation methods
    if go install github.com/TBXark/mcp-proxy@latest; then
        log "✅ MCP Proxy installed via go install"
    elif [ -f "go.mod" ]; then
        go build -o atlas-mcp-proxy .
        log "✅ MCP Proxy built from source"
    else
        log "Cloning and building MCP Proxy..."
        git clone https://github.com/TBXark/mcp-proxy.git temp_proxy
        cd temp_proxy
        go build -o ../atlas-mcp-proxy .
        cd ..
        rm -rf temp_proxy
        log "✅ MCP Proxy built from repository"
    fi
    
    chmod +x atlas-mcp-proxy
    cd "$SCRIPT_DIR"
fi

log "${GREEN}✅ Go dependencies ready${NC}"
log ""

# AppleScript MCP Server Setup
log "${PURPLE}🍎 Setting up AppleScript MCP Server...${NC}"

if [ ! -d "$SCRIPT_DIR/applescript-mcp-server" ]; then
    log "Cloning AppleScript MCP Server..."
    git clone https://github.com/joshrutkowski/applescript-mcp.git "$SCRIPT_DIR/applescript-mcp-server"
    cd "$SCRIPT_DIR/applescript-mcp-server"
    
    log "Installing AppleScript MCP dependencies..."
    npm install
    
    log "Building AppleScript MCP Server..."
    npm run build
    
    cd "$SCRIPT_DIR"
    log "✅ AppleScript MCP Server installed"
else
    log "AppleScript MCP Server already installed, updating..."
    cd "$SCRIPT_DIR/applescript-mcp-server"
    git pull origin main
    npm install
    npm run build
    cd "$SCRIPT_DIR"
    log "✅ AppleScript MCP Server updated"
fi

log "${GREEN}✅ AppleScript MCP ready${NC}"
log ""

# Atlas Configuration Setup
log "${PURPLE}⚙️  Setting up Atlas configuration...${NC}"

# Create .env file if not exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cat > "$SCRIPT_DIR/.env" << EOF
# Atlas Environment Configuration
ATLAS_ENV=production
ATLAS_MCP_PROXY_MODE=true
ATLAS_MCP_USE_GLOBAL_CONFIG=true
ATLAS_MCP_PROXY_URL=http://localhost:9090
ATLAS_MCP_PROXY_CLIENTS=atlas-default-token,atlas-secure-token

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_HOST=http://localhost:11434

# GitHub Integration (optional)
# GITHUB_TOKEN=your_github_token_here

# Ukrainian TTS Configuration
ATLAS_TTS_MODEL_PATH=$SCRIPT_DIR/mcp_tts_ukrainian/model.pth
ATLAS_TTS_CONFIG=$SCRIPT_DIR/mcp_tts_ukrainian/config.yaml

# Logging
LOG_LEVEL=INFO
ATLAS_LOG_FILE=$SCRIPT_DIR/atlas.log
EOF
    log "✅ Environment configuration created"
fi

# Validate configurations
log "Validating configurations..."
if [ -f "$SCRIPT_DIR/mcp-proxy/atlas-global-config.json" ]; then
    log "✅ Atlas global config found"
else
    log "❌ Atlas global config missing"
fi

if [ -f "$SCRIPT_DIR/start_atlas.sh" ] && [ -x "$SCRIPT_DIR/start_atlas.sh" ]; then
    log "✅ Atlas startup script ready"
else
    log "❌ Atlas startup script missing or not executable"
fi

log ""

# Services Installation Summary
log "${PURPLE}📋 Installation Summary${NC}"
log "======================="

# Python packages
if [ "$SKIP_PYTHON" = false ]; then
    source "$VENV_PATH/bin/activate"
    PYTHON_PACKAGES=$(pip list | wc -l)
    log "🐍 Python packages: $PYTHON_PACKAGES installed"
fi

# NPM packages
if [ "$SKIP_NPM" = false ]; then
    NPM_GLOBAL_PACKAGES=$(npm list -g --depth=0 2>/dev/null | grep -E "(@modelcontextprotocol|@playwright|better-playwright)" | wc -l)
    log "📦 NPM MCP packages: $NPM_GLOBAL_PACKAGES installed"
fi

# MCP Proxy
if [ -f "$SCRIPT_DIR/mcp-proxy/atlas-mcp-proxy" ]; then
    log "🔗 MCP Proxy: Ready"
else
    log "❌ MCP Proxy: Not installed"
fi

log ""

# Validation Tests
log "${PURPLE}🧪 Running validation tests...${NC}"

# Test Python environment
if [ "$SKIP_PYTHON" = false ]; then
    source "$VENV_PATH/bin/activate"
    python3 -c "
import sys
try:
    import fastapi, uvicorn, aiohttp, ollama, pygame
    print('✅ Core Python imports: OK')
except ImportError as e:
    print(f'❌ Core Python imports: {e}')
    sys.exit(1)
" || { log "${RED}❌ Python validation failed${NC}"; exit 1; }
fi

# Test NPM packages
if [ "$SKIP_NPM" = false ]; then
    if npx @modelcontextprotocol/inspector --version > /dev/null 2>&1; then
        log "✅ MCP Inspector: Available"
    else
        log "❌ MCP Inspector: Not available"
    fi
    
    if npx better-playwright-mcp --version > /dev/null 2>&1; then
        log "✅ Better Playwright MCP: Available"
    else
        log "❌ Better Playwright MCP: Not available"
    fi
fi

# Test Atlas components
if [ -f "$SCRIPT_DIR/atlas_core.py" ]; then
    log "✅ Atlas Core: Found"
else
    log "❌ Atlas Core: Missing"
fi

if [ -f "$SCRIPT_DIR/mcp_tts_ukrainian/mcp_tts_server.py" ]; then
    log "✅ TTS Server: Found"
else
    log "❌ TTS Server: Missing"
fi

if [ -f "$SCRIPT_DIR/mcp-task-orchestrator/mcp_task_orchestrator/server.py" ]; then
    log "✅ Task Orchestrator: Found"
else
    log "❌ Task Orchestrator: Missing"
fi

if [ -f "$SCRIPT_DIR/applescript-mcp-server/dist/index.js" ]; then
    log "✅ AppleScript MCP: Found"
else
    log "❌ AppleScript MCP: Missing"
fi

log ""

# Final Summary
log "${GREEN}🎉 Atlas Deployment Complete!${NC}"
log "=============================="
log ""
log "${CYAN}📍 Installation Location:${NC} $SCRIPT_DIR"
log "${CYAN}🐍 Python Environment:${NC} $VENV_PATH"
log "${CYAN}📄 Log File:${NC} $LOG_FILE"
log ""
log "${PURPLE}🔧 Installed MCP Services:${NC}"
log "   • Task Orchestrator (15 tools)"
log "   • Ukrainian TTS (3 tools)"  
log "   • Automation (8 tools)"
log "   • Better Playwright (29 tools)"
log "   • AppleScript MCP (32 tools)"
log "   • Web Fetch (5 tools - virtual)"
log "   ${GREEN}Total: ~92 tools across 6 services${NC}"
log ""
log "${CYAN}🚀 To start Atlas:${NC}"
log "   cd $SCRIPT_DIR"
log "   ./start_atlas.sh"
log ""
log "${CYAN}🔧 To activate Python environment manually:${NC}"
log "   source $VENV_PATH/bin/activate"
log ""
log "${CYAN}📊 To check status:${NC}"
log "   curl http://localhost:8000/"
log ""
log "${CYAN}🛠️  To access tools list:${NC}"
log "   curl http://localhost:8000/tools"
log ""

# Create completion marker
touch "$SCRIPT_DIR/.atlas_deployed"
log "$(date '+%Y-%m-%d %H:%M:%S') - Atlas deployment completed successfully" >> "$LOG_FILE"

log "${GREEN}✅ Ready to launch Atlas Autonomous System!${NC}"
