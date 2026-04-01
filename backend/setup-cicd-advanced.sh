#!/bin/bash

# Setup advanced CI/CD pipeline

set -e

echo "🚀 Setting up advanced CI/CD pipeline"
echo "======================================"
echo ""

# Check if .gitlab-ci.yml exists
if [ -f ".gitlab-ci.yml" ]; then
    echo "💾 Backing up existing .gitlab-ci.yml"
    cp .gitlab-ci.yml .gitlab-ci.yml.backup
fi

# Copy advanced configuration
echo "📝 Copying advanced CI/CD configuration..."
cp .gitlab-ci-advanced.yml .gitlab-ci.yml

echo "✓ Advanced CI/CD configuration installed"
echo ""

echo "📋 Configuration checklist:"
echo "  [ ] Set CI_REGISTRY_USER variable"
echo "  [ ] Set CI_REGISTRY_PASSWORD variable"
echo "  [ ] Set STAGING_SERVER variable"
echo "  [ ] Set STAGING_USER variable"
echo "  [ ] Set STAGING_SSH_KEY variable"
echo "  [ ] Set PRODUCTION_SERVER variable"
echo "  [ ] Set PRODUCTION_USER variable"
echo "  [ ] Set PRODUCTION_SSH_KEY variable"
echo "  [ ] Set SLACK_WEBHOOK_URL variable (optional)"
echo ""

echo "📚 Next steps:"
echo "1. Go to Project Settings → CI/CD → Variables"
echo "2. Add all required variables"
echo "3. Commit and push .gitlab-ci.yml"
echo "4. Monitor pipeline in CI/CD → Pipelines"
echo ""

echo "📚 Pipeline stages:"
echo "  1. Validate - Code quality checks"
echo "  2. Test - Unit, integration, performance tests"
echo "  3. Build - Docker image building"
echo "  4. Security - SAST, container, dependency scanning"
echo "  5. Deploy - Staging and production deployment"
echo "  6. Monitor - Health checks and notifications"
echo ""

echo "✅ Advanced CI/CD pipeline setup complete!"
echo ""
