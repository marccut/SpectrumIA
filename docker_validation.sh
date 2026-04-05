#!/bin/bash

# Docker validation script for SpectrumIA
# Checks Docker setup and health of all services

echo "🔍 SpectrumIA Docker Validation"
echo "================================"
echo ""

# Check Docker installation
echo "📋 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✅ Docker: $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi
echo "✅ Docker Compose: $(docker-compose --version)"
echo ""

# Validate docker-compose.yml syntax
echo "📋 Validating docker-compose.yml..."
if docker-compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has syntax errors"
    docker-compose config
    exit 1
fi
echo ""

# Check Dockerfile
echo "📋 Validating Dockerfile..."
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile exists"
else
    echo "❌ Dockerfile not found"
    exit 1
fi
echo ""

# List services
echo "📋 Services defined in docker-compose.yml:"
docker-compose config --services | while read service; do
    echo "  ✓ $service"
done
echo ""

# Test build (optional)
read -p "🔨 Build Docker image? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Building image..."
    docker-compose build
    if [ $? -eq 0 ]; then
        echo "✅ Build successful"
    else
        echo "❌ Build failed"
        exit 1
    fi
fi
echo ""

# Test services (optional)
read -p "🚀 Start services? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting services..."
    docker-compose up -d

    sleep 10

    echo ""
    echo "📊 Service Health:"
    echo "==================="

    # Check SpectrumIA
    if docker-compose logs spectrumia | grep -q "streamlit run"; then
        echo "✅ SpectrumIA: Running"
    else
        echo "⚠️  SpectrumIA: Starting (check logs)"
    fi

    # Check PostgreSQL
    if docker exec spectrumia_postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL: Healthy"
    else
        echo "⚠️  PostgreSQL: Starting"
    fi

    # Check Redis
    if docker exec spectrumia_redis redis-cli ping | grep -q PONG; then
        echo "✅ Redis: Healthy"
    else
        echo "⚠️  Redis: Starting"
    fi

    # Check Prometheus
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo "✅ Prometheus: Healthy (http://localhost:9090)"
    else
        echo "⚠️  Prometheus: Starting"
    fi

    # Check Grafana
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        echo "✅ Grafana: Healthy (http://localhost:3000)"
    else
        echo "⚠️  Grafana: Starting"
    fi

    # Check Elasticsearch
    if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
        echo "✅ Elasticsearch: Healthy"
    else
        echo "⚠️  Elasticsearch: Starting"
    fi

    # Check Kibana
    if curl -s http://localhost:5601/api/status > /dev/null 2>&1; then
        echo "✅ Kibana: Healthy (http://localhost:5601)"
    else
        echo "⚠️  Kibana: Starting"
    fi

    echo ""
    echo "🌐 Access URLs:"
    echo "==============="
    echo "SpectrumIA:   http://localhost:8501"
    echo "Prometheus:   http://localhost:9090"
    echo "Grafana:      http://localhost:3000 (admin/admin)"
    echo "Kibana:       http://localhost:5601"
    echo ""

    read -p "Stop services? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down
        echo "✅ Services stopped"
    fi
fi

echo ""
echo "✅ Validation complete!"
