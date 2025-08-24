# Atlas MCP Full Automation Guide

This guide provides comprehensive instructions for using the enhanced Atlas MCP automation system with intelligent firewall detection and mitigation.

## 🚀 Quick Start

### One-Command Setup
```bash
# Automatic setup with firewall detection
./scripts/master-setup.sh

# Safe mode for firewall-restricted environments
./scripts/master-setup.sh safe

# Full automation mode (no firewall checks)
./scripts/master-setup.sh full
```

### Available Scripts

| Script | Purpose | Best For |
|--------|---------|----------|
| `master-setup.sh` | Main entry point with intelligent mode selection | First-time setup |
| `full-automation-setup.sh` | Complete Kubernetes automation | Production deployment |
| `firewall-detection.sh` | Network restriction analysis | Troubleshooting |
| `setup-k8s-ci.sh` | CI/CD optimized setup | GitHub Actions |

## 📋 Setup Modes

### Auto Mode (Recommended)
- Automatically detects firewall restrictions
- Chooses optimal deployment strategy
- Provides fallback options

```bash
./scripts/master-setup.sh auto
```

### Safe Mode
- Uses only localhost networking
- Firewall-safe operations
- Works in restricted environments

```bash
./scripts/master-setup.sh safe
```

### Full Mode
- Complete Kubernetes automation
- All features enabled
- Requires unrestricted network access

```bash
./scripts/master-setup.sh full
```

## 🔥 Firewall Detection & Mitigation

### Automatic Detection
The firewall detection system tests:
- ✅ Localhost connectivity (127.0.0.1)
- ⚠️ Private networks (10.x.x.x, 172.x.x.x, 192.168.x.x)
- ⚠️ Kubernetes networks (10.244.x.x, 10.96.x.x)
- ✅ External services (GitHub, PyPI)

### Generated Configurations
When firewall restrictions are detected, the system generates:

#### `firewall-configs/docker-compose.firewall-safe.yml`
```yaml
services:
  atlas-core:
    network_mode: "host"
    environment:
      - ATLAS_BIND_ADDRESS=127.0.0.1
    ports:
      - "127.0.0.1:8000:8000"
```

#### `firewall-configs/port-forward-all.sh`
```bash
#!/bin/bash
# Port-forward all services for localhost access
kubectl port-forward svc/atlas-core-service 8000:8000 -n atlas-mcp-dev &
kubectl port-forward svc/atlas-frontend-service 8080:8080 -n atlas-mcp-dev &
```

## 🏗️ Kubernetes Automation

### Full Automation Features
- **Progressive Docker Image Building**: Multiple fallback strategies
- **Intelligent Error Recovery**: Automatic retries with backoff
- **Firewall-Safe Testing**: Port-forward based service validation
- **Comprehensive Artifact Collection**: Detailed debugging information

### Build Strategies
1. **Standard Build**: Normal Docker build process
2. **Trusted Hosts**: For SSL certificate issues
3. **Minimal Build**: Fallback with reduced dependencies  
4. **Placeholder Images**: Emergency fallback to prevent blocking

### Service Testing
```bash
# Automatic port-forward testing
./scripts/full-automation-setup.sh

# Manual port-forward setup
./firewall-configs/port-forward-all.sh

# Access services
curl http://localhost:8000/status      # Atlas Core
curl http://localhost:8080/health      # Atlas Frontend
curl http://localhost:4002/health      # MCP Automation
```

## 🤖 GitHub Actions Integration

### Enhanced Workflow
The updated `.github/workflows/k8s-firewall-safe.yml` provides:

- **Multi-Strategy Testing**: Full automation + isolated testing
- **Artifact Collection**: Comprehensive debugging information
- **Automatic Issue Creation**: On deployment failures
- **Matrix Testing**: Multiple automation modes

### Triggering CI
```bash
# Add label to PR for testing
gh pr edit <PR_NUMBER> --add-label "k8s-test"

# Manual workflow trigger
gh workflow run "Atlas MCP Kubernetes CI (Firewall Safe)"
```

## 📊 Reports and Artifacts

### Deployment Report
Generated at: `automation-artifacts/deployment-report.md`

