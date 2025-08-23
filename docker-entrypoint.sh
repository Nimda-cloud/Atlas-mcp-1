#!/bin/bash
set -e

echo "🤖 Starting Atlas Autonomous System..."

# Derive Ollama API base (inside container)
export OLLAMA_HOST="${OLLAMA_HOST:-0.0.0.0:11434}"
if [[ -n "${OLLAMA_URL}" ]]; then
  OLLAMA_API="${OLLAMA_URL}"
else
  # If OLLAMA_HOST lacks scheme, prepend http://
  if [[ "${OLLAMA_HOST}" != http* ]]; then
    OLLAMA_API="http://${OLLAMA_HOST}"
  else
    OLLAMA_API="${OLLAMA_HOST}"
  fi
fi

# Resolve desired models from env with sensible fallbacks
MODEL1="${ATLAS_LLM1_MODEL:-${ATLAS_LLM_MODEL:-llama3.1:8b}}"
MODEL2="${ATLAS_LLM2_MODEL:-${ATLAS_LLM_MODEL:-gpt-oss:latest}}"
MODEL3="${ATLAS_LLM3_MODEL:-${ATLAS_LLM_MODEL:-llama3.1:8b}}"

# Build a unique list of models to pull, plus global fallbacks
FALLBACK_MODELS=("gpt-oss:latest" "llama3.1:8b" "llama3:latest" "mistral:latest")
MODELS_TO_PULL=()
for m in "$MODEL1" "$MODEL2" "$MODEL3"; do
  [[ -n "$m" ]] && MODELS_TO_PULL+=("$m")
done
for fm in "${FALLBACK_MODELS[@]}"; do
  # De-duplicate
  if [[ ! " ${MODELS_TO_PULL[*]} " =~ " ${fm} " ]]; then
    MODELS_TO_PULL+=("$fm")
  fi
done

# Decide whether to run embedded Ollama or use external (host) Ollama.
# If OLLAMA_URL is set (e.g., http://host.docker.internal:11434), we will not start embedded Ollama.
USE_EMBEDDED_OLLAMA=${USE_EMBEDDED_OLLAMA:-}
if [[ -z "${OLLAMA_URL}" && "${USE_EMBEDDED_OLLAMA}" == "true" ]]; then
  # Start embedded Ollama only when explicitly requested
  if ! pgrep -x "ollama" >/dev/null 2>&1; then
      echo "📦 Starting embedded Ollama server on ${OLLAMA_HOST}..."
      ollama serve &
      
      # Wait for Ollama to be ready by polling /api/tags
      echo "⏳ Waiting for embedded Ollama to be ready..."
      for i in {1..30}; do
        if curl -fsS "${OLLAMA_API}/api/tags" >/dev/null 2>&1; then
          break
        fi
        sleep 1
      done
      
      echo "📥 Ensuring required LLM models are available in embedded Ollama..."
      for model in "${MODELS_TO_PULL[@]}"; do
        echo "➡️  Checking model: $model"
        if curl -fsS "${OLLAMA_API}/api/tags" | grep -q "\"name\": \"${model}\""; then
          echo "✅ Model already present: $model"
        else
          echo "⬇️  Pulling $model ..."
          if ! ollama pull "$model"; then
            echo "⚠️  Failed to pull $model, continuing with other models"
          fi
        fi
      done
  fi
else
  echo "🔗 Using external Ollama at ${OLLAMA_API}"
fi

# Create data directories
mkdir -p /app/data/memory /app/data/logs /app/data/config

# Set up configuration if not exists
if [ ! -f "/app/data/config/agents.json" ]; then
    echo "⚙️  Creating default agent configuration..."
    DEFAULT_MODEL="$MODEL1"
    cat > /app/data/config/agents.json << EOF
{
  "agents": [
    {
      "name": "Atlas-Interface",
      "provider": "ollama",
      "model": "${DEFAULT_MODEL}",
      "role": "interface",
      "skills": ["conversation", "memory", "user_interaction"]
    },
    {
      "name": "Atlas-Orchestrator", 
      "provider": "ollama",
      "model": "${MODEL2}",
      "role": "orchestrator",
      "skills": ["planning", "task_execution", "automation"]
    },
    {
      "name": "Atlas-Monitor",
      "provider": "ollama", 
      "model": "${MODEL3}",
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