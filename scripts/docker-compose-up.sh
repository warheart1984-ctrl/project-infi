#!/usr/bin/env bash
set -e

# AAES-OS Development Environment Setup

echo "🚀 Starting AAES-OS Docker Compose environment..."

# Check if .env exists, create if not
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        cat > .env << 'EOF'
NODE_ENV=development
SOVREN_LAW_KEY=dev-key-change-in-production
LOG_LEVEL=info
EOF
    fi
fi

# Pull latest images
echo "📦 Pulling latest images..."
docker compose pull --ignore-buildable || true

# Build images
echo "🔨 Building Docker images..."
docker compose build --no-cache

# Start services
echo "▶️  Starting services..."
docker compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to become healthy..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker compose ps | grep -q "healthy"; then
        echo "✅ Services are healthy!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Waiting... ($attempt/$max_attempts)"
    sleep 2
done

# Show service status
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Environment ready!"
echo ""
echo "Available services:"
echo "  • Ops Console:        http://localhost:3001"
echo "  • Platform API:       http://localhost:3000"
echo "  • Platform Web:       http://localhost:3002"
echo "  • Sovereign Control:  http://localhost:3003"
echo "  • USS API:            http://localhost:3004"
echo ""
echo "View logs with: docker compose logs -f <service-name>"
echo "Stop all with:  docker compose down"
