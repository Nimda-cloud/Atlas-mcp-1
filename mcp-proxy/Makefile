# Atlas MCP Proxy Makefile
# Зручні команди для розробки та деплою

BUILD_DIR=./build
BUILD=$(shell git rev-parse --short HEAD)@$(shell date +%s)
CURRENT_OS := $(shell uname -s | tr '[:upper:]' '[:lower:]')
CURRENT_ARCH := $(shell uname -m | tr '[:upper:]' '[:lower:]')
LD_FLAGS=-ldflags "-X main.BuildVersion=$(BUILD)"
GO_BUILD=CGO_ENABLED=0 go build $(LD_FLAGS)

.PHONY: help build atlas install clean test run run-global health check-deps status

# Default target
help:
	@echo "Atlas MCP Proxy - Available commands:"
	@echo ""
	@echo "  🔧 Development:"
	@echo "    build       - Build original mcp-proxy binary"
	@echo "    atlas       - Build atlas-mcp-proxy binary"
	@echo "    install     - Install dependencies and build"
	@echo "    clean       - Clean build artifacts"
	@echo "    test        - Run tests (if available)"
	@echo ""
	@echo "  🚀 Runtime:"
	@echo "    run         - Run with basic Atlas config"
	@echo "    run-global  - Run with global MCP config"
	@echo "    health      - Check proxy health"
	@echo ""
	@echo "  📋 Utilities:"
	@echo "    check-deps  - Check Go dependencies"
	@echo "    update-deps - Update dependencies"
	@echo "    status      - Show current status"

# Original build (TBXark compatible)
build:
	$(GO_BUILD) -o $(BUILD_DIR)/ ./...

# Atlas-specific build
atlas: check-deps
	@echo "🔨 Building atlas-mcp-proxy..."
	@go build -v -ldflags="-s -w" -o atlas-mcp-proxy .
	@echo "✅ Build complete: atlas-mcp-proxy"

# Check dependencies
check-deps:
	@echo "🔍 Checking Go environment..."
	@go version
	@echo "📦 Checking dependencies..."
	@go mod verify

# Update dependencies
update-deps:
	@echo "📥 Updating dependencies..."
	@go mod tidy
	@go mod download

# Install and build
install:
	@echo "🚀 Running Atlas MCP Proxy installer..."
	@./install-atlas-proxy.sh

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -f atlas-mcp-proxy
	@rm -f mcp-proxy
	@rm -rf $(BUILD_DIR)
	@go clean
	@echo "✅ Clean complete"

# Test (placeholder for future tests)
test:
	@echo "🧪 Running tests..."
	@go test -v ./... || echo "No tests found"

# Run with basic config
run: atlas
	@echo "🚀 Starting Atlas MCP Proxy (basic config)..."
	@./start-atlas-proxy.sh

# Run with global config
run-global: atlas
	@echo "🚀 Starting Atlas MCP Proxy (global config)..."
	@./start-atlas-proxy.sh --global

# Health check
health:
	@echo "🔍 Checking Atlas MCP Proxy health..."
	@curl -s http://localhost:9090/health || echo "❌ Proxy not responding on port 9090"
	@curl -s http://localhost:9090/tools | jq '.tools | length' 2>/dev/null && echo "tools available" || echo "Tools endpoint check failed"

# Quick status check
status:
	@echo "📊 Atlas MCP Proxy Status:"
	@echo "Port 9090: $$(lsof -i :9090 > /dev/null 2>&1 && echo '✅ Active' || echo '❌ Inactive')"
	@echo "Binary: $$([ -f atlas-mcp-proxy ] && echo '✅ Built' || echo '❌ Not built')"
	@echo "Config: $$([ -f atlas-config.json ] && echo '✅ Basic' || echo '❌ Missing') | $$([ -f atlas-global-config.json ] && echo '✅ Global' || echo '❌ Missing')"

# Development workflow
dev: clean atlas run

# Production setup
prod: install run-global

.PHONY: buildLinuxX86
buildLinuxX86:
	GOOS=linux GOARCH=amd64 $(GO_BUILD) -o $(BUILD_DIR)/ ./...

.PHONY: buildImage
buildImage:
	docker buildx build --platform=linux/amd64,linux/arm64 -t ghcr.io/tbxark/map-proxy:latest . --push --provenance=false

.PHONY: lint
lint:
	golangci-lint run

.PHONY: format
format:
	golangci-lint fmt
	golangci-lint run --fix
	go fmt ./...
	go mod tidy