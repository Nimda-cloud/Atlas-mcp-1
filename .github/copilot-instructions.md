# Atlas MCP Development Instructions

**ALWAYS follow these instructions first. Only use additional search and context gathering if the information here is incomplete or found to be in error.**

Atlas MCP is an autonomous system with multi-agent AI for macOS management, supporting three deployment methods: Local Python, Docker, and Kubernetes production.

## Working Effectively

### Bootstrap and Build Commands
- **NEVER CANCEL builds or long-running commands** - builds may take 10+ minutes, tests take 3-5 minutes
- **Set timeout to 15+ minutes** for all build commands to prevent premature cancellation
- **Network issues**: PyPI connections may timeout due to SSL certificate issues - document failures rather than skip

### Local Python Development
```bash
# Basic validation (works without dependencies - 30 seconds)
python test_basic.py

# Create environment and install dependencies
python3 -m venv atlas_env
source atlas_env/bin/activate
pip install --upgrade pip

# Install requirements - NEVER CANCEL - takes 3-5 minutes, may fail with network timeouts
timeout 600 pip install -r requirements.txt

# If pip install fails due to network issues, try essential packages only:
pip install ollama openai fastapi uvicorn aiohttp psutil pydantic python-dotenv pyyaml click pytest pytest-asyncio

# Run full tests (requires dependencies - 2-3 minutes)
python test_atlas.py

# Start Atlas locally
./start_atlas.sh --local
# Alternative: python atlas_core.py
```

### Docker Development  
```bash
# Validate configuration (10 seconds)
docker compose config

# Build main image - NEVER CANCEL - takes 5-10 minutes, may fail with SSL issues
timeout 900 docker build -t atlas-test .

# Start full stack with all profiles - NEVER CANCEL - takes 3-5 minutes
docker compose --profile monitoring --profile mcp --profile macos up -d

# Check service health (wait 2-3 minutes for startup)
curl -f http://localhost:8000/status
curl -f http://localhost:8080/health  
curl -f http://localhost:4002/health  # mcp-automation
curl -f http://localhost:4003/health  # mcp-automator  
curl -f http://localhost:4004/health  # mcp-tts
```

### Kubernetes Production
```bash
# Check dependencies
kubectl version --client
make help

# Build Docker images - NEVER CANCEL - takes 10-15 minutes total
timeout 1200 make build-images

# Deploy to development - NEVER CANCEL - takes 5-8 minutes  
timeout 600 make install-dev

# Check status and logs
make status-dev
make logs-dev

# Access services via port forwarding
make port-forward-atlas-dev      # http://localhost:8080
make port-forward-grafana-dev    # http://localhost:3000  
make port-forward-prometheus-dev # http://localhost:9090
```

## Validation and Testing

### Manual Validation Scenarios
**ALWAYS test these scenarios after making changes:**

1. **Core System Test**:
   ```bash
   # Start system
   ./start_atlas.sh --local
   
   # Wait 30 seconds, then test
   curl -f http://localhost:8000/status
   curl -f http://localhost:8000/docs  # API documentation
   ```

2. **Web Interface Test**:
   - Open http://localhost:8000 in browser
   - Verify dashboard loads without errors
   - Test agent chat interface
   - Screenshot any UI changes

3. **MCP Services Test**:
   ```bash
   # Test each MCP service endpoint
   curl -f http://localhost:4002/health  # automation
   curl -f http://localhost:4003/health  # macos-automator
   curl -f http://localhost:4004/health  # tts
   curl -f http://localhost:4005/mcp     # playwright
   ```

4. **Full Stack Test** (Docker):
   ```bash
   docker compose --profile monitoring --profile mcp up -d
   # Wait 3 minutes for all services
   curl -f http://localhost:8080/health  # 3D frontend
   curl -f http://localhost:3000         # Grafana
   curl -f http://localhost:9090         # Prometheus
   ```

### Automated Tests
```bash
# Basic structure tests (no dependencies required - 30 seconds)
python test_basic.py

# Full system tests (requires pip install - 2-3 minutes)  
python test_atlas.py

# Docker validation (10 seconds)
docker compose config

# Kubernetes dry-run (30 seconds)
kubectl kustomize k8s/overlays/development
```

## Common Issues and Solutions

