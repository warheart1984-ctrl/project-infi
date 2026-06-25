# AWS Monitoring, Logging & Alerts Setup

## Overview

This guide covers:
- CloudWatch Logs configuration
- CloudWatch Metrics monitoring
- CloudWatch Alarms setup
- Performance monitoring
- Error tracking
- Custom dashboards

---

## 1. Setup CloudWatch Logs

### Create Log Groups

```bash
REGION=us-east-1

# Create log groups
aws logs create-log-group --log-group-name /ecs/aais-backend --region $REGION
aws logs create-log-group --log-group-name /ecs/aais-frontend --region $REGION
aws logs create-log-group --log-group-name /rds/aais-db --region $REGION
aws logs create-log-group --log-group-name /elasticache/aais-redis --region $REGION

# Set retention policies (30 days)
aws logs put-retention-policy \
  --log-group-name /ecs/aais-backend \
  --retention-in-days 30 \
  --region $REGION

aws logs put-retention-policy \
  --log-group-name /ecs/aais-frontend \
  --retention-in-days 30 \
  --region $REGION

echo "✓ Log groups created"
```

### Enable RDS Logging

```bash
# Enable PostgreSQL logs
aws rds modify-db-instance \
  --db-instance-identifier aais-db \
  --enable-cloudwatch-logs-exports postgresql \
  --apply-immediately \
  --region $REGION

echo "✓ RDS logging enabled"
```

### View Logs

```bash
# Real-time logs
aws logs tail /ecs/aais-backend --follow --region $REGION

# Last 100 lines
aws logs tail /ecs/aais-backend -n 100 --region $REGION

# Filter logs
aws logs filter-log-events \
  --log-group-name /ecs/aais-backend \
  --filter-pattern "ERROR" \
  --region $REGION
```

---

## 2. Setup CloudWatch Metrics

### Enable Container Insights

```bash
# Install CloudWatch Container Insights agent
aws ecs update-cluster-settings \
  --cluster aais-cluster \
  --settings name=containerInsights,value=enabled \
  --region $REGION

echo "✓ Container Insights enabled"
```

### Custom Metrics

```bash
# Put custom metric (example: API response time)
aws cloudwatch put-metric-data \
  --namespace AAIS \
  --metric-name APIResponseTime \
  --value 250 \
  --unit Milliseconds \
  --region $REGION

# Put custom metric (example: cache hit rate)
aws cloudwatch put-metric-data \
  --namespace AAIS \
  --metric-name CacheHitRate \
  --value 85.5 \
  --unit Percent \
  --region $REGION

echo "✓ Custom metrics sent"
```

### View Metrics

```bash
# List available metrics
aws cloudwatch list-metrics \
  --namespace AWS/ECS \
  --region $REGION

# Get metric statistics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=aais-backend Name=ClusterName,Value=aais-cluster \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region $REGION
```

---

## 3. Setup CloudWatch Alarms

### CPU Utilization Alarm

```bash
# Backend CPU alarm
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
```

### Memory Utilization Alarm

```bash
# Backend memory alarm
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
```

### Error Rate Alarm

```bash
# Create SNS topic for alerts
SNS_TOPIC=$(aws sns create-topic \
  --name aais-alerts \
  --region $REGION \
  --query 'TopicArn' \
  --output text)

echo "SNS Topic: $SNS_TOPIC"

# Subscribe to alerts
aws sns subscribe \
  --topic-arn $SNS_TOPIC \
  --protocol email \
  --notification-endpoint your-email@example.com \
  --region $REGION

echo "✓ SNS topic created and subscribed"
```

### RDS Alarm

```bash
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

# RDS storage alarm
aws cloudwatch put-metric-alarm \
  --alarm-name aais-db-storage-low \
  --alarm-description "Alert when database storage is low" \
  --metric-name FreeStorageSpace \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 2147483648 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=DBInstanceIdentifier,Value=aais-db \
  --alarm-actions arn:aws:sns:$REGION:$ACCOUNT_ID:aais-alerts \
  --region $REGION

echo "✓ RDS alarms created"
```

### ALB Alarm

```bash
# ALB target health alarm
aws cloudwatch put-metric-alarm \
  --alarm-name aais-alb-unhealthy-targets \
  --alarm-description "Alert when ALB has unhealthy targets" \
  --metric-name UnHealthyHostCount \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:$REGION:$ACCOUNT_ID:aais-alerts \
  --region $REGION

echo "✓ ALB alarm created"
```

---

## 4. Create CloudWatch Dashboard

```bash
# Create dashboard
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
            [".", "DatabaseConnections", {"stat": "Average"}],
            [".", "FreeStorageSpace", {"stat": "Average"}]
          ],
          "period": 300,
          "stat": "Average",
          "region": "'$REGION'",
          "title": "RDS Metrics"
        }
      },
      {
        "type": "log",
        "properties": {
          "query": "fields @timestamp, @message | filter @message like /ERROR/ | stats count() by bin(5m)",
          "region": "'$REGION'",
          "title": "Error Count"
        }
      }
    ]
  }' \
  --region $REGION

echo "✓ Dashboard created"
```

---

## 5. Setup Log Insights Queries

### Error Analysis

```bash
# Find errors in the last hour
aws logs start-query \
  --log-group-name /ecs/aais-backend \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | stats count() as error_count' \
  --region $REGION
```

### Performance Analysis

```bash
# Find slow requests
aws logs start-query \
  --log-group-name /ecs/aais-backend \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @duration | filter @duration > 1000 | stats avg(@duration), max(@duration), pct(@duration, 95)' \
  --region $REGION
```

### Database Queries

```bash
# Find slow database queries
aws logs start-query \
  --log-group-name /rds/aais-db \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @duration | filter @duration > 1000 | stats count() as slow_queries' \
  --region $REGION
```

---

## 6. Performance Monitoring

### Monitor API Response Times

```bash
# Get average response time
aws cloudwatch get-metric-statistics \
  --namespace AAIS \
  --metric-name APIResponseTime \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum,Minimum \
  --region $REGION
```

### Monitor Cache Hit Rate

```bash
# Get cache hit rate
aws cloudwatch get-metric-statistics \
  --namespace AAIS \
  --metric-name CacheHitRate \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --region $REGION
```

### Monitor Database Connections

```bash
# Get database connection count
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=aais-db \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region $REGION
```

---

## 7. Health Checks

### Application Health Check

```bash
# Check backend health
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[0].DNSName' \
  --output text \
  --region $REGION)

curl -s http://$ALB_DNS/health | jq .
```

### Database Health Check

```bash
# Check database connectivity
DB_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier aais-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text \
  --region $REGION)

echo "Database endpoint: $DB_ENDPOINT"
```

### Service Health Check

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster aais-cluster \
  --services aais-backend aais-frontend \
  --query 'services[*].[serviceName,status,runningCount,desiredCount]' \
  --output table \
  --region $REGION
```

---

## 8. Monitoring Checklist

- [ ] CloudWatch Logs configured
- [ ] Log retention policies set
- [ ] Container Insights enabled
- [ ] Custom metrics created
- [ ] Alarms configured
- [ ] SNS topic created
- [ ] Email notifications subscribed
- [ ] Dashboard created
- [ ] Log Insights queries saved
- [ ] Health checks passing
- [ ] Performance baseline established
- [ ] Alert thresholds tuned

---

## 9. Monitoring Best Practices

### Key Metrics to Monitor

1. **Application Metrics**
   - API response time (target: < 500ms)
   - Error rate (target: < 0.1%)
   - Request throughput
   - Cache hit rate (target: > 80%)

2. **Infrastructure Metrics**
   - CPU utilization (target: < 70%)
   - Memory utilization (target: < 80%)
   - Disk usage (target: < 80%)
   - Network throughput

3. **Database Metrics**
   - Connection count
   - Query latency
   - Slow query count
   - Storage usage

4. **Availability Metrics**
   - Uptime percentage (target: > 99.9%)
   - Healthy host count
   - Task count
   - Service status

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU | 70% | 85% |
| Memory | 75% | 90% |
| Error Rate | 0.5% | 1% |
| Response Time | 1000ms | 2000ms |
| Disk Usage | 75% | 90% |
| DB Connections | 80 | 100 |

---

## 10. Troubleshooting

### High CPU Usage

```bash
# Check which service is using CPU
aws ecs describe-services \
  --cluster aais-cluster \
  --services aais-backend aais-frontend \
  --region $REGION

# Check logs for errors
aws logs tail /ecs/aais-backend --follow --region $REGION
```

### High Memory Usage

```bash
# Check memory metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=aais-backend Name=ClusterName,Value=aais-cluster \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum \
  --region $REGION
```

### Database Connection Issues

```bash
# Check database status
aws rds describe-db-instances \
  --db-instance-identifier aais-db \
  --query 'DBInstances[0].[DBInstanceStatus,DBInstanceIdentifier,Endpoint.Address]' \
  --output table \
  --region $REGION
```

---

## 11. Cost Optimization

- CloudWatch Logs: $0.50 per GB ingested
- CloudWatch Metrics: $0.10 per custom metric
- CloudWatch Alarms: $0.10 per alarm
- CloudWatch Dashboard: Free (up to 3)
- CloudWatch Logs Insights: $0.005 per GB scanned

**Estimated monthly cost: $20-50**

---

## Support

- CloudWatch Documentation: https://docs.aws.amazon.com/cloudwatch/
- CloudWatch Logs Insights: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html
- AWS Support: https://console.aws.amazon.com/support
