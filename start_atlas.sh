#!/bin/bash

# Atlas Autonomous System - Quick Start Script
# This script provides an easy way to start the Atlas system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "🤖 Atlas Autonomous System"
    echo "=========================="
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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for service to be ready
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

print_header

# Parse command line arguments
MODE=""
BACKGROUND=false
NO_BROWSER=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            MODE="docker"
            shift
            ;;
        --local)
            MODE="local"
            shift
            ;;
        --background|-b)
            BACKGROUND=true
            shift
            ;;
        --no-browser)
            NO_BROWSER=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --docker      Run using Docker Compose"
            echo "  --local       Run locally with Python"
            echo "  --background  Run in background"
            echo "  --no-browser  Don't open browser automatically"
            echo "  --help        Show this help message"
            echo ""
            echo "If no mode is specified, will auto-detect best option."
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Auto-detect mode if not specified
if [ -z "$MODE" ]; then
    if command_exists docker && command_exists docker-compose && [ -f "docker-compose.yml" ]; then
        MODE="docker"
        print_status "Auto-detected Docker environment"
    elif command_exists python3 && [ -f "atlas_core.py" ]; then
        MODE="local"
        print_status "Auto-detected local Python environment"
    else
        print_error "Could not detect how to run Atlas. Please specify --docker or --local"
        exit 1
    fi
fi

# Pre-flight checks
print_status "Performing pre-flight checks..."

# Load .env if present
if [ -f .env ]; then
    print_status "Loading environment from .env"
    # shellcheck disable=SC2046
    set -a; source ./.env; set +a
fi

if [ "$MODE" = "docker" ]; then
    if ! command_exists docker; then
        print_error "Docker is required but not installed"
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is required but not installed"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    print_success "Docker environment ready"

