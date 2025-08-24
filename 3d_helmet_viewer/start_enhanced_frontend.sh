#!/bin/bash

echo "🚀 Starting Atlas Enhanced 3D Frontend..."

# Check if we're in the right directory
if [ ! -f "enhanced_frontend_simple.html" ]; then
    echo "❌ Error: enhanced_frontend_simple.html not found"
    echo "Please run this script from the 3d_helmet_viewer directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Install required packages if not available
echo "📦 Installing required packages..."
pip3 install fastapi uvicorn aiohttp python-multipart websockets 2>/dev/null || {
    echo "⚠️  Warning: Could not install packages via pip. Using fallback server..."
}

# Check if enhanced_server.py exists
if [ -f "enhanced_server.py" ]; then
    echo "🌐 Starting enhanced server with full integration..."
    python3 enhanced_server.py
else
    echo "🌐 Starting simple HTTP server..."
    python3 -m http.server 8080
fi