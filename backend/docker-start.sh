#!/bin/bash

# Start AAIS with Docker Compose

echo "🚀 Starting AAIS..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run docker-setup.sh first."
    exit 1
fi

# Start services
docker-compose up -d

echo ""
echo "✅ AAIS is starting..."
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🌐 Access points:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:5000"
echo "  Database:  localhost:5432"
echo "  Redis:     localhost:6379"
echo ""
echo "📝 View logs: docker-compose logs -f"
echo ""
