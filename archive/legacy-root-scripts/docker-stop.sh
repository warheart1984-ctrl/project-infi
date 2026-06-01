#!/bin/bash

# Stop AAIS services

echo "🛑 Stopping AAIS..."

docker-compose down

echo "✅ AAIS stopped"
echo ""
echo "💾 Data is preserved in volumes"
echo "🗑️  To remove all data: docker-compose down -v"
echo ""