### Network/SSL Issues
- **PyPI SSL errors**: Common in containerized environments - "certificate verify failed: self-signed certificate in certificate chain"
- **pip install timeouts**: HTTPSConnectionPool read timeouts when downloading packages
- **Solution**: Document the failure, try core packages individually, increase timeout values
- **Known failures**: PyAudio (requires system audio libraries), some ML packages
- **Workaround**: `pip install ollama openai fastapi uvicorn aiohttp psutil pydantic python-dotenv pyyaml click pytest pytest-asyncio` (core packages only)

### Build Failures  
- **Docker build fails**: Usually network-related during pip install step
- **Solution**: Use longer timeouts, document exact error, try minimal requirements
- **Kubernetes fails**: Often due to missing Docker images
- **Solution**: Ensure `make build-images` completes successfully first

### Missing Dependencies
- **Audio packages (PyAudio)**: Require system libraries, may fail on Linux
- **macOS packages**: Will be skipped on non-macOS systems (expected)
- **Solution**: System will gracefully degrade functionality

## Project Structure

### Core Files
- `atlas_core.py` - Main AI agent system with FastAPI web interface
- `mcp_automation_server.py` - Model Context Protocol automation server
- `mcp_macos_automator.py` - macOS-specific automation capabilities  
- `requirements.txt` - Python dependencies (26 packages)

### Key Scripts
- `start_atlas.sh` - Smart startup script (auto-detects environment)
- `install_macos.sh` - macOS installation and setup
- `setup-k8s.sh` - Kubernetes cluster setup and deployment
- `k8s-manage.sh` - Kubernetes management operations

### Configuration
- `docker-compose.yml` - Multi-service stack with monitoring
- `Makefile` - Quick Kubernetes operations and builds
- `k8s/` - Complete Kubernetes manifests with overlays
- `.env.k8s.example` - Environment variables template

### Build Outputs
- Avoid committing: `atlas_env/`, `__pycache__/`, `*.log`, `data/`, Docker volumes

## Time Expectations

**CRITICAL - NEVER CANCEL these operations:**

- **Basic tests**: 30 seconds
- **pip install requirements.txt**: 3-5 minutes (may timeout)
- **Docker build**: 5-10 minutes (may fail due to network)  
- **Docker compose up**: 3-5 minutes startup
- **Kubernetes build-images**: 10-15 minutes total
- **Kubernetes deploy**: 5-8 minutes
- **Full system startup**: 2-3 minutes (wait before testing)

## Development Workflow

1. **Always run basic tests first**: `python test_basic.py`
2. **Check file syntax**: `python -m py_compile atlas_core.py mcp_*.py`
3. **Validate Docker config**: `docker compose config`  
4. **Test with timeouts**: Use 600-1200 second timeouts for builds
5. **Manual validation**: Test actual functionality, take screenshots of UI changes
6. **Document failures**: If builds fail due to network issues, document the exact error rather than skip

## Environment Variables

Key environment variables for different deployment modes:
- `ATLAS_WEB_PORT=8000` - Web interface port
- `OLLAMA_URL=http://localhost:11434` - LLM service URL  
- `ATLAS_LLM1_MODEL=llama3.1:8b` - Interface agent model
- `ATLAS_DATA_DIR=/app/data` - Data storage location
- `USE_EMBEDDED_OLLAMA=false` - Use external Ollama instance

See `.env.k8s.example` for complete variable list.

## Quick Reference

### Essential URLs
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs  
- 3D Frontend: http://localhost:8080
- Grafana: http://localhost:3000 (admin/atlas_admin)
- Prometheus: http://localhost:9090

### Emergency Commands
```bash
# Stop everything
docker compose down
killall python  # if running locally

# Clean restart  
docker compose down -v && docker compose up -d

# Kubernetes emergency stop
make clean-dev
```

### Architecture Notes
- **LLM1**: Interface agent (user interaction, memory)
- **LLM2**: Orchestrator agent (task planning, coordination)  
- **LLM3**: Monitor agent (system health, security)
- **MCP Hub**: Modular services for automation, TTS, browser control
- **3D Frontend**: WebGL-based enhanced interface
- **Monitoring**: Prometheus metrics + Grafana dashboards

**Remember**: Set long timeouts, wait for services to be ready, and manually validate functionality after changes.