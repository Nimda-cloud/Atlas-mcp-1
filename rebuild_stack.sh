#!/bin/bash
set -e

echo "🔄 Atlas Stack Rebuild Script"
echo "============================="

# Stop all services in correct order
echo "🛑 Stopping all services..."
docker compose --profile monitoring --profile mcp --profile macos down

# Clean up old containers, networks, and volumes (optional)
if [[ "$1" == "--clean" ]]; then
    echo "🧹 Cleaning up old containers and volumes..."
    docker compose down --volumes --remove-orphans
    docker system prune -f
    echo "✅ Cleanup completed"
fi

# Build with no cache if requested
BUILD_ARGS=""
if [[ "$1" == "--no-cache" || "$2" == "--no-cache" ]]; then
    BUILD_ARGS="--no-cache"
    echo "🏗️  Building with no cache..."
fi

# Step 1: Start core services first
echo "🚀 Starting core services..."
docker compose up --build $BUILD_ARGS -d

# Wait for core services to be healthy
echo "⏳ Waiting for core services to be ready..."
for i in {1..40}; do
    if curl -fsS "http://localhost:8000/status" >/dev/null 2>&1; then
        echo "✅ Atlas core is ready"
        break
    fi
    sleep 1
done

for i in {1..30}; do
    if curl -fsS "http://localhost:8080/health" >/dev/null 2>&1; then
        echo "✅ Frontend is ready"
        break
    fi
    sleep 1
done

for i in {1..30}; do
    if curl -fsS "http://localhost:4004/health" >/dev/null 2>&1; then
        echo "✅ TTS service is ready"
        break
    fi
    sleep 1
done

# Step 2: Start monitoring services
echo "📊 Starting monitoring services..."
docker compose --profile monitoring up -d

# Wait for Redis to be ready before starting exporter
echo "⏳ Waiting for Redis to be ready..."
for i in {1..20}; do
    if docker exec atlas-redis redis-cli ping >/dev/null 2>&1; then
        echo "✅ Redis is ready"
        break
    fi
    sleep 1
done

# Verify Redis exporter connectivity
echo "🔍 Verifying Redis exporter connectivity..."
for i in {1..20}; do
    if curl -fsS "http://localhost:9121/metrics" | grep -q "redis_up"; then
        echo "✅ Redis exporter is working"
        break
    fi
    sleep 1
done

# Step 3: Start MCP services
echo "🔧 Starting MCP services..."
docker compose --profile mcp --profile macos up -d

echo "📦 Final stack status:"
docker compose ps

echo ""
echo "🎉 Atlas stack rebuild completed successfully!"
echo "📊 Access points:"
echo "   - Atlas Core: http://localhost:8000"
echo "   - Frontend: http://localhost:8080"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000 (admin/atlas_admin)"
echo "   - Redis Metrics: http://localhost:9121/metrics"
