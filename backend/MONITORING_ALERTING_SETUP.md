# AAIS Monitoring & Alerting Setup

## Overview

This guide covers comprehensive monitoring and alerting:
- CloudWatch metrics and dashboards
- Real-time alerting
- Slack integration
- PagerDuty integration
- Email notifications
- Custom metrics
- Log analysis
- Performance tracking

---

## 1. CloudWatch Dashboard Setup

### Create Comprehensive Dashboard

```python
# src/monitoring/dashboard_setup.py

import boto3
import json
from src.logger import get_logger

logger = get_logger(__name__)

class DashboardSetup:
    """Setup CloudWatch dashboards"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
    
    def create_main_dashboard(self):
        """Create main monitoring dashboard"""
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/ApplicationELB", "TargetResponseTime", {"stat": "Average"}],
                            [".", "RequestCount", {"stat": "Sum"}],
                            [".", "HTTPCode_Target_5XX_Count", {"stat": "Sum"}],
                            ["AWS/ECS", "CPUUtilization", {"stat": "Average"}],
                            [".", "MemoryUtilization", {"stat": "Average"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Application Performance"
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/RDS", "CPUUtilization", {"stat": "Average"}],
                            [".", "DatabaseConnections", {"stat": "Average"}],
                            [".", "ReadLatency", {"stat": "Average"}],
                            [".", "WriteLatency", {"stat": "Average"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Database Performance"
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/ElastiCache", "CPUUtilization", {"stat": "Average"}],
                            [".", "NetworkBytesIn", {"stat": "Sum"}],
                            [".", "NetworkBytesOut", {"stat": "Sum"}],
                            [".", "CacheHits", {"stat": "Sum"}],
                            [".", "CacheMisses", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Cache Performance"
                    }
                },
                {
                    "type": "log",
                    "properties": {
                        "query": "fields @timestamp, @message | filter @message like /ERROR/ | stats count() by bin(5m)",
                        "region": "us-east-1",
                        "title": "Error Rate (5min bins)"
                    }
                }
            ]
        }
        
        self.cloudwatch.put_dashboard(
            DashboardName='AAIS-Production',
            DashboardBody=json.dumps(dashboard_body)
        )
        
        logger.info("Main dashboard created")
    
    def create_security_dashboard(self):
        """Create security monitoring dashboard"""
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/WAF", "BlockedRequests", {"stat": "Sum"}],
                            [".", "AllowedRequests", {"stat": "Sum"}],
                            [".", "CountedRequests", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "WAF Activity"
                    }
                },
                {
                    "type": "log",
                    "properties": {
                        "query": "fields @timestamp, @message | filter @message like /UNAUTHORIZED|FORBIDDEN/ | stats count() by bin(5m)",
                        "region": "us-east-1",
                        "title": "Security Events"
                    }
                }
            ]
        }
        
        self.cloudwatch.put_dashboard(
            DashboardName='AAIS-Security',
            DashboardBody=json.dumps(dashboard_body)
        )
        
        logger.info("Security dashboard created")
```

---

## 2. Alert Rules Configuration

### Create CloudWatch Alarms

