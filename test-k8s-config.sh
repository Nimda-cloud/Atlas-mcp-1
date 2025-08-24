#!/bin/bash

# Test script for Kubernetes configuration
# Validates that all configurations are correct before deployment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🧪 Testing Atlas MCP Kubernetes Configuration${NC}"
echo ""

# Test 1: YAML Syntax Validation
echo "1. Validating YAML syntax..."
if find k8s/ -name "*.yaml" | xargs -I {} python3 -c "import yaml; list(yaml.safe_load_all(open('{}')))" 2>/dev/null; then
    echo -e "   ${GREEN}✓ All YAML files have valid syntax${NC}"
else
    echo -e "   ${RED}✗ YAML syntax errors found${NC}"
    exit 1
fi

# Test 2: Kustomize Build Test
echo "2. Testing Kustomize builds..."

echo "   Testing base build..."
if kubectl kustomize k8s/base > /tmp/base-test.yaml 2>/dev/null; then
    echo -e "   ${GREEN}✓ Base build successful ($(wc -l < /tmp/base-test.yaml) lines)${NC}"
else
    echo -e "   ${RED}✗ Base build failed${NC}"
    exit 1
fi

echo "   Testing development build..."
if kubectl kustomize k8s/overlays/development > /tmp/dev-test.yaml 2>/dev/null; then
    echo -e "   ${GREEN}✓ Development build successful ($(wc -l < /tmp/dev-test.yaml) lines)${NC}"
else
    echo -e "   ${RED}✗ Development build failed${NC}"
    exit 1
fi

# Test 3: Ollama Configuration Check
echo "3. Checking Ollama configuration..."

if grep -q "OLLAMA_URL.*ollama-host-service" /tmp/dev-test.yaml; then
    echo -e "   ${GREEN}✓ Ollama URL points to host service${NC}"
else
    echo -e "   ${RED}✗ Ollama URL not configured correctly${NC}"
    exit 1
fi

if grep -q "USE_EMBEDDED_OLLAMA.*false" /tmp/dev-test.yaml; then
    echo -e "   ${GREEN}✓ Embedded Ollama disabled for development${NC}"
else
    echo -e "   ${RED}✗ Embedded Ollama not disabled${NC}"
    exit 1
fi

if grep -q "name: ollama-host-service" /tmp/dev-test.yaml; then
    echo -e "   ${GREEN}✓ Ollama host service included${NC}"
else
    echo -e "   ${RED}✗ Ollama host service missing${NC}"
    exit 1
fi

# Test 4: Network Policy Check
echo "4. Checking network policies..."

if grep -q "port: 11434" /tmp/dev-test.yaml; then
    echo -e "   ${GREEN}✓ Ollama port (11434) configured${NC}"
else
    echo -e "   ${RED}✗ Ollama port not found in configuration${NC}"
    exit 1
fi

# Test 5: Namespace Configuration
echo "5. Checking namespace configuration..."

if grep -q "namespace: atlas-mcp-dev" /tmp/dev-test.yaml; then
    echo -e "   ${GREEN}✓ Development namespace configured correctly${NC}"
else
    echo -e "   ${RED}✗ Development namespace not configured${NC}"
    exit 1
fi

# Test 6: Resource Count Validation
echo "6. Validating resource counts..."

DEPLOYMENTS=$(grep -c "kind: Deployment" /tmp/dev-test.yaml)
SERVICES=$(grep -c "kind: Service" /tmp/dev-test.yaml)
CONFIGMAPS=$(grep -c "kind: ConfigMap" /tmp/dev-test.yaml)

if [ "$DEPLOYMENTS" -ge 15 ]; then
    echo -e "   ${GREEN}✓ Expected deployments found ($DEPLOYMENTS)${NC}"
else
    echo -e "   ${RED}✗ Not enough deployments found ($DEPLOYMENTS < 15)${NC}"
    exit 1
fi

if [ "$SERVICES" -ge 10 ]; then
    echo -e "   ${GREEN}✓ Expected services found ($SERVICES)${NC}"
else
    echo -e "   ${RED}✗ Not enough services found ($SERVICES < 10)${NC}"
    exit 1
fi

# Cleanup
rm -f /tmp/base-test.yaml /tmp/dev-test.yaml

echo ""
echo -e "${GREEN}🎉 All tests passed! Kubernetes configuration is ready.${NC}"
echo ""
echo "Next steps:"
echo "1. Start Kind cluster: kind create cluster --config=kind-config.yaml"
echo "2. Deploy Atlas: make install-dev"
echo "3. Check status: make status-dev"
echo "4. Access Atlas: make port-forward-atlas-dev"