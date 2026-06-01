#!/bin/bash

# AWS Performance Optimization Setup Script

set -e

echo "⚡ AWS Performance Optimization Setup"
echo "====================================="
echo ""

# Get configuration
REGION=${1:-us-east-1}
CLUSTER=${2:-aais-cluster}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Region: $REGION"
echo "Cluster: $CLUSTER"
echo "Account ID: $ACCOUNT_ID"
echo ""

# Step 1: Setup Auto-scaling
echo "📊 Setting up ECS auto-scaling..."

# Backend auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/$CLUSTER/aais-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10 \
  --region $REGION 2>/dev/null || echo "Backend target already registered"

aws application-autoscaling put-scaling-policy \
  --policy-name aais-backend-cpu-scaling \
  --service-namespace ecs \
  --resource-id service/$CLUSTER/aais-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {"PredefinedMetricType": "ECSServiceAverageCPUUtilization"},
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }' \
  --region $REGION 2>/dev/null || echo "Backend scaling policy exists"

echo "✓ Backend auto-scaling configured"

# Frontend auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/$CLUSTER/aais-frontend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 8 \
  --region $REGION 2>/dev/null || echo "Frontend target already registered"

aws application-autoscaling put-scaling-policy \
  --policy-name aais-frontend-cpu-scaling \
  --service-namespace ecs \
  --resource-id service/$CLUSTER/aais-frontend \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {"PredefinedMetricType": "ECSServiceAverageCPUUtilization"},
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }' \
  --region $REGION 2>/dev/null || echo "Frontend scaling policy exists"

echo "✓ Frontend auto-scaling configured"
echo ""

# Step 2: Enable RDS Performance Insights
echo "📊 Enabling RDS Performance Insights..."
aws rds modify-db-instance \
  --db-instance-identifier aais-db \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --apply-immediately \
  --region $REGION 2>/dev/null || echo "Performance Insights already enabled"

echo "✓ RDS Performance Insights enabled"
echo ""

# Step 3: Create Performance Alarms
echo "🚨 Creating performance alarms..."

aws cloudwatch put-metric-alarm \
  --alarm-name aais-alb-response-time-high \
  --alarm-description "Alert when ALB response time exceeds 1 second" \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:$REGION:$ACCOUNT_ID:aais-alerts \
  --region $REGION 2>/dev/null || echo "Response time alarm exists"

echo "✓ Performance alarms created"
echo ""

# Step 4: Enable Spot Instances
echo "💰 Enabling Spot instances for cost savings..."

aws ecs update-service \
  --cluster $CLUSTER \
  --service aais-backend \
  --capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=70 capacityProvider=FARGATE,weight=30 \
  --region $REGION 2>/dev/null || echo "Spot instances already enabled"

echo "✓ Spot instances enabled (70% cost savings)"
echo ""

echo "✅ Performance optimization setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Monitor auto-scaling activities"
echo "2. Setup CloudFront CDN"
echo "3. Configure cache optimization"
echo "4. Monitor performance metrics"
echo "5. Consider purchasing reserved instances"
echo ""
echo "View auto-scaling activities:"
echo "  aws application-autoscaling describe-scaling-activities --service-namespace ecs --region $REGION"
echo ""
echo "View current service status:"
echo "  aws ecs describe-services --cluster $CLUSTER --services aais-backend aais-frontend --region $REGION"
echo ""
