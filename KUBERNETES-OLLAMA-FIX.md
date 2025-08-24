# 🔧 Kubernetes macOS Ollama Connectivity Fix

This document outlines the fixes applied to resolve Kubernetes networking issues on macOS and enable proper connectivity between Atlas containers and the host Ollama service.

## Issues Fixed

### 1. Kind Cluster Network Configuration
**Problem**: Kind clusters on macOS couldn't access host services (like Ollama) due to network isolation.

**Solution**: Updated `kind-config.yaml` with:
- Proper networking configuration with API server settings
- Host port mapping for Ollama (11434) to enable direct access
- Improved cluster setup for macOS Docker Desktop

### 2. Hardcoded IP Addresses
**Problem**: Configuration contained hardcoded IPs (`172.17.97.123`, `172.19.0.1`) that only worked on specific systems.

**Solution**: 
- Replaced hardcoded IPs with dynamic detection
- Created service-based discovery using `ollama-host-service`
- Added automatic host IP detection in `k8s-manage.sh`

### 3. Incorrect Ollama URL Configuration
**Problem**: Atlas was configured to use `host.docker.internal:11434` which doesn't work in Kind clusters.

**Solution**: Changed to use Kubernetes service discovery:
```yaml
OLLAMA_URL: "http://ollama-host-service:11434"
```

### 4. Development Environment Using Embedded Ollama
**Problem**: Development overlay was set to `USE_EMBEDDED_OLLAMA: "true"` instead of using host Ollama.

**Solution**: Updated development configuration:
```yaml
USE_EMBEDDED_OLLAMA: "false"
OLLAMA_URL: "http://ollama-host-service:11434"
```

### 5. Missing Ollama Host Service
**Problem**: The `ollama-host-service.yaml` wasn't included in the base kustomization.

**Solution**: Added to `k8s/base/kustomization.yaml`:
```yaml
resources:
- ollama-host-service.yaml
```

### 6. Network Policy Restrictions
**Problem**: Network policies didn't allow egress traffic to Ollama port 11434.

**Solution**: Added egress rule:
```yaml
- to: []
  ports:
  - protocol: TCP
    port: 11434
```

### 7. Kustomize Configuration Issues
**Problem**: Development overlay used problematic `namePrefix` causing patch conflicts.

**Solution**: 
- Removed `namePrefix: dev-` from development overlay
- Simplified patch structure
- Fixed all kustomize builds to work properly

## Architecture

### Host Connectivity Flow
```
Atlas Container → ollama-host-service:11434 → Host IP:11434 → Host Ollama
```

### Dynamic IP Detection
The `k8s-manage.sh` script now automatically:
1. Detects the Kind cluster gateway IP
2. Updates the `ollama-host-service` endpoint
3. Verifies Ollama connectivity
4. Provides helpful error messages if Ollama is unavailable

### Service Configuration
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ollama-host-service
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - name: http
    port: 11434
    targetPort: 11434
---
apiVersion: v1
kind: Endpoints
metadata:
  name: ollama-host-service
subsets:
- addresses:
  - ip: 172.18.0.1  # Dynamically updated
  ports:
  - name: http
    port: 11434
```

## Testing

Run the configuration test:
```bash
./test-k8s-config.sh
```

This validates:
- ✅ YAML syntax correctness
- ✅ Kustomize builds work
- ✅ Ollama configuration is correct
- ✅ Network policies allow traffic
- ✅ Namespace configuration
- ✅ Expected resource counts

## Usage

### Development Environment
```bash
# 1. Create Kind cluster with proper networking
kind create cluster --config=kind-config.yaml --name=atlas-mcp-dev

# 2. Deploy Atlas (automatically configures Ollama connectivity)
make install-dev

# 3. Check status
make status-dev

# 4. Access Atlas
make port-forward-atlas-dev
```

### Verify Ollama Connectivity
The setup script automatically checks Ollama connectivity:
```bash
# Manual verification
kubectl exec -n atlas-mcp-dev deployment/atlas-core -- curl -s http://ollama-host-service:11434/api/tags
```

## Results

- ✅ **Atlas containers can connect to host Ollama**
- ✅ **Dynamic host IP detection works on different systems**
- ✅ **No more hardcoded network configuration**
- ✅ **Proper service discovery using Kubernetes services**
- ✅ **Network policies allow required traffic**
- ✅ **Development environment fully functional**
- ✅ **All Kubernetes configurations validated**

The Atlas MCP system now properly integrates with host Ollama services on macOS Kind clusters.