#!/bin/bash
set -e

echo "🔧 Atlas Stack Test Script"
echo "=========================="

# Test basic connectivity
echo "🔍 Testing basic service connectivity..."

# Atlas Core
if curl -fsS "http://localhost:8000/status" >/dev/null 2>&1; then
    echo "✅ Atlas Core: OK"
else
    echo "❌ Atlas Core: FAILED"
    exit 1
fi

# Frontend
if curl -fsS "http://localhost:8080/health" >/dev/null 2>&1; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: FAILED"
    exit 1
fi

# TTS Service
if curl -fsS "http://localhost:4004/health" >/dev/null 2>&1; then
    echo "✅ TTS Service: OK"
else
    echo "❌ TTS Service: FAILED"
    exit 1
fi

# Redis
if docker exec atlas-redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis: OK"
else
    echo "❌ Redis: FAILED"
    exit 1
fi

# Redis Exporter
REDIS_UP=$(curl -s http://localhost:9121/metrics | grep "^redis_up " | cut -d' ' -f2)
if [[ "$REDIS_UP" == "1" ]]; then
    echo "✅ Redis Exporter: OK (redis_up = $REDIS_UP)"
else
    echo "❌ Redis Exporter: FAILED (redis_up = $REDIS_UP)"
    exit 1
fi

# Prometheus
if curl -fsS "http://localhost:9090/-/ready" >/dev/null 2>&1; then
    echo "✅ Prometheus: OK"
else
    echo "❌ Prometheus: FAILED"
    exit 1
fi

# Grafana
if curl -fsS "http://localhost:3000/api/health" >/dev/null 2>&1; then
    echo "✅ Grafana: OK"
else
    echo "❌ Grafana: FAILED"
    exit 1
fi

echo ""
echo "🎉 All services are working correctly!"
echo ""
echo "📊 Service URLs:"
echo "   - Atlas Core: http://localhost:8000"
echo "   - Frontend: http://localhost:8080"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000 (admin/atlas_admin)"
echo "   - Redis Metrics: http://localhost:9121/metrics"
echo ""
echo "🔧 Container status:"
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
