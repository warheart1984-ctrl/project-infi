#!/bin/bash

# AAIS Docker Setup Script

set -e

echo "🐳 AAIS Docker Setup"
echo "==================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Docker found"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker Compose found"

# Create SSL directory if it doesn't exist
if [ ! -d "ssl" ]; then
    echo "📁 Creating SSL directory..."
    mkdir -p ssl
fi

# Generate self-signed SSL certificate if it doesn't exist
if [ ! -f "ssl/certificate.crt" ] || [ ! -f "ssl/private.key" ]; then
    echo "🔐 Generating self-signed SSL certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/private.key \
        -out ssl/certificate.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    echo "✅ SSL certificate generated"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created (please update with your settings)"
fi

# Build images
echo "🔨 Building Docker images..."
docker-compose build

echo ""
echo "✅ Docker setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env file with your settings"
echo "2. Run: docker-compose up -d"
echo "3. Access the application at http://localhost:3000"
echo "4. API is available at http://localhost:5000"
echo ""
echo "📚 Useful commands:"
echo "  docker-compose up -d          # Start all services"
echo "  docker-compose down           # Stop all services"
echo "  docker-compose logs -f        # View logs"
echo "  docker-compose ps             # View running services"
echo "  docker-compose exec backend bash  # Access backend shell"
echo ""