elif [ "$MODE" = "local" ]; then
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! command_exists ollama; then
        print_error "Ollama is required but not installed. Please install from https://ollama.ai"
        exit 1
    fi
    
    # Determine Ollama URL
    OLLAMA_URL_ENV=${OLLAMA_URL:-}
    if [ -z "$OLLAMA_URL_ENV" ] && [ -n "$OLLAMA_HOST" ]; then
        OLLAMA_URL_ENV="http://$OLLAMA_HOST"
    fi
    OLLAMA_URL_ENV=${OLLAMA_URL_ENV:-http://localhost:11434}

    # Check if Ollama is running
    if ! curl -s "$OLLAMA_URL_ENV/api/tags" >/dev/null 2>&1; then
        print_warning "Ollama is not running. Starting Ollama..."
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command_exists brew; then
                brew services start ollama
            else
                ollama serve &
            fi
        else
            # Linux/other
            ollama serve &
        fi
        
        print_status "Waiting for Ollama to start..."
        if ! wait_for_service "$OLLAMA_URL_ENV/api/tags"; then
            print_error "Failed to start Ollama"
            exit 1
        fi
    fi
    
    # Ensure at least one supported model is available (prefer env-configured)
    PREFERRED_MODELS=()
    [ -n "$ATLAS_LLM1_MODEL" ] && PREFERRED_MODELS+=("$ATLAS_LLM1_MODEL")
    [ -n "$ATLAS_LLM2_MODEL" ] && PREFERRED_MODELS+=("$ATLAS_LLM2_MODEL")
    [ -n "$ATLAS_LLM3_MODEL" ] && PREFERRED_MODELS+=("$ATLAS_LLM3_MODEL")
    # Fallbacks commonly available locally
    PREFERRED_MODELS+=("gpt-oss:latest" "llama3.1:8b" "llama3:latest" "mistral:latest")

    if ! ollama list | awk '{print $1}' | grep -Eq "^("$(printf "%s|" "${PREFERRED_MODELS[@]}" | sed 's/|$//')")$"; then
        for m in "${PREFERRED_MODELS[@]}"; do
            print_warning "Model $m not found locally. Attempting to pull..."
            if ollama pull "$m"; then
                print_success "Pulled model: $m"
                break
            fi
        done
    fi
    
    print_success "Local environment ready"
fi

# Check for port conflicts
if port_in_use 8000; then
    print_warning "Port 8000 is already in use. Atlas web interface may not be accessible."
    print_status "You can change the port by setting ATLAS_WEB_PORT environment variable"
fi

# Start Atlas
print_status "Starting Atlas Autonomous System in $MODE mode..."

if [ "$MODE" = "docker" ]; then
    # Docker mode with profiles and health waits
    CMD=(docker compose --profile monitoring --profile mcp --profile macos up)
    if [ "$BACKGROUND" = true ]; then
        CMD+=(-d)
    fi
    print_status "Starting Atlas stack (monitoring + mcp + macos profiles)..."
    "${CMD[@]}"

    # Wait for key services
    print_status "Waiting for services to become healthy..."
    wait_for_service "http://localhost:8000/status" || print_warning "atlas-core not responding yet"
    wait_for_service "http://localhost:8080/health" || print_warning "frontend not responding yet"
    wait_for_service "http://localhost:4002/health" || print_warning "mcp-automation not responding yet"
    wait_for_service "http://localhost:4003/health" || print_warning "mcp-automator not responding yet"
    wait_for_service "http://localhost:4004/health" || print_warning "tts mcp not responding yet"
    wait_for_service "http://localhost:4005/mcp" || print_warning "playwright mcp not responding yet"

elif [ "$MODE" = "local" ]; then
    # Local mode
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "atlas_env" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv atlas_env
    fi
    
    # Activate virtual environment
    source atlas_env/bin/activate
    
    # Install dependencies if needed
    if [ ! -f "atlas_env/.deps_installed" ]; then
        print_status "Installing Python dependencies..."
        pip install --upgrade pip
        pip install -r requirements.txt
        touch atlas_env/.deps_installed
    fi
    
    # Create data directories
    mkdir -p data/memory data/config data/logs
    
    # Start Atlas
    if [ "$BACKGROUND" = true ]; then
        print_status "Starting Atlas in background..."
        nohup python atlas_core.py > data/logs/atlas.log 2>&1 &
        ATLAS_PID=$!
        echo $ATLAS_PID > data/atlas.pid
        print_success "Atlas started in background (PID: $ATLAS_PID)"
        print_status "View logs with: tail -f data/logs/atlas.log"
    else
        print_status "Starting Atlas (press Ctrl+C to stop)..."
        python atlas_core.py
    fi
fi

# Wait a moment for the service to start
if [ "$BACKGROUND" = true ]; then
    sleep 3
    
    # Check if Atlas is responding
    if wait_for_service "http://localhost:8000/status"; then
        print_success "Atlas is running and responding"
        
        # Open browser if requested
        if [ "$NO_BROWSER" = false ]; then
            print_status "Opening Atlas dashboard in browser..."
            if command_exists open; then
                # macOS
                open http://localhost:8000
            elif command_exists xdg-open; then
                # Linux
                xdg-open http://localhost:8000
            elif command_exists start; then
                # Windows
                start http://localhost:8000
            else
                print_status "Please open http://localhost:8000 in your browser"
            fi
        fi
        
        echo ""
        print_success "✅ Atlas Autonomous System is ready!"
        echo ""
        echo "📋 Quick Info:"
        echo "   • Web Interface: http://localhost:8000"
        echo "   • API Docs: http://localhost:8000/docs"
        echo "   • Status: http://localhost:8000/status"
        echo ""
        echo "🛑 To stop Atlas:"
        if [ "$MODE" = "docker" ]; then
            echo "   docker-compose down"
        else
            echo "   kill \$(cat data/atlas.pid) # or press Ctrl+C if running in foreground"
        fi
        echo ""
        
    else
        print_error "Atlas failed to start properly"
        exit 1
    fi
fi