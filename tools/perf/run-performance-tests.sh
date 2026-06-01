#!/bin/bash

# Performance testing script

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
cd "${repo_root}"

echo "📊 Performance Testing Suite"
echo "=============================="
echo ""

# Check if server is running
echo "Checking if server is running..."
if ! curl -s http://localhost:5000/health > /dev/null; then
    echo "❌ Server not running. Start it with: docker-compose up"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q locust requests

echo ""
echo "🧪 Running performance tests..."
echo ""

# Run Python performance tests
echo "1. Running Python performance tests..."
python tools/perf/performance_test.py

echo ""
echo "2. Running Apache Bench tests..."
echo ""

# Health endpoint
echo "Testing /health endpoint (1000 requests, 10 concurrent):"
ab -n 1000 -c 10 -q http://localhost:5000/health

echo ""
echo "3. Running wrk tests..."
echo ""

if command -v wrk &> /dev/null; then
    echo "Testing with wrk (4 threads, 100 connections, 30 seconds):"
    wrk -t4 -c100 -d30s http://localhost:5000/health
else
    echo "⚠ wrk not installed. Skipping wrk tests."
fi

echo ""
echo "✅ Performance testing complete!"
echo ""
echo "📝 Results Summary:"
echo "  - Check response times"
echo "  - Monitor error rates"
echo "  - Review resource usage"
echo "  - Identify bottlenecks"
echo ""
