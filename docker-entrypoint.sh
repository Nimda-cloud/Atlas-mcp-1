#!/bin/bash
set -e

echo "🤖 Starting Atlas Autonomous System..."

# Derive Ollama API base. Prefer localhost when running locally, 0.0.0.0 in containers.
is_container() {
  [[ -f "/.dockerenv" ]] && return 0
  grep -Eqa '(docker|containerd)' /proc/1/cgroup 2>/dev/null && return 0
  return 1
}

# Helper: check command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Helper: wait for simple HTTP endpoint
wait_for_url() {
  local url="$1"; local retries="${2:-20}"; local delay="${3:-1}"
  for i in $(seq 1 "$retries"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}

# If running OUTSIDE container, allow this script to orchestrate the FULL Docker stack.
# Default behavior on host: if Docker Compose is available and docker-compose.yml exists,
# and either --full-stack is passed OR no args are provided, spin up the full stack.
if ! is_container; then
  if command_exists docker && docker compose version >/dev/null 2>&1 && [[ -f "docker-compose.yml" ]]; then
    if [[ "$1" == "--full-stack" || "$1" == "fullstack" || "$#" -eq 0 ]]; then
      echo "🧩 Detected host execution. Launching FULL Atlas stack via Docker Compose..."
      DETACH=${ATLAS_DETACH:-true}
      BUILD=${ATLAS_BUILD:-true}
      # Build args
      CMD=(docker compose --profile monitoring --profile mcp --profile macos up)
      [[ "$BUILD" == "true" ]] && CMD+=(--build)
      [[ "$DETACH" == "true" ]] && CMD+=(-d)
      echo "➡️  Command: ${CMD[*]}"
      "${CMD[@]}"

      echo "⏳ Waiting for key services to respond..."
      wait_for_url "http://localhost:8000/status" 40 1 || echo "⚠️ atlas-core not responding yet"
      wait_for_url "http://localhost:8080/health" 30 1 || echo "⚠️ frontend not responding yet"
      wait_for_url "http://localhost:4004/health" 30 1 || echo "⚠️ tts mcp not responding yet"
      wait_for_url "http://localhost:6333/dashboard" 20 1 || echo "⚠️ qdrant dashboard not responding yet"

      echo "📦 Current stack status:"
      docker compose ps || true

      echo "✅ Full stack startup invoked. Exiting host launcher path."
      exit 0
    fi
  fi
fi

if [[ -z "${OLLAMA_HOST}" ]]; then
  if is_container; then
    export OLLAMA_HOST="0.0.0.0:11434"
  else
    export OLLAMA_HOST="localhost:11434"
  fi
fi
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
MODEL1="${ATLAS_LLM1_MODEL:-${ATLAS_LLM_MODEL:-llama3.2:latest}}"
MODEL2="${ATLAS_LLM2_MODEL:-${ATLAS_LLM_MODEL:-gpt-oss:latest}}"
MODEL3="${ATLAS_LLM3_MODEL:-${ATLAS_LLM_MODEL:-llama3.2:latest}}"

# Build a unique list of models to pull, plus global fallbacks
FALLBACK_MODELS=("gpt-oss:latest" "llama3.2:latest" "llama3:latest" "mistral:latest")
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

# Resolve data directory with safe fallbacks (works in Docker and when run locally)
# 1) Respect ATLAS_DATA_DIR if provided
# 2) Default to /app/data (in-container)
# 3) Fallback to ./data (when local filesystem is read-only for /app)

DATA_DIR_CANDIDATES=()
if [[ -n "${ATLAS_DATA_DIR}" ]]; then
  DATA_DIR_CANDIDATES+=("${ATLAS_DATA_DIR}")
fi
DATA_DIR_CANDIDATES+=("/app/data" "${PWD}/data")

pick_data_dir() {
  for d in "$@"; do
    # Try to create and verify writability without failing the script
    if mkdir -p "$d" 2>/dev/null && [ -w "$d" ]; then
      echo "$d"
      return 0
    fi
  done
  return 1
}

CHOSEN_DATA_DIR=$(pick_data_dir "${DATA_DIR_CANDIDATES[@]}") || true
if [[ -z "${CHOSEN_DATA_DIR}" ]]; then
  echo "❌ Unable to find a writable data directory. Please set ATLAS_DATA_DIR to a writable path."
  exit 1
fi

export ATLAS_DATA_DIR="${CHOSEN_DATA_DIR}"
export ATLAS_LOG_DIR="${ATLAS_LOG_DIR:-${ATLAS_DATA_DIR}/logs}"

# Create required subfolders inside the chosen data dir
mkdir -p "${ATLAS_DATA_DIR}/memory" "${ATLAS_DATA_DIR}/logs" "${ATLAS_DATA_DIR}/config"
echo "📂 Using data directory: ${ATLAS_DATA_DIR}"

# Set up configuration if not exists
if [ ! -f "${ATLAS_DATA_DIR}/config/agents.json" ]; then
    echo "⚙️  Creating default agent configuration..."
    DEFAULT_MODEL="$MODEL1"
    cat > "${ATLAS_DATA_DIR}/config/agents.json" << EOF
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
# Determine python executable
PY_BIN="python"
if ! command -v ${PY_BIN} >/dev/null 2>&1; then
  PY_BIN="python3"
fi

# Default command behavior
if [ "$#" -eq 0 ]; then
  set -- "$PY_BIN" atlas_core.py
elif [[ "$1" == -* ]]; then
  # If the first argument is an option, prepend the default command
  set -- "$PY_BIN" atlas_core.py "$@"
fi

exec "$@"