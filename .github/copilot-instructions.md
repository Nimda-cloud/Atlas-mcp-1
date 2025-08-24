# GitHub Copilot Instructions for Atlas MCP

## Repository Overview

**Atlas Autonomous System** is an advanced autonomous macOS management system using multiple AI agents (LLM1: Interface, LLM2: Orchestrator, LLM3: Monitor) with local LLM processing via Ollama. The system provides intelligent computer automation, voice interaction, web-based 3D interfaces, and full enterprise Kubernetes deployment capabilities.

**Repository Size:** ~140 files, primarily Python (~50KB core files), with Docker/K8s configurations, 3D assets, and monitoring setup.

**Core Technologies:**
- **Languages:** Python 3.11+, JavaScript, Shell, YAML
- **Frameworks:** FastAPI, aiohttp, uvicorn (web), Three.js (3D frontend)
- **AI/ML:** Ollama (local LLM), OpenAI API, sentence-transformers
- **Automation:** pyautogui, pynput, AppleScript (macOS only)
- **Storage:** Redis (cache), Qdrant (vector DB), persistent volumes
- **Deployment:** Docker Compose, Kubernetes (production), local Python
- **Monitoring:** Prometheus + Grafana stack

## Build and Deployment Instructions

### Prerequisites and Versions

**Always check these requirements first:**
- Python 3.11+ (required for all modes)
- Docker 20.10+ and Docker Compose 2.0+ (for containerized deployment)
- Ollama service (for LLM functionality)
- kubectl and kustomize (for Kubernetes deployment)
- macOS 10.15+ (for full macOS automation features)

### Bootstrap Steps

**For local development:**
```bash
# 1. Create Python virtual environment (ALWAYS do this first)
python3 -m venv atlas_env
source atlas_env/bin/activate

# 2. Install dependencies (expect 1-3 minutes depending on network)
pip install --upgrade pip
pip install -r requirements.txt

# Note: PyAudio and some audio libraries may fail on non-macOS systems
# This is expected and won't prevent core functionality
```

**For Docker deployment:**
```bash
# 1. Verify Docker is running
docker info

# 2. Pull required images (optional, auto-pulled during build)
docker pull python:3.11-slim
docker pull redis:7-alpine
docker pull qdrant/qdrant:latest
```

### Build Commands (Ordered by Reliability)

**1. Local Python Mode (Most Reliable):**
```bash
# Quick start - auto-detects environment
./start_atlas.sh

# Explicit local mode
./start_atlas.sh --local

# Background mode (for testing)
./start_atlas.sh --local --background
```

**Expected timing:** 30-60 seconds for first run (includes venv creation and dependency installation)

**2. Docker Compose Mode:**
```bash
# Standard startup
./start_atlas.sh --docker

# Background mode
docker-compose --profile monitoring --profile mcp up -d

# Build from scratch if needed
docker-compose build --no-cache
```

**Expected timing:** 2-5 minutes for first build, 30 seconds for subsequent runs

**3. Kubernetes Mode (Production):**
```bash
# Interactive setup (recommended for first time)
./setup-k8s.sh

# Direct deployment
make install-dev          # Development environment
make install-prod         # Production environment

# Status check
make status-dev
```

**Expected timing:** 5-10 minutes for cluster setup, 2-3 minutes for deployment

### Testing Commands

**Always run these in order:**

```bash
# 1. Basic syntax and structure test (no dependencies)
python test_basic.py

# 2. Full functional test (requires dependencies)
python test_atlas.py

# 3. Docker configuration validation
docker-compose config

# 4. Kubernetes config validation (if using K8s)
./test-k8s-config.sh
```

### Health Check Endpoints

**After starting services, verify these endpoints respond:**
- Atlas Core: `http://localhost:8000/status` 
- Enhanced Frontend: `http://localhost:8080/health`
- MCP Automation: `http://localhost:4002/health`
- MCP Automator: `http://localhost:4003/health`
- TTS Service: `http://localhost:4004/health`
- Playwright MCP: `http://localhost:4005/mcp`

### Common Build Issues and Workarounds

**Issue: PyAudio installation fails**
- **Cause:** Missing audio libraries on non-macOS systems
- **Workaround:** Remove PyAudio from requirements.txt temporarily, or install system audio libraries first
- **Impact:** Audio features disabled, but core functionality works

**Issue: Port conflicts (8000, 8080, 4002-4005)**
- **Check:** `lsof -i :8000` to see what's using the port
- **Workaround:** Set environment variables: `ATLAS_WEB_PORT=8001`

**Issue: Ollama not responding**
- **Check:** `curl http://localhost:11434/api/tags`
- **Fix:** Start Ollama service: `ollama serve` or `brew services start ollama` (macOS)

**Issue: Docker permission denied**
- **Check:** `docker info` shows no errors
- **Fix:** Add user to docker group or use sudo

**Issue: Kubernetes pod CrashLoopBackOff**
- **Diagnosis:** `kubectl describe pod <pod-name> -n atlas-mcp`
- **Common causes:** Missing secrets, resource limits too low, image pull failures

### Time Requirements for Commands

- `python test_basic.py`: 5-10 seconds
- `python test_atlas.py`: 30-60 seconds  
- `pip install -r requirements.txt`: 1-3 minutes
- `./start_atlas.sh --local`: 30-60 seconds
- `docker-compose up`: 2-5 minutes (first time)
- `make install-dev`: 3-7 minutes
- Full K8s deployment: 5-15 minutes

## Project Architecture and File Layout

### Core Application Files
```
atlas_core.py              # Main application entry point (1500+ lines)
├── AtlasCore class        # Primary system orchestrator
├── LLMAgent classes       # AI agent implementations  
├── MacOSAutomation class  # System automation interface
└── FastAPI web app        # HTTP API and UI endpoints

mcp_automation_server.py   # MCP server for general automation (400+ lines)
mcp_macos_automator.py     # MCP server for macOS-specific automation (600+ lines)
```

### Configuration Files
```
requirements.txt           # Python dependencies (26 packages)
docker-compose.yml         # Multi-service container orchestration (210 lines)
.env.k8s.example          # Environment variables template
Dockerfile                # Main application container
Dockerfile.mcp-*          # Specialized MCP server containers
```

### Deployment Configurations
```
k8s/                      # Kubernetes configurations
├── base/                 # Base resources (15 YAML files)
│   ├── namespace.yaml    # atlas-mcp namespace
│   ├── *-deployment.yaml # Service deployments
│   ├── services.yaml     # Kubernetes services
│   ├── hpa.yaml         # Horizontal Pod Autoscaler
│   └── secrets.yaml     # Secrets management
├── overlays/
│   ├── development/      # Dev environment configs
│   └── production/       # Prod environment configs
├── monitoring/           # Prometheus + Grafana
└── ingress/             # Load balancer + SSL
```

### Scripts and Utilities
```
start_atlas.sh            # Main startup script (270+ lines)
install_macos.sh          # macOS installation script
setup-k8s.sh             # Kubernetes cluster setup
k8s-manage.sh            # Kubernetes management commands
Makefile                 # Quick command shortcuts (100+ lines)
```

### Frontend and Assets
```
3d_helmet_viewer/         # 3D web interface
├── enhanced_frontend.html # Main UI
├── enhanced_server.py    # Frontend server
├── DamagedHelmet.glb    # 3D robot head model
└── requirements-frontend.txt # Frontend dependencies

archived_3d_assets/       # Legacy 3D components
services/                 # Supporting services
├── tts_mcp_adapter/     # Text-to-speech service
└── mcp_playwright_server/ # Browser automation
```

### Data and Logs (Created at Runtime)
```
data/                     # Application data (git-ignored)
├── config/              # Runtime configuration
├── memory/              # Agent memory storage  
└── logs/                # Application logs

atlas_env/               # Python virtual environment (git-ignored)
```

## CI/CD and Validation Pipeline

### Pre-commit Checks (Run These Before Committing)

```bash
# 1. Code syntax validation
python test_basic.py

# 2. Docker config validation  
docker-compose config

# 3. Python code formatting (if black is installed)
black --check atlas_core.py mcp_*.py

# 4. Basic import tests
python -c "import atlas_core; print('✅ Imports OK')"
```

### GitHub Workflows (Currently None)

**Note:** Repository currently has no `.github/workflows/` directory. Consider adding:
- Syntax validation workflow
- Docker build validation
- K8s config testing
- Security scanning

### Production Deployment Checklist

```bash
# 1. Test in development first
make install-dev && make test-dev

# 2. Prepare production secrets
cp .env.k8s.example .env.k8s
# Edit .env.k8s with production values

# 3. Deploy to production
make install-prod

# 4. Verify deployment
make status-prod && make monitoring-prod

# 5. Run integration tests
make test-prod
```

## Key Dependencies and Ecosystem

### Critical Dependencies (Always Required)
- `ollama>=0.2.0` - Local LLM runtime
- `fastapi>=0.104.0` - Web framework
- `uvicorn>=0.24.0` - ASGI server
- `aiohttp>=3.9.0` - Async HTTP client
- `psutil>=5.9.0` - System monitoring

### macOS-Specific Dependencies
- `py-applescript>=1.0.3` - AppleScript integration
- `appscript>=1.2.2` - Application scripting
- These are marked with `sys_platform == "darwin"` and will be skipped on other platforms

### Optional/Problematic Dependencies
- `pyaudio>=0.2.11` - Often fails on non-macOS, audio features only
- `pyautogui>=0.9.54` - GUI automation, may require display
- `pynput>=1.7.6` - Input monitoring, may require permissions

### Development Dependencies
- `pytest>=7.4.0` - Testing framework
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Linting

## Agent Instructions Summary

**Trust these instructions** - they are tested and comprehensive. Only perform additional searches if:
1. Instructions appear outdated or incomplete
2. Commands fail with unexpected errors
3. New features need to be added that aren't covered

**Key principles for working with this repository:**
1. **Always use virtual environments** for Python development
2. **Test locally first** before Docker/K8s deployment  
3. **Check health endpoints** after starting services
4. **Use make commands** for Kubernetes operations - they're well-tested
5. **Expect some optional dependencies to fail** on non-macOS systems
6. **Run tests frequently** - they're fast and catch issues early

**Most reliable development workflow:**
```bash
./start_atlas.sh --local --background  # Start system
python test_atlas.py                   # Verify functionality  
# Make your changes
python test_basic.py                   # Quick validation
./start_atlas.sh --local               # Test changes
```

This repository is well-structured with comprehensive automation. The build system is mature but requires attention to platform-specific dependencies and service orchestration.