#!/bin/bash
set -e

echo "🤖 Starting Atlas Autonomous System..."

# Start Ollama in the background if not already running
if ! pgrep -x "ollama" > /dev/null; then
    echo "📦 Starting Ollama server..."
    ollama serve &
    
    # Wait for Ollama to be ready
    echo "⏳ Waiting for Ollama to be ready..."
    sleep 10
    
    # Pull required models if not already available
    echo "📥 Pulling required LLM models..."
    ollama pull llama3.1:8b-instruct || echo "⚠️  Failed to pull llama3.1:8b-instruct, will try at runtime"
fi

# Create data directories
mkdir -p /app/data/memory /app/data/logs /app/data/config

# Set up configuration if not exists
if [ ! -f "/app/data/config/agents.json" ]; then
    echo "⚙️  Creating default agent configuration..."
    cat > /app/data/config/agents.json << EOF
{
  "agents": [
    {
      "name": "Atlas-Interface",
      "provider": "ollama",
      "model": "llama3.1:8b-instruct",
      "role": "interface",
      "skills": ["conversation", "memory", "user_interaction"]
    },
    {
      "name": "Atlas-Orchestrator", 
      "provider": "ollama",
      "model": "llama3.1:8b-instruct",
      "role": "orchestrator",
      "skills": ["planning", "task_execution", "automation"]
    },
    {
      "name": "Atlas-Monitor",
      "provider": "ollama", 
      "model": "llama3.1:8b-instruct",
      "role": "monitor",
      "skills": ["system_monitoring", "security", "anomaly_detection"]
    }
  ]
}
EOF
fi

echo "🚀 Starting Atlas application..."

# Execute the main command
exec "$@"