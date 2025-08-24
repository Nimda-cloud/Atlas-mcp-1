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