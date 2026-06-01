#!/bin/bash

# Deploy to AWS ECS

set -e

echo "🚀 Deploying to AWS ECS"
echo "======================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    echo "Visit: https://aws.amazon.com/cli/"
    exit 1
fi

echo "✅ AWS CLI found"
echo ""

# Get AWS configuration
read -p "Enter AWS region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Enter AWS account ID: " AWS_ACCOUNT_ID
read -p "Enter ECS cluster name: " CLUSTER_NAME
read -p "Enter ECR repository name (backend): " BACKEND_REPO
read -p "Enter ECR repository name (frontend): " FRONTEND_REPO

echo ""
echo "📦 Building Docker images..."

# Build images
docker build -t $BACKEND_REPO:latest -f Dockerfile .
docker build -t $FRONTEND_REPO:latest -f Dockerfile.frontend .

echo ""
echo "🔐 Logging in to ECR..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo ""
echo "📤 Pushing images to ECR..."

# Tag and push backend
docker tag $BACKEND_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$BACKEND_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$BACKEND_REPO:latest

# Tag and push frontend
docker tag $FRONTEND_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$FRONTEND_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$FRONTEND_REPO:latest

echo ""
echo "✅ Images pushed to ECR"
echo ""
echo "📝 Next steps:"
echo "1. Update ECS task definitions with new image URIs"
echo "2. Update ECS services to use new task definitions"
echo "3. Monitor deployment in AWS Console"
echo ""
echo "🔗 AWS Console: https://console.aws.amazon.com/ecs"
echo ""
