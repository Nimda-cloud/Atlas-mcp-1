#!/bin/bash

# Atlas Autonomous System - macOS Installation Script
# This script installs and configures the Atlas system on macOS

set -e

echo "🤖 Atlas Autonomous System - macOS Installation"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This installation script is designed for macOS only."
    print_status "For other platforms, please use Docker or manual installation."
    exit 1
fi

print_success "Running on macOS - proceeding with installation"

# Check for Xcode Command Line Tools
print_status "Checking for Xcode Command Line Tools..."
if ! xcode-select -p &> /dev/null; then
    print_warning "Xcode Command Line Tools not found. Installing..."
    xcode-select --install
    print_status "Please follow the installation dialog and run this script again."
    exit 1
else
    print_success "Xcode Command Line Tools found"
fi

# Check for Homebrew
print_status "Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    print_success "Homebrew found"
fi

# Update Homebrew
print_status "Updating Homebrew..."
brew update

# Install Python 3.11 if not available
print_status "Checking Python installation..."
if ! command -v python3.11 &> /dev/null; then
    print_warning "Python 3.11 not found. Installing..."
    brew install python@3.11
else
    print_success "Python 3.11 found"
fi

# Install Ollama
print_status "Checking for Ollama..."
if ! command -v ollama &> /dev/null; then
    print_warning "Ollama not found. Installing..."
    brew install ollama
    
    # Start Ollama service
    print_status "Starting Ollama service..."
    brew services start ollama
    
    # Wait for Ollama to start
    sleep 5
    
    # Pull required model
    print_status "Pulling required LLM model (this may take a while)..."
    ollama pull llama3.1:8b-instruct
else
    print_success "Ollama found"
    
    # Ensure Ollama is running
    if ! pgrep -x "ollama" > /dev/null; then
        print_status "Starting Ollama service..."
        brew services start ollama
        sleep 5
    fi
    
    # Check if model is available
    if ! ollama list | grep -q "llama3.1:8b-instruct"; then
        print_status "Pulling required LLM model..."
        ollama pull llama3.1:8b-instruct
    fi
fi

# Install Docker (optional but recommended)
print_status "Checking for Docker..."
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found. Installing Docker Desktop..."
    brew install --cask docker
    print_status "Please start Docker Desktop manually and ensure it's running."
else
    print_success "Docker found"
fi

# Install Git (usually pre-installed on macOS)
print_status "Checking for Git..."
if ! command -v git &> /dev/null; then
    print_warning "Git not found. Installing..."
    brew install git
else
    print_success "Git found"
fi

# Create Atlas directory
ATLAS_DIR="$HOME/Atlas"
print_status "Creating Atlas directory at $ATLAS_DIR..."
mkdir -p "$ATLAS_DIR"
cd "$ATLAS_DIR"

# Clone or update Atlas repository (if this is being run from the repo)
if [[ -f "$(dirname "$0")/atlas_core.py" ]]; then
    print_status "Installing from local repository..."
    cp -r "$(dirname "$0")"/* "$ATLAS_DIR/"
else
    print_status "Repository files not found locally. Please ensure atlas_core.py and other files are in the same directory."
    exit 1
fi

# Create Python virtual environment
print_status "Creating Python virtual environment..."
python3.11 -m venv atlas_env
source atlas_env/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
print_status "Creating application directories..."
mkdir -p logs data/memory data/config data/models

# Create default configuration
print_status "Creating default configuration..."
cat > data/config/atlas_config.json << EOF
{
    "system": {
        "name": "Atlas Autonomous System",
        "version": "1.0.0",
        "platform": "macOS",
        "data_dir": "$ATLAS_DIR/data",
        "log_level": "INFO"
    },
    "llm": {
        "provider": "ollama",
        "api_base": "http://localhost:11434",
        "default_model": "llama3.1:8b-instruct",
        "temperature": 0.7,
        "max_tokens": 1000
    },
    "web": {
        "host": "127.0.0.1",
        "port": 8000,
        "auto_open": true
    },
    "automation": {
        "enabled": true,
        "safe_mode": true,
        "require_confirmation": true
    },
    "voice": {
        "tts_enabled": true,
        "stt_enabled": true,
        "voice_commands": true
    }
}
EOF

# Create startup script
print_status "Creating startup script..."
cat > start_atlas.sh << 'EOF'
#!/bin/bash

# Atlas Startup Script
cd "$HOME/Atlas"

# Activate virtual environment
source atlas_env/bin/activate

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama..."
    brew services start ollama
    sleep 5
fi

# Start Atlas
echo "🤖 Starting Atlas Autonomous System..."
python atlas_core.py

EOF

chmod +x start_atlas.sh

# Create macOS app bundle (optional)
print_status "Creating macOS application bundle..."
mkdir -p Atlas.app/Contents/MacOS
mkdir -p Atlas.app/Contents/Resources

cat > Atlas.app/Contents/Info.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Atlas</string>
    <key>CFBundleIdentifier</key>
    <string>com.atlas.autonomous</string>
    <key>CFBundleName</key>
    <string>Atlas Autonomous System</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
</dict>
</plist>
EOF

cat > Atlas.app/Contents/MacOS/Atlas << 'EOF'
#!/bin/bash
cd "$HOME/Atlas"
./start_atlas.sh
EOF

chmod +x Atlas.app/Contents/MacOS/Atlas

# Setup LaunchAgent for auto-start (optional)
read -p "Would you like Atlas to start automatically on login? (y/N): " AUTO_START
if [[ $AUTO_START =~ ^[Yy]$ ]]; then
    print_status "Setting up auto-start..."
    
    LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
    mkdir -p "$LAUNCH_AGENT_DIR"
    
    cat > "$LAUNCH_AGENT_DIR/com.atlas.autonomous.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.atlas.autonomous</string>
    <key>ProgramArguments</key>
    <array>
        <string>$ATLAS_DIR/start_atlas.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$ATLAS_DIR/logs/atlas.log</string>
    <key>StandardErrorPath</key>
    <string>$ATLAS_DIR/logs/atlas_error.log</string>
</dict>
</plist>
EOF

    launchctl load "$LAUNCH_AGENT_DIR/com.atlas.autonomous.plist"
    print_success "Auto-start configured"
fi

# Final setup
print_status "Performing final setup..."

# Test Ollama connection
if ollama list &> /dev/null; then
    print_success "Ollama is accessible and working"
else
    print_warning "Ollama connection test failed. Please check the installation."
fi

# Create desktop shortcut
ln -sf "$ATLAS_DIR/Atlas.app" "$HOME/Desktop/Atlas.app" 2>/dev/null || true

print_success "✅ Atlas Autonomous System installation completed!"
echo ""
echo "📋 Installation Summary:"
echo "   • Installation directory: $ATLAS_DIR"
echo "   • Startup script: $ATLAS_DIR/start_atlas.sh"
echo "   • Configuration: $ATLAS_DIR/data/config/atlas_config.json"
echo "   • Logs: $ATLAS_DIR/logs/"
echo ""
echo "🚀 To start Atlas:"
echo "   • Run: $ATLAS_DIR/start_atlas.sh"
echo "   • Or double-click Atlas.app on your Desktop"
echo "   • Or use Docker: docker-compose up -d"
echo ""
echo "🌐 Web interface will be available at: http://localhost:8000"
echo ""
echo "📖 For more information, see the README.md file"

# Ask if user wants to start Atlas now
read -p "Would you like to start Atlas now? (y/N): " START_NOW
if [[ $START_NOW =~ ^[Yy]$ ]]; then
    print_status "Starting Atlas..."
    ./start_atlas.sh
fi