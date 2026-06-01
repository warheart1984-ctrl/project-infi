#!/bin/bash

# Deploy to Heroku

set -e

echo "🚀 Deploying to Heroku"
echo "======================"
echo ""

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it first."
    echo "Visit: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

echo "✅ Heroku CLI found"
echo ""

# Check if logged in
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Not logged in to Heroku. Running: heroku login"
    heroku login
fi

echo "✅ Logged in to Heroku"
echo ""

# Get app name
read -p "Enter Heroku app name: " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo "❌ App name is required"
    exit 1
fi

echo ""
echo "📦 Setting up Heroku app: $APP_NAME"
echo ""

# Create app if it doesn't exist
if ! heroku apps:info -a $APP_NAME &> /dev/null; then
    echo "Creating Heroku app..."
    heroku create $APP_NAME
fi

# Add PostgreSQL addon
echo "Adding PostgreSQL addon..."
heroku addons:create heroku-postgresql:hobby-dev -a $APP_NAME || echo "PostgreSQL addon already exists"

# Add Redis addon
echo "Adding Redis addon..."
heroku addons:create heroku-redis:premium-0 -a $APP_NAME || echo "Redis addon already exists"

# Set environment variables
echo "Setting environment variables..."
heroku config:set ENVIRONMENT=production -a $APP_NAME
heroku config:set DEBUG=False -a $APP_NAME
heroku config:set LOG_LEVEL=INFO -a $APP_NAME
heroku config:set SECRET_KEY=$(openssl rand -hex 32) -a $APP_NAME
heroku config:set RATE_LIMIT=60 -a $APP_NAME

echo ""
echo "🔗 Adding Heroku remote..."
heroku git:remote -a $APP_NAME

echo ""
echo "📤 Deploying application..."
git push heroku main

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 View logs:"
echo "  heroku logs --tail -a $APP_NAME"
echo ""
echo "🌐 Open app:"
echo "  heroku open -a $APP_NAME"
echo ""
echo "📝 View config:"
echo "  heroku config -a $APP_NAME"
echo ""