```markdown
# Atlas MCP Kubernetes Deployment Report

**Cluster:** atlas-mcp-auto-1693234567
**Namespace:** atlas-mcp-dev
**Started:** 2024-08-24T23:30:00Z

## Service Tests
- ✅ atlas-core-service: SUCCESS
- ✅ atlas-frontend-service: SUCCESS
- ❌ mcp-automation-service: FAILED
```

### Firewall Detection Report
Generated at: `/tmp/atlas-firewall-mitigation.json`

Includes:
- Network connectivity test results
- Detected restrictions analysis
- Recommended mitigations
- Firewall-safe configuration suggestions

## 🛠️ Troubleshooting

### Common Issues

#### ErrImageNeverPull
```bash
# Check if images are loaded
kubectl get nodes -o wide
docker exec <cluster>-control-plane crictl images

# Reload images
kind load docker-image atlas-mcp/atlas-core:latest --name <cluster>
```

#### Service Not Responding
```bash
# Check pod status
kubectl get pods -n atlas-mcp-dev
kubectl describe pod <pod-name> -n atlas-mcp-dev

# Check service endpoint
kubectl get svc -n atlas-mcp-dev
kubectl port-forward svc/<service-name> <port>:<port> -n atlas-mcp-dev
```

#### Firewall Restrictions
```bash
# Run firewall detection
./scripts/firewall-detection.sh

# Use safe mode
./scripts/master-setup.sh safe

# Check generated configs
ls firewall-configs/
```

### Debug Mode
Enable verbose output:
```bash
# Verbose setup
./scripts/master-setup.sh --verbose auto

# Debug individual scripts
SKIP_FIREWALL_CHECK=false ./scripts/firewall-detection.sh
```

## 🔧 Advanced Configuration

### Environment Variables
```bash
# Deployment configuration
export CLUSTER_NAME="my-cluster"
export NAMESPACE="my-namespace"
export CLEANUP_ON_EXIT="false"
export MAX_RETRIES="5"
export TIMEOUT="1200"

# Firewall settings
export SKIP_FIREWALL_CHECK="false"
export ARTIFACTS_DIR="./my-artifacts"

# Run setup
./scripts/master-setup.sh
```

### Custom Docker Images
```bash
# Build with custom tags
docker build -t atlas-mcp/atlas-core:custom .
docker build -t atlas-mcp/atlas-frontend:custom ./3d_helmet_viewer/

# Load into cluster
kind load docker-image atlas-mcp/atlas-core:custom --name my-cluster
```

## 📈 Performance Optimization

### Build Performance
- Use Docker BuildKit for faster builds
- Enable Docker layer caching
- Pre-build base images

### Cluster Performance
- Allocate sufficient resources to Kind cluster
- Use SSD storage for better I/O performance
- Monitor resource usage during deployment

### Network Performance
- Use localhost networking when possible
- Minimize external network calls
- Cache dependencies locally

## 🔐 Security Considerations

### Firewall Compliance
- All automation scripts respect firewall restrictions
- No attempts to bypass security policies
- Graceful degradation in restricted environments

### Container Security
- Images built with security best practices
- Non-root user execution where possible
- Minimal attack surface

### Network Security
- Localhost-only access in restricted environments
- Port-forward instead of direct cluster access
- No persistent external connections

## 📚 Additional Resources

- [Firewall Solutions Guide](FIREWALL-SOLUTIONS.md)
- [Kubernetes Setup Guide](../k8s/README.md)
- [Docker Compose Configuration](../docker-compose.yml)
- [GitHub Actions Workflows](../.github/workflows/)

## 🆘 Getting Help

### Self-Diagnosis
1. Run `./scripts/firewall-detection.sh`
2. Check `automation-artifacts/deployment-report.md`
3. Review GitHub Actions artifacts

### Community Support
- Create issue with deployment report
- Include firewall detection results
- Provide environment details

### Quick Links
- [Project Repository](https://github.com/oleg121203/Atlas-mcp)
- [Issue Tracker](https://github.com/oleg121203/Atlas-mcp/issues)
- [Discussions](https://github.com/oleg121203/Atlas-mcp/discussions)

---

*This guide is automatically updated as part of the Atlas MCP automation improvements.*