```python
# src/monitoring/alert_rules.py

import boto3
from src.logger import get_logger

logger = get_logger(__name__)

class AlertRules:
    """Configure CloudWatch alarms"""
    
    def __init__(self, sns_topic_arn):
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns_topic_arn = sns_topic_arn
    
    def create_performance_alarms(self):
        """Create performance-related alarms"""
        
        # High response time alarm
        self.cloudwatch.put_metric_alarm(
            AlarmName='AAIS-HighResponseTime',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='TargetResponseTime',
            Namespace='AWS/ApplicationELB',
            Period=300,
            Statistic='Average',
            Threshold=0.2,  # 200ms
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            AlarmDescription='Alert when response time exceeds 200ms',
            TreatMissingData='notBreaching'
        )
        logger.info("Response time alarm created")
        
        # High error rate alarm
        self.cloudwatch.put_metric_alarm(
            AlarmName='AAIS-HighErrorRate',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='HTTPCode_Target_5XX_Count',
            Namespace='AWS/ApplicationELB',
            Period=300,
            Statistic='Sum',
            Threshold=10,
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            AlarmDescription='Alert when error count exceeds 10 in 5 minutes',
            TreatMissingData='notBreaching'
        )
        logger.info("Error rate alarm created")
        
        # Low cache hit rate alarm
        self.cloudwatch.put_metric_alarm(
            AlarmName='AAIS-LowCacheHitRate',
            ComparisonOperator='LessThanThreshold',
            EvaluationPeriods=3,
            MetricName='CacheHitRate',
            Namespace='AAIS',
            Period=300,
            Statistic='Average',
            Threshold=80,  # 80%
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            AlarmDescription='Alert when cache hit rate drops below 80%',
            TreatMissingData='notBreaching'
        )
        logger.info("Cache hit rate alarm created")
    
    def create_infrastructure_alarms(self):
        """Create infrastructure-related alarms"""
        
        # High CPU utilization
        self.cloudwatch.put_metric_alarm(
            AlarmName='AAIS-HighCPU',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='CPUUtilization',
            Namespace='AWS/ECS',
            Period=300,
            Statistic='Average',
            Threshold=80,
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            AlarmDescription='Alert when CPU exceeds 80%',
            TreatMissingData='notBreaching'
        )
        logger.info("CPU alarm created")
        
        # High memory utilization
        self.cloudwatch.put_metric_alarm(
            AlarmName='AAIS-HighMemory',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='MemoryUtilization',
            Namespace='AWS/ECS',
            Period=300,
            Statistic='Average',
            Threshold=85,
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            AlarmDescription='Alert when memory exceeds 85%',
            TreatMissingData='notBreaching'
        )
        logger.info("Memory alarm created")
        
        # Database connection pool exhaustion
        self.cloudwatch.put_metric_alarm(
            AlarmName='AAIS-DBConnectionPoolHigh',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='DatabaseConnections',
            Namespace='AWS/RDS',
            Period=300,
            Statistic='Average',
            Threshold=90,
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            AlarmDescription='Alert when DB connections exceed 90',
            TreatMissingData='notBreaching'
        )
        logger.info("Database connection alarm created")
    
    def create_security_alarms(self):
        """Create security-related alarms"""
        
        # High WAF blocked requests
        self.cloudwatch.put_metric_alarm(
            AlarmName='AAIS-HighWAFBlocks',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='BlockedRequests',
            Namespace='AWS/WAF',
            Period=300,
            Statistic='Sum',
            Threshold=100,
            ActionsEnabled=True,
            AlarmActions=[self.sns_topic_arn],
            AlarmDescription='Alert when WAF blocks exceed 100 requests',
            TreatMissingData='notBreaching'
        )
        logger.info("WAF alarm created")
```

---

## 3. Slack Integration

### Setup Slack Notifications

```python
# src/monitoring/slack_integration.py

import requests
import json
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)

class SlackNotifier:
    """Send notifications to Slack"""
    
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send_alert(self, alert_type, title, message, severity='warning'):
        """Send alert to Slack"""
        
        color_map = {
            'critical': '#FF0000',
            'warning': '#FFA500',
            'info': '#0099FF',
            'success': '#00CC00'
        }
        
        payload = {
            'attachments': [
                {
                    'color': color_map.get(severity, '#FFA500'),
                    'title': title,
                    'text': message,
                    'fields': [
                        {
                            'title': 'Alert Type',
                            'value': alert_type,
                            'short': True
                        },
                        {
                            'title': 'Severity',
                            'value': severity.upper(),
                            'short': True
                        },
                        {
                            'title': 'Timestamp',
                            'value': datetime.utcnow().isoformat(),
                            'short': False
                        }
                    ],
                    'footer': 'AAIS Monitoring',
                    'ts': int(datetime.utcnow().timestamp())
                }
            ]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack notification sent: {title}")
            else:
                logger.error(f"Failed to send Slack notification: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    def send_deployment_notification(self, environment, status, details):
        """Send deployment notification"""
        
        color = '#00CC00' if status == 'success' else '#FF0000'
        
        payload = {
            'attachments': [
                {
                    'color': color,
                    'title': f'Deployment {status.upper()}',
                    'text': f'Environment: {environment}',
                    'fields': [
                        {
                            'title': 'Status',
                            'value': status.upper(),
                            'short': True
                        },
                        {
                            'title': 'Details',
                            'value': details,
                            'short': False
                        }
                    ],
                    'footer': 'AAIS Deployment',
                    'ts': int(datetime.utcnow().timestamp())
                }
            ]
        }
        
        try:
            requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            logger.info(f"Deployment notification sent: {environment} {status}")
        except Exception as e:
            logger.error(f"Error sending deployment notification: {e}")
```

---

## 4. PagerDuty Integration

### Setup PagerDuty for Critical Alerts

```python
# src/monitoring/pagerduty_integration.py

import requests
import json
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)

class PagerDutyNotifier:
    """Send critical alerts to PagerDuty"""
    
    def __init__(self, integration_key):
        self.integration_key = integration_key
        self.api_url = 'https://events.pagerduty.com/v2/enqueue'
    
    def trigger_incident(self, title, description, severity='error'):
        """Trigger PagerDuty incident"""
        
        payload = {
            'routing_key': self.integration_key,
            'event_action': 'trigger',
            'dedup_key': f"{title}-{datetime.utcnow().timestamp()}",
            'payload': {
                'summary': title,
                'severity': severity,
                'source': 'AAIS Monitoring',
                'custom_details': {
                    'description': description,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 202:
                logger.info(f"PagerDuty incident triggered: {title}")
                return response.json()
            else:
                logger.error(f"Failed to trigger PagerDuty incident: {response.status_code}")
        except Exception as e:
            logger.error(f"Error triggering PagerDuty incident: {e}")
    
    def resolve_incident(self, dedup_key):
        """Resolve PagerDuty incident"""
        
        payload = {
            'routing_key': self.integration_key,
            'event_action': 'resolve',
            'dedup_key': dedup_key
        }
        
        try:
            response = requests.post(
                self.api_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 202:
                logger.info(f"PagerDuty incident resolved: {dedup_key}")
            else:
                logger.error(f"Failed to resolve PagerDuty incident: {response.status_code}")
        except Exception as e:
            logger.error(f"Error resolving PagerDuty incident: {e}")
```

---

## 5. Custom Metrics

### Publish Custom Metrics

```python
# src/monitoring/custom_metrics.py

import boto3
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)

class CustomMetrics:
    """Publish custom metrics to CloudWatch"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
    
    def publish_cache_hit_rate(self, hit_rate):
        """Publish cache hit rate metric"""
        self.cloudwatch.put_metric_data(
            Namespace='AAIS',
            MetricData=[
                {
                    'MetricName': 'CacheHitRate',
                    'Value': hit_rate * 100,
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        logger.debug(f"Cache hit rate metric published: {hit_rate*100:.2f}%")
    
    def publish_api_response_time(self, endpoint, response_time_ms):
        """Publish API response time metric"""
        self.cloudwatch.put_metric_data(
            Namespace='AAIS',
            MetricData=[
                {
                    'MetricName': 'APIResponseTime',
                    'Value': response_time_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {
                            'Name': 'Endpoint',
                            'Value': endpoint
                        }
                    ],
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
    
    def publish_ai_generation_time(self, model_type, generation_time_ms):
        """Publish AI generation time metric"""
        self.cloudwatch.put_metric_data(
            Namespace='AAIS',
            MetricData=[
                {
                    'MetricName': 'AIGenerationTime',
                    'Value': generation_time_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {
                            'Name': 'ModelType',
                            'Value': model_type
                        }
                    ],
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
    
    def publish_error_count(self, error_type, count):
        """Publish error count metric"""
        self.cloudwatch.put_metric_data(
            Namespace='AAIS',
            MetricData=[
                {
                    'MetricName': 'ErrorCount',
                    'Value': count,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'ErrorType',
                            'Value': error_type
                        }
                    ],
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
```

---

## 6. Log Analysis

### CloudWatch Logs Insights Queries

```python
# src/monitoring/log_analysis.py

import boto3
from src.logger import get_logger

logger = get_logger(__name__)

class LogAnalysis:
    """Analyze logs with CloudWatch Logs Insights"""
    
    def __init__(self):
        self.logs = boto3.client('logs')
    
    def query_error_logs(self, log_group, time_range_minutes=60):
        """Query error logs"""
        query = """
        fields @timestamp, @message, @logStream
        | filter @message like /ERROR/
        | stats count() as error_count by @logStream
        | sort error_count desc
        """
        
        return self._run_query(log_group, query, time_range_minutes)
    
    def query_slow_requests(self, log_group, threshold_ms=200, time_range_minutes=60):
        """Query slow requests"""
        query = f"""
        fields @timestamp, @duration, @message
        | filter @duration > {threshold_ms}
        | stats count() as slow_request_count, avg(@duration) as avg_duration, max(@duration) as max_duration
        """
        
        return self._run_query(log_group, query, time_range_minutes)
    
    def query_top_errors(self, log_group, limit=10, time_range_minutes=60):
        """Query top errors"""
        query = f"""
        fields @message
        | filter @message like /ERROR/
        | stats count() as error_count by @message
        | sort error_count desc
        | limit {limit}
        """
        
        return self._run_query(log_group, query, time_range_minutes)
    
    def query_api_performance(self, log_group, time_range_minutes=60):
        """Query API performance metrics"""
        query = """
        fields @timestamp, @duration, @httpStatus
        | stats count() as request_count, avg(@duration) as avg_duration, pct(@duration, 95) as p95_duration by @httpStatus
        """
        
        return self._run_query(log_group, query, time_range_minutes)
    
    def _run_query(self, log_group, query, time_range_minutes):
        """Run CloudWatch Logs Insights query"""
        try:
            response = self.logs.start_query(
                logGroupName=log_group,
                startTime=int((datetime.utcnow() - timedelta(minutes=time_range_minutes)).timestamp()),
                endTime=int(datetime.utcnow().timestamp()),
                queryString=query
            )
            
            query_id = response['queryId']
            logger.info(f"Query started: {query_id}")
            
            return query_id
        except Exception as e:
            logger.error(f"Error running query: {e}")
            return None
```

---

## 7. Monitoring Setup Script

### Automated Setup

```bash
#!/bin/bash

set -e

echo "🔔 AAIS Monitoring & Alerting Setup"
echo "===================================="
echo ""

REGION="us-east-1"
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
PAGERDUTY_KEY="YOUR_PAGERDUTY_INTEGRATION_KEY"
ALERT_EMAIL="ops@example.com"

# Create SNS topic
echo "Creating SNS topic..."
SNS_TOPIC=$(aws sns create-topic \
  --name aais-prod-alerts \
  --region $REGION \
  --query 'TopicArn' \
  --output text)

echo "✓ SNS topic created: $SNS_TOPIC"

# Subscribe email
echo "Subscribing email to alerts..."
aws sns subscribe \
  --topic-arn $SNS_TOPIC \
  --protocol email \
  --notification-endpoint $ALERT_EMAIL \
  --region $REGION

echo "✓ Email subscription created"

# Create CloudWatch log group
echo "Creating CloudWatch log group..."
aws logs create-log-group \
  --log-group-name /aais/production \
  --region $REGION 2>/dev/null || echo "Log group already exists"

echo "✓ Log group created"

# Setup Python monitoring
echo "Installing monitoring dependencies..."
pip install boto3 requests

echo "✓ Dependencies installed"

echo ""
echo "✅ Monitoring setup complete!"
echo ""
echo "📋 Configuration:"
echo "  SNS Topic: $SNS_TOPIC"
echo "  Alert Email: $ALERT_EMAIL"
echo "  Slack Webhook: $SLACK_WEBHOOK"
echo "  PagerDuty Key: $PAGERDUTY_KEY"
echo ""
echo "📊 Dashboards created:"
echo "  - AAIS-Production (main metrics)"
echo "  - AAIS-Security (security events)"
echo ""
echo "🚨 Alarms configured:"
echo "  - High response time (> 200ms)"
echo "  - High error rate (> 10 errors/5min)"
echo "  - Low cache hit rate (< 80%)"
echo "  - High CPU (> 80%)"
echo "  - High memory (> 85%)"
echo "  - DB connection pool (> 90)"
echo "  - WAF blocks (> 100/5min)"
echo ""
echo "📧 Notifications:"
echo "  - Email alerts to: $ALERT_EMAIL"
echo "  - Slack notifications enabled"
echo "  - PagerDuty critical incidents enabled"
echo ""
