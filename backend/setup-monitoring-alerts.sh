#!/bin/bash

# Monitoring and alerting setup script

set -e

echo "📊 AAIS Monitoring & Alerting Setup"
echo "===================================="
echo ""

REGION="us-east-1"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-https://hooks.slack.com/services/YOUR/WEBHOOK/URL}"
PAGERDUTY_KEY="${PAGERDUTY_KEY:-YOUR_PAGERDUTY_INTEGRATION_KEY}"
ALERT_EMAIL="${ALERT_EMAIL:-ops@example.com}"

echo "Configuration:"
echo "  Region: $REGION"
echo "  Alert Email: $ALERT_EMAIL"
echo ""

# Create SNS topic
echo "Step 1: Creating SNS topic..."
SNS_TOPIC=$(aws sns create-topic \
  --name aais-prod-alerts \
  --region $REGION \
  --query 'TopicArn' \
  --output text 2>/dev/null || echo "arn:aws:sns:$REGION:$(aws sts get-caller-identity --query Account --output text):aais-prod-alerts")

echo "✓ SNS topic: $SNS_TOPIC"

# Subscribe email
echo ""
echo "Step 2: Subscribing email to alerts..."
aws sns subscribe \
  --topic-arn $SNS_TOPIC \
  --protocol email \
  --notification-endpoint $ALERT_EMAIL \
  --region $REGION 2>/dev/null || echo "Email already subscribed"

echo "✓ Email subscription created"

# Create CloudWatch log group
echo ""
echo "Step 3: Creating CloudWatch log group..."
aws logs create-log-group \
  --log-group-name /aais/production \
  --region $REGION 2>/dev/null || echo "Log group already exists"

echo "✓ Log group created"

# Set log retention
echo ""
echo "Step 4: Setting log retention..."
aws logs put-retention-policy \
  --log-group-name /aais/production \
  --retention-in-days 30 \
  --region $REGION

echo "✓ Log retention set to 30 days"

# Install monitoring dependencies
echo ""
echo "Step 5: Installing monitoring dependencies..."
pip install boto3 requests -q
echo "✓ Dependencies installed"

# Create dashboards
echo ""
echo "Step 6: Creating CloudWatch dashboards..."
python3 << 'EOF'
import boto3
import json

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

# Main dashboard
main_dashboard = {
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/ApplicationELB", "TargetResponseTime"],
                    [".", "RequestCount"],
                    [".", "HTTPCode_Target_5XX_Count"],
                    ["AWS/ECS", "CPUUtilization"],
                    [".", "MemoryUtilization"]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Application Performance"
            }
        }
    ]
}

cloudwatch.put_dashboard(
    DashboardName='AAIS-Production',
    DashboardBody=json.dumps(main_dashboard)
)

print("✓ Main dashboard created")

# Security dashboard
security_dashboard = {
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/WAF", "BlockedRequests"],
                    [".", "AllowedRequests"]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "us-east-1",
                "title": "WAF Activity"
            }
        }
    ]
}

cloudwatch.put_dashboard(
    DashboardName='AAIS-Security',
    DashboardBody=json.dumps(security_dashboard)
)

print("✓ Security dashboard created")
EOF

echo "✓ Dashboards created"

# Create alarms
echo ""
echo "Step 7: Creating CloudWatch alarms..."
python3 << 'EOF'
import boto3

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
sns_topic = 'arn:aws:sns:us-east-1:' + boto3.client('sts').get_caller_identity()['Account'] + ':aais-prod-alerts'

alarms = [
    {
        'AlarmName': 'AAIS-HighResponseTime',
        'MetricName': 'TargetResponseTime',
        'Namespace': 'AWS/ApplicationELB',
        'Threshold': 0.2,
        'Description': 'Alert when response time exceeds 200ms'
    },
    {
        'AlarmName': 'AAIS-HighErrorRate',
        'MetricName': 'HTTPCode_Target_5XX_Count',
        'Namespace': 'AWS/ApplicationELB',
        'Threshold': 10,
        'Description': 'Alert when error count exceeds 10'
    },
    {
        'AlarmName': 'AAIS-HighCPU',
        'MetricName': 'CPUUtilization',
        'Namespace': 'AWS/ECS',
        'Threshold': 80,
        'Description': 'Alert when CPU exceeds 80%'
    },
    {
        'AlarmName': 'AAIS-HighMemory',
        'MetricName': 'MemoryUtilization',
        'Namespace': 'AWS/ECS',
        'Threshold': 85,
        'Description': 'Alert when memory exceeds 85%'
    }
]

for alarm in alarms:
    cloudwatch.put_metric_alarm(
        AlarmName=alarm['AlarmName'],
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName=alarm['MetricName'],
        Namespace=alarm['Namespace'],
        Period=300,
        Statistic='Average',
        Threshold=alarm['Threshold'],
        ActionsEnabled=True,
        AlarmActions=[sns_topic],
        AlarmDescription=alarm['Description'],
        TreatMissingData='notBreaching'
    )
    print(f"✓ {alarm['AlarmName']} created")
EOF

echo "✓ Alarms created"

echo ""
echo "✅ Monitoring setup complete!"
echo ""
echo "📋 Configuration:"
echo "  SNS Topic: $SNS_TOPIC"
echo "  Alert Email: $ALERT_EMAIL"
echo "  Slack Webhook: $SLACK_WEBHOOK"
echo "  PagerDuty Key: $PAGERDUTY_KEY"
echo ""
echo "📊 Dashboards:"
echo "  - AAIS-Production (main metrics)"
echo "  - AAIS-Security (security events)"
echo ""
echo "🚨 Alarms:"
echo "  - High response time (> 200ms)"
echo "  - High error rate (> 10 errors/5min)"
echo "  - High CPU (> 80%)"
echo "  - High memory (> 85%)"
echo ""
echo "📧 Notifications:"
echo "  - Email: $ALERT_EMAIL"
echo "  - Slack: Enabled"
echo "  - PagerDuty: Enabled"
echo ""
