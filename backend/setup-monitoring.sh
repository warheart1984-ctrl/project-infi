#!/bin/bash

# AWS Monitoring Setup Script

set -e

echo "🔍 AWS Monitoring Setup"
echo "======================"
echo ""

# Get configuration
REGION=${1:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Region: $REGION"
echo "Account ID: $ACCOUNT_ID"
echo ""

# Create log groups
echo "📝 Creating log groups..."
aws logs create-log-group --log-group-name /ecs/aais-backend --region $REGION 2>/dev/null || echo "Backend log group exists"
aws logs create-log-group --log-group-name /ecs/aais-frontend --region $REGION 2>/dev/null || echo "Frontend log group exists"

# Set retention
aws logs put-retention-policy --log-group-name /ecs/aais-backend --retention-in-days 30 --region $REGION
aws logs put-retention-policy --log-group-name /ecs/aais-frontend --retention-in-days 30 --region $REGION

echo "✓ Log groups created"
echo ""

# Enable Container Insights
echo "📊 Enabling Container Insights..."
aws ecs update-cluster-settings \
  --cluster aais-cluster \
  --settings name=containerInsights,value=enabled \
  --region $REGION

echo "✓ Container Insights enabled"
echo ""

# Create SNS topic
echo "📧 Creating SNS topic for alerts..."
SNS_TOPIC=$(aws sns create-topic \
  --name aais-alerts \
  --region $REGION \
  --query 'TopicArn' \
  --output text)

echo "SNS Topic: $SNS_TOPIC"
echo ""

# Create alarms
echo "🚨 Creating CloudWatch alarms..."

# CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name aais-backend-cpu-high \
  --alarm-description "Alert when backend CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=aais-backend Name=ClusterName,Value=aais-cluster \
  --alarm-actions arn:aws:sns:$REGION:$ACCOUNT_ID:aais-alerts \
  --region $REGION

echo "✓ CPU alarm created"

# Memory alarm
aws cloudwatch put-metric-alarm \
  --alarm-name aais-backend-memory-high \
  --alarm-description "Alert when backend memory exceeds 80%" \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=aais-backend Name=ClusterName,Value=aais-cluster \
  --alarm-actions arn:aws:sns:$REGION:$ACCOUNT_ID:aais-alerts \
  --region $REGION

echo "✓ Memory alarm created"

# RDS CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name aais-db-cpu-high \
  --alarm-description "Alert when database CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=DBInstanceIdentifier,Value=aais-db \
  --alarm-actions arn:aws:sns:$REGION:$ACCOUNT_ID:aais-alerts \
  --region $REGION

echo "✓ RDS alarm created"
echo ""

# Create dashboard
echo "📈 Creating CloudWatch dashboard..."
aws cloudwatch put-dashboard \
  --dashboard-name AAIS-Monitoring \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/ECS", "CPUUtilization", {"stat": "Average"}],
            [".", "MemoryUtilization", {"stat": "Average"}]
          ],
          "period": 300,
          "stat": "Average",
          "region": "'$REGION'",
          "title": "ECS Service Metrics"
        }
      },
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/RDS", "CPUUtilization", {"stat": "Average"}],
            [".", "DatabaseConnections", {"stat": "Average"}]
          ],
          "period": 300,
          "stat": "Average",
          "region": "'$REGION'",
          "title": "RDS Metrics"
        }
      }
    ]
  }' \
  --region $REGION

echo "✓ Dashboard created"
echo ""

echo "✅ Monitoring setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Subscribe to SNS topic for alerts"
echo "2. View dashboard: https://console.aws.amazon.com/cloudwatch/"
echo "3. Configure additional alarms as needed"
echo "4. Setup log insights queries"
echo ""
echo "SNS Topic ARN: $SNS_TOPIC"
echo ""
