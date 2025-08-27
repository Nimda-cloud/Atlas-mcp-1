#!/bin/bash

# Atlas Environment Setup Script
# ==============================
# 
# This script sets up and validates the Atlas virtual environment.
# Run this before starting the Atlas system to ensure all dependencies are available.
# 
# Оновлено: 2025-08-26 - Актуалізовано перевірки та залежності

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Atlas Environment Setup${NC}"
echo "=================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/atlas_venv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment not found at: $VENV_PATH${NC}"
    echo -e "${YELLOW}Creating new virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo -e "${YELLOW}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Check and install Neo4j if needed
echo -e "${YELLOW}🗄️ Checking Neo4j installation...${NC}"
if ! command -v neo4j &> /dev/null; then
    echo -e "${YELLOW}📦 Neo4j not found. Installing via Homebrew...${NC}"
    if command -v brew &> /dev/null; then
        brew install neo4j
        echo -e "${GREEN}✅ Neo4j installed successfully${NC}"
    else
        echo -e "${RED}❌ Homebrew not found. Please install Neo4j manually:${NC}"
        echo "  1. Install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "  2. Install Neo4j: brew install neo4j"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Neo4j already installed${NC}"
fi

# Start Neo4j service if not running
echo -e "${YELLOW}🔧 Checking Neo4j service...${NC}"
if ! brew services list | grep neo4j | grep -q started; then
    echo -e "${YELLOW}🚀 Starting Neo4j service...${NC}"
    brew services start neo4j
    echo -e "${GREEN}✅ Neo4j service started${NC}"
    
    # Wait for Neo4j to start
    echo -e "${YELLOW}⏳ Waiting for Neo4j to initialize...${NC}"
    sleep 10
else
    echo -e "${GREEN}✅ Neo4j service already running${NC}"
fi

# Validate key imports
echo -e "${YELLOW}🔍 Validating key imports...${NC}"
python3 -c "
import sys
errors = []

# Test core imports
try:
    import fastapi
    import uvicorn
    import aiohttp
    import ollama
    import pygame
    import requests
    print('✅ Core imports: OK')
except ImportError as e:
    errors.append(f'Core imports: {e}')

# Test Ukrainian TTS (optional)
try:
    import ukrainian_tts
    print('✅ Ukrainian TTS: Available')
except ImportError:
    print('⚠️  Ukrainian TTS: Not available (можна встановити окремо)')

# Test TTS fallbacks
try:
    import pyttsx3
    import gtts
    print('✅ TTS Fallbacks: OK')
except ImportError as e:
    errors.append(f'TTS fallbacks: {e}')

# Test macOS frameworks
try:
    import pyautogui
    import pynput
    import psutil
    print('✅ System automation: OK')
except ImportError as e:
    errors.append(f'System automation: {e}')

# Test macOS specific (optional)
try:
    import objc
    print('✅ macOS PyObjC: Available')
except ImportError:
    print('⚠️  macOS PyObjC: Not available (optional)')

# Test AppleScript (optional)
try:
    import applescript
    print('✅ AppleScript: Available')
except ImportError:
    print('⚠️  AppleScript: Not available (optional)')

if errors:
    print('\\n❌ Critical import errors:')
    for error in errors:
        print(f'  - {error}')
    sys.exit(1)
else:
    print('\\n🎉 All critical imports successful!')
"

echo -e "${GREEN}✅ Environment setup complete!${NC}"
echo ""
echo "To activate the environment manually:"
echo "  source $VENV_PATH/bin/activate"
echo ""
echo "To start Atlas:"
echo "  ./start_atlas.sh"
