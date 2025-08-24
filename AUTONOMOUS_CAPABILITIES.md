# Atlas Autonomous System Documentation

## Overview

The Atlas MCP system has been enhanced with complete autonomous capabilities, enabling fully automated development, testing, and deployment workflows.

## Autonomous Features

### 🔄 Enhanced GitHub Workflows

#### PR Agent CI Workflow (`.github/workflows/pr-agent-ci.yml`)
- **Auto-detection**: Automatically processes PRs from `copilot-*`, `agent/`, or `copilot-agent/` branches
- **Multi-platform testing**: Tests on both Linux containers and macOS
- **Smart merging**: Enhanced mergeable state handling with 120-second timeout
- **Robust error handling**: Graceful fallbacks for dependency installation

**Key improvements:**
- Waits for PR to become mergeable (handles GitHub's async state updates)
- Best-effort dependency installation with fallback to core packages
- Automatic branch cleanup after merge

#### Post-merge Local Verification (`.github/workflows/post-merge-local.yml`)
- **Configurable startup**: Uses repository variables for flexible service configuration
- **Health monitoring**: Automated health checks with configurable endpoints
- **Local synchronization**: Automatic sync of developer working copy
- **Failure reporting**: Creates GitHub issues on verification failure

**Configuration variables:**
- `START_CMD`: Command to start your service (e.g., `uvicorn app:app --port 8000`)
- `HEALTHCHECK_URL`: URL for health verification (e.g., `http://localhost:8000/health`)
- `LOCAL_REPO_PATH`: Path to local repository for auto-sync

### 🤖 Autonomous Scripts

#### Setup Script (`atlas_autonomous_setup.sh`)
Comprehensive system setup with:
- System requirements validation
- Python environment creation
- Dependency installation with error handling
- Test execution
- Port availability checking
- Autonomous script generation

#### Diagnostic Script (`atlas_diagnostic.sh`)
Fast system validation covering:
- File structure integrity
- Python syntax validation
- Docker environment check
- Kubernetes configuration validation
- Port availability
- GitHub workflow validation

#### Health Monitor (`atlas_health_monitor.sh`)
Real-time service monitoring for:
- Atlas Core (port 8000)
- Enhanced Frontend (port 8080)
- MCP Automation (port 4002)
- MCP Automator (port 4003)
- TTS Service (port 4004)
- Playwright MCP (port 4005)

#### Autonomous Startup (`atlas_start_autonomous.sh`)
Intelligent startup with:
- Automatic deployment method selection
- Service health verification
- User-friendly status reporting

### 📊 Testing Infrastructure

#### Autonomous Capabilities Test (`test_autonomous_capabilities.py`)
Comprehensive validation of:
- GitHub workflow syntax and structure
- Autonomous script functionality
- Deployment configuration validity
- Health monitoring setup
- Environment adaptation

**Features:**
- JSON report generation
- Detailed test logging
- Performance metrics
- Recommendations for improvements

## Usage Guide

### Quick Start

1. **Run diagnostic check:**
   ```bash
   ./atlas_diagnostic.sh
   ```

2. **Full autonomous setup:**
   ```bash
   ./atlas_autonomous_setup.sh
   ```

3. **Start Atlas autonomously:**
   ```bash
   ./atlas_start_autonomous.sh
   ```

4. **Monitor system health:**
   ```bash
   ./atlas_health_monitor.sh
   ```

### Development Workflow

1. **Agent creates PR** from `copilot-*` branch
2. **CI automatically tests** on Linux and macOS
3. **PR auto-merges** when tests pass and mergeable
4. **Post-merge verification** runs on self-hosted macOS runner
5. **Local repository syncs** automatically
6. **Issues created** automatically on failure

### Configuration Setup

For complete autonomous operation, configure these repository variables:

```bash
# Repository Variables (Settings → Actions → Variables)
START_CMD="./start_atlas.sh --local --background"
HEALTHCHECK_URL="http://localhost:8000/status"
LOCAL_REPO_PATH="/path/to/your/local/atlas-mcp"
```

### Self-hosted Runner Setup

1. **Install self-hosted runner** with labels: `self-hosted`, `macOS`
2. **Install Docker Desktop** for containerized services
3. **Configure runner** to run as a service
4. **Set repository permissions** to "Read and write"

## Architecture

### Autonomous Cycle
```
Agent PR → CI Tests → Auto-merge → Local Verification → Sync → Issue on Failure
```

### Service Dependencies
```
Atlas Core (8000) ← Web Interface
   ↓
MCP Services (4002-4005) ← Automation, macOS, TTS, Playwright
   ↓
Database Services ← Redis (6379), Qdrant (6333-6334)
   ↓
3D Frontend (8080) ← Enhanced UI
```

### Health Monitoring
- **Real-time checks** for all service endpoints
- **Configurable timeouts** for different service types
- **Automated restart** capabilities (via start script)
- **Status reporting** with clear success/failure indicators

## Network Considerations

The system handles common network issues in CI environments:

- **PyPI SSL certificate** verification failures
- **Connection timeouts** during package installation
- **Graceful degradation** to core packages when full installation fails
- **Best-effort installations** with detailed error reporting

## Troubleshooting

### Common Issues

1. **Port conflicts**: Run `./atlas_diagnostic.sh` to check port availability
2. **Permission errors**: Ensure scripts are executable (`chmod +x *.sh`)
3. **Network issues**: Check error logs for SSL/timeout issues
4. **Runner problems**: Verify self-hosted runner labels and connectivity

### Debug Commands

```bash
# Check system status
./atlas_diagnostic.sh

# Validate workflows
python -c "import yaml; yaml.safe_load(open('.github/workflows/pr-agent-ci.yml'))"

# Test Docker setup
docker compose config

# Check Kubernetes
kubectl kustomize k8s/overlays/development

# Monitor logs
tail -f logs/app.txt
```

## Security Features

- **Branch protection** with required status checks
- **Limited scope** for auto-merge (only agent branches)
- **Secure variable handling** for configuration
- **Isolated environments** for testing
- **Audit trail** through GitHub Actions logs

## Performance Optimizations

- **Parallel testing** on multiple platforms
- **Efficient caching** of dependencies
- **Fast diagnostic** checks (< 30 seconds)
- **Background services** startup
- **Intelligent timeouts** based on operation type

## Future Enhancements

Planned autonomous features:
- **Automated dependency updates** with testing
- **Performance regression detection**
- **Security vulnerability scanning**
- **Auto-scaling** based on load
- **Predictive maintenance** alerts

---

For detailed technical information, see:
- `PROJECT_STRUCTURE.md` - System architecture
- `README.md` - Basic usage guide
- `ІНСТРУКЦІЯ.md` - Ukrainian documentation
- Test reports in `atlas_autonomous_test_report.json`