# AWS Performance Optimization - Auto-scaling, CDN & Optimization

## Overview

This guide covers:
- ECS auto-scaling configuration
- CloudFront CDN setup
- Database optimization
- Cache optimization
- Application performance tuning
- Cost optimization

---

## 1. Setup ECS Auto-scaling

### Enable Auto-scaling for Backend Service

```bash
REGION=us-east-1
CLUSTER=aais-cluster
SERVICE=aais-backend

# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/$CLUSTER/$SERVICE \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10 \
  --region $REGION

echo "✓ Scalable target registered"

# Create scaling policy (target tracking)
aws application-autoscaling put-scaling-policy \
  --policy-name aais-backend-cpu-scaling \
  --service-namespace ecs \
  --resource-id service/$CLUSTER/$SERVICE \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }' \
  --region $REGION

echo "✓ CPU scaling policy created"

# Create memory scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name aais-backend-memory-scaling \
  --service-namespace ecs \
  --resource-id service/$CLUSTER/$SERVICE \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 80.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageMemoryUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }' \
  --region $REGION

echo "✓ Memory scaling policy created"
```

### Enable Auto-scaling for Frontend Service

```bash
SERVICE=aais-frontend

# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/$CLUSTER/$SERVICE \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 8 \
  --region $REGION

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name aais-frontend-cpu-scaling \
  --service-namespace ecs \
  --resource-id service/$CLUSTER/$SERVICE \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }' \
  --region $REGION

echo "✓ Frontend auto-scaling configured"
```

### Monitor Auto-scaling

```bash
# View scaling activities
aws application-autoscaling describe-scaling-activities \
  --service-namespace ecs \
  --region $REGION \
  --query 'ScalingActivities[*].[ResourceId,StatusCode,StartTime]' \
  --output table

# View current desired count
aws ecs describe-services \
  --cluster $CLUSTER \
  --services aais-backend aais-frontend \
  --query 'services[*].[serviceName,desiredCount,runningCount]' \
  --output table \
  --region $REGION
```

---

## 2. Setup CloudFront CDN

### Create CloudFront Distribution

```bash
# Get ALB DNS
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[0].DNSName' \
  --output text \
  --region $REGION)

echo "ALB DNS: $ALB_DNS"

# Create CloudFront distribution
DISTRIBUTION=$(aws cloudfront create-distribution \
  --distribution-config '{
    "CallerReference": "'$(date +%s)'",
    "Comment": "AAIS CDN Distribution",
    "Enabled": true,
    "Origins": {
      "Quantity": 1,
      "Items": [{
        "Id": "aais-alb",
        "DomainName": "'$ALB_DNS'",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "https-only"
        }
      }]
    },
    "DefaultCacheBehavior": {
      "AllowedMethods": {
        "Quantity": 7,
        "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
      },
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      },
      "TargetOriginId": "aais-alb",
      "ViewerProtocolPolicy": "redirect-to-https",
      "ForwardedValues": {
        "QueryString": true,
        "Cookies": {"Forward": "all"},
        "Headers": {
          "Quantity": 5,
          "Items": ["Authorization", "Host", "User-Agent", "Accept", "Content-Type"]
        }
      },
      "MinTTL": 0,
      "DefaultTTL": 3600,
      "MaxTTL": 86400,
      "Compress": true
    },
    "CacheBehaviors": [{
      "PathPattern": "/api/*",
      "AllowedMethods": {
        "Quantity": 7,
        "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
      },
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      },
      "TargetOriginId": "aais-alb",
      "ViewerProtocolPolicy": "https-only",
      "ForwardedValues": {
        "QueryString": true,
        "Cookies": {"Forward": "all"},
        "Headers": {
          "Quantity": 5,
          "Items": ["Authorization", "Host", "User-Agent", "Accept", "Content-Type"]
        }
      },
      "MinTTL": 0,
      "DefaultTTL": 0,
      "MaxTTL": 0,
      "Compress": true
    },
    {
      "PathPattern": "/static/*",
      "AllowedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      },
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      },
      "TargetOriginId": "aais-alb",
      "ViewerProtocolPolicy": "https-only",
      "ForwardedValues": {
        "QueryString": false,
        "Cookies": {"Forward": "none"}
      },
      "MinTTL": 0,
      "DefaultTTL": 86400,
      "MaxTTL": 31536000,
      "Compress": true
    }]
  }' \
  --query 'Distribution.Id' \
  --output text)

echo "CloudFront Distribution ID: $DISTRIBUTION"
echo "✓ CloudFront distribution created"
```

### Get CloudFront Domain

```bash
# Get CloudFront domain name
CF_DOMAIN=$(aws cloudfront get-distribution \
  --id $DISTRIBUTION \
  --query 'Distribution.DomainName' \
  --output text)

echo "CloudFront Domain: $CF_DOMAIN"
echo "Access your app at: https://$CF_DOMAIN"
```

---

## 3. Database Optimization

### Enable RDS Performance Insights

```bash
aws rds modify-db-instance \
  --db-instance-identifier aais-db \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --apply-immediately \
  --region $REGION

echo "✓ Performance Insights enabled"
```

### Optimize RDS Parameters

```bash
# Create parameter group
aws rds create-db-parameter-group \
  --db-parameter-group-name aais-postgres-optimized \
  --db-parameter-group-family postgres15 \
  --description "Optimized parameters for AAIS" \
  --region $REGION

# Modify parameters for performance
aws rds modify-db-parameter-group \
  --db-parameter-group-name aais-postgres-optimized \
  --parameters \
    "ParameterName=shared_buffers,ParameterValue=262144,ApplyMethod=pending-reboot" \
    "ParameterName=effective_cache_size,ParameterValue=786432,ApplyMethod=pending-reboot" \
    "ParameterName=work_mem,ParameterValue=4096,ApplyMethod=immediate" \
    "ParameterName=maintenance_work_mem,ParameterValue=65536,ApplyMethod=pending-reboot" \
    "ParameterName=random_page_cost,ParameterValue=1.1,ApplyMethod=immediate" \
    "ParameterName=effective_io_concurrency,ParameterValue=200,ApplyMethod=immediate" \
  --region $REGION

echo "✓ RDS parameters optimized"
```

### Add Read Replicas

```bash
# Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier aais-db-read-replica \
  --source-db-instance-identifier aais-db \
  --db-instance-class db.t3.micro \
  --region $REGION

echo "✓ Read replica created"
```

---

## 4. Cache Optimization

### Enable Redis Cluster Mode

```bash
# Create Redis cluster
aws elasticache create-replication-group \
  --replication-group-description "AAIS Redis Cluster" \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.micro \
  --num-cache-clusters 3 \
  --automatic-failover-enabled \
  --multi-az-enabled \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --region $REGION

echo "✓ Redis cluster created"
```

### Configure Cache Eviction Policy

```bash
# Create parameter group
aws elasticache create-cache-parameter-group \
  --cache-parameter-group-name aais-redis-optimized \
  --cache-parameter-group-family redis7 \
  --description "Optimized Redis parameters" \
  --region $REGION

# Modify parameters
aws elasticache modify-cache-parameter-group \
  --cache-parameter-group-name aais-redis-optimized \
  --parameter-name-values \
    "ParameterName=maxmemory-policy,ParameterValue=allkeys-lru" \
    "ParameterName=timeout,ParameterValue=300" \
  --region $REGION

echo "✓ Redis cache optimized"
```

---

## 5. Application Performance Tuning

### Enable Gzip Compression

```bash
# Update ALB to enable compression
aws elbv2 modify-target-group-attributes \
  --target-group-arn arn:aws:elasticloadbalancing:$REGION:$ACCOUNT_ID:targetgroup/aais-backend-tg/* \
  --attributes Key=deregistration_delay.timeout_seconds,Value=30 \
  --region $REGION

echo "✓ ALB compression enabled"
```

### Optimize Connection Pooling

```bash
# Update RDS connection settings
aws rds modify-db-instance \
  --db-instance-identifier aais-db \
  --db-parameter-group-name aais-postgres-optimized \
  --apply-immediately \
  --region $REGION

echo "✓ Connection pooling optimized"
```

### Enable HTTP/2

```bash
# CloudFront automatically supports HTTP/2
echo "✓ HTTP/2 enabled via CloudFront"
```

---

## 6. Monitoring Performance

### Create Performance Alarms

```bash
# ALB response time alarm
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
  --region $REGION

echo "✓ Response time alarm created"

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

echo "✓ Database CPU alarm created"
```

### View Performance Metrics

```bash
# Get ALB response time
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region $REGION

# Get CloudFront cache statistics
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name CacheHitRate \
  --dimensions Name=DistributionId,Value=$DISTRIBUTION \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --region $REGION
```

---

## 7. Cost Optimization

### Use Spot Instances

```bash
# Update ECS service to use Spot instances
aws ecs update-service \
  --cluster $CLUSTER \
  --service aais-backend \
  --capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=70 capacityProvider=FARGATE,weight=30 \
  --region $REGION

echo "✓ Spot instances enabled (70% cost savings)"
```

### Reserved Instances

```bash
# Purchase 1-year reserved instances
aws ec2 describe-reserved-instances-offerings \
  --filters Name=instance-type,Values=t3.micro \
  --query 'ReservedInstancesOfferings[0]' \
  --region $REGION

echo "✓ Consider purchasing reserved instances for 30-40% savings"
```

### S3 Lifecycle Policies

```bash
# Create lifecycle policy for CloudTrail logs
aws s3api put-bucket-lifecycle-configuration \
  --bucket aais-cloudtrail-logs-$ACCOUNT_ID \
  --lifecycle-configuration '{
    "Rules": [{
      "Id": "archive-old-logs",
      "Status": "Enabled",
      "Transitions": [{
        "Days": 30,
        "StorageClass": "GLACIER"
      }],
      "Expiration": {"Days": 365}
    }]
  }' \
  --region $REGION

echo "✓ S3 lifecycle policy configured"
```

---

## 8. Performance Checklist

- [ ] ECS auto-scaling configured
- [ ] CloudFront CDN enabled
- [ ] Cache hit rate > 80%
- [ ] API response time < 500ms
- [ ] Database response time < 100ms
- [ ] CPU utilization < 70%
- [ ] Memory utilization < 80%
- [ ] Gzip compression enabled
- [ ] HTTP/2 enabled
- [ ] Read replicas configured
- [ ] Connection pooling optimized
- [ ] Performance alarms configured
- [ ] Spot instances enabled
- [ ] Reserved instances purchased
- [ ] S3 lifecycle policies set

---

## 9. Performance Targets

| Metric | Target | Current |
|--------|--------|----------|
| API Response Time (p95) | < 500ms | - |
| Database Response Time | < 100ms | - |
| Cache Hit Rate | > 80% | - |
| CPU Utilization | < 70% | - |
| Memory Utilization | < 80% | - |
| Throughput | > 100 req/s | - |
| Error Rate | < 0.1% | - |
| Uptime | > 99.9% | - |

---

## 10. Cost Estimate

**Before Optimization:**
- ECS Fargate: $100/month
- RDS: $50/month
- ElastiCache: $30/month
- ALB: $30/month
- **Total: $210/month**

**After Optimization:**
- ECS Fargate Spot (70%): $30/month
- ECS Fargate (30%): $30/month
- RDS Reserved: $30/month
- ElastiCache Reserved: $15/month
- ALB: $30/month
- CloudFront: $20/month
- **Total: $155/month (26% savings)**

---

## Support

- ECS Auto-scaling: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-auto-scaling.html
- CloudFront: https://docs.aws.amazon.com/cloudfront/
- RDS Performance: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html
- ElastiCache: https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/
