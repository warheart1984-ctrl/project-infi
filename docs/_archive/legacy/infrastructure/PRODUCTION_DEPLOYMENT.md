# AAIS Production Deployment Guide

## Overview

This guide covers deploying AAIS to production:
- Pre-deployment checklist
- Infrastructure setup
- Database migration
- Application deployment
- DNS configuration
- SSL/TLS setup
- Monitoring activation
- Health checks
- Rollback procedures

---

## 1. Pre-Deployment Checklist

### Security Review

```bash
#!/bin/bash

echo "🔒 Security Pre-Deployment Checklist"
echo "===================================="
echo ""

# Check environment variables
echo "✓ Checking environment variables..."
required_vars=(
  "DATABASE_URL"
  "REDIS_URL"
  "SECRET_KEY"
  "AWS_ACCESS_KEY_ID"
  "AWS_SECRET_ACCESS_KEY"
  "DOMAIN_NAME"
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Missing: $var"
    exit 1
  fi
done

echo "✓ All environment variables set"
echo ""

# Check SSL certificates
echo "✓ Checking SSL certificates..."
if [ ! -f "/etc/ssl/certs/aais.crt" ]; then
  echo "❌ SSL certificate not found"
  exit 1
fi

echo "✓ SSL certificate found"
echo ""

# Check database connectivity
echo "✓ Checking database connectivity..."
psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "❌ Database connection failed"
  exit 1
fi

echo "✓ Database connection successful"
echo ""

# Check Redis connectivity
echo "✓ Checking Redis connectivity..."
redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "❌ Redis connection failed"
  exit 1
fi

echo "✓ Redis connection successful"
echo ""

echo "✅ All security checks passed!"
```

---

## 2. Infrastructure Setup

### AWS Infrastructure Deployment

```bash
#!/bin/bash

set -e

echo "🏗️ AWS Infrastructure Deployment"
echo "================================="
echo ""

REGION="us-east-1"
CLUSTER_NAME="aais-prod"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create VPC
echo "Creating VPC..."
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --region $REGION \
  --query 'Vpc.VpcId' \
  --output text)

echo "✓ VPC created: $VPC_ID"

# Create subnets
echo "Creating subnets..."
SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone ${REGION}a \
  --region $REGION \
  --query 'Subnet.SubnetId' \
  --output text)

SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone ${REGION}b \
  --region $REGION \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✓ Subnets created: $SUBNET_1, $SUBNET_2"

# Create ECS cluster
echo "Creating ECS cluster..."
aws ecs create-cluster \
  --cluster-name $CLUSTER_NAME \
  --region $REGION

echo "✓ ECS cluster created: $CLUSTER_NAME"

# Create RDS instance
echo "Creating RDS instance..."
aws rds create-db-instance \
  --db-instance-identifier aais-prod-db \
  --db-instance-class db.t3.small \
  --engine postgres \
  --master-username aais \
  --master-user-password "$(openssl rand -base64 32)" \
  --allocated-storage 100 \
  --storage-encrypted \
  --multi-az \
  --backup-retention-period 30 \
  --region $REGION

echo "✓ RDS instance created"

# Create ElastiCache cluster
echo "Creating ElastiCache cluster..."
aws elasticache create-cache-cluster \
  --cache-cluster-id aais-prod-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --region $REGION

echo "✓ ElastiCache cluster created"

echo ""
echo "✅ Infrastructure deployment complete!"
```

---

## 3. Database Migration

### Database Setup and Migration

```bash
#!/bin/bash

set -e

echo "🗄️ Database Migration"
echo "===================="
echo ""

DB_HOST="aais-prod-db.c9akciq32.us-east-1.rds.amazonaws.com"
DB_NAME="aais_prod"
DB_USER="aais"

# Wait for RDS to be ready
echo "Waiting for RDS to be ready..."
for i in {1..30}; do
  if pg_isready -h $DB_HOST -U $DB_USER > /dev/null 2>&1; then
    echo "✓ RDS is ready"
    break
  fi
  echo "Waiting... ($i/30)"
  sleep 10
done

# Create database
echo "Creating database..."
psql -h $DB_HOST -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
echo "✓ Database created"

# Run migrations
echo "Running database migrations..."
cd /app
alembic upgrade head
echo "✓ Migrations completed"

# Create indexes
echo "Creating indexes..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME << EOF
CREATE INDEX idx_user_id ON generated_content(user_id);
CREATE INDEX idx_created_at ON generated_content(created_at);
CREATE INDEX idx_content_type ON generated_content(content_type);
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_cache_key ON cache_entries(key);
EOF

echo "✓ Indexes created"

echo ""
echo "✅ Database migration complete!"
```

---

## 4. Application Deployment

### ECS Task Definition and Service

```bash
#!/bin/bash

set -e

echo "🚀 Application Deployment"
echo "========================="
echo ""

REGION="us-east-1"
CLUSTER="aais-prod"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/aais-backend:latest"

# Register task definition
echo "Registering task definition..."
aws ecs register-task-definition \
  --family aais-backend \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 512 \
  --memory 1024 \
  --execution-role-arn arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole \
  --container-definitions "[
    {
      \"name\": \"backend\",
      \"image\": \"$IMAGE\",
      \"portMappings\": [{\"containerPort\": 5000}],
      \"environment\": [
        {\"name\": \"ENVIRONMENT\", \"value\": \"production\"},
        {\"name\": \"LOG_LEVEL\", \"value\": \"INFO\"}
      ],
      \"secrets\": [
        {\"name\": \"DATABASE_URL\", \"valueFrom\": \"arn:aws:secretsmanager:$REGION:$ACCOUNT_ID:secret:aais/db/url\"},
        {\"name\": \"REDIS_URL\", \"valueFrom\": \"arn:aws:secretsmanager:$REGION:$ACCOUNT_ID:secret:aais/redis/url\"}
      ],
      \"logConfiguration\": {
        \"logDriver\": \"awslogs\",
        \"options\": {
          \"awslogs-group\": \"/ecs/aais-backend\",
          \"awslogs-region\": \"$REGION\",
          \"awslogs-stream-prefix\": \"ecs\"
        }
      }
    }
  ]" \
  --region $REGION

echo "✓ Task definition registered"

# Create service
echo "Creating ECS service..."
aws ecs create-service \
  --cluster $CLUSTER \
  --service-name aais-backend \
  --task-definition aais-backend \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:$REGION:$ACCOUNT_ID:targetgroup/aais-backend/xxx,containerName=backend,containerPort=5000" \
  --region $REGION

echo "✓ ECS service created"

# Wait for service to stabilize
echo "Waiting for service to stabilize..."
aws ecs wait services-stable \
  --cluster $CLUSTER \
  --services aais-backend \
  --region $REGION

echo "✓ Service is stable"

echo ""
echo "✅ Application deployment complete!"
```

---

## 5. DNS Configuration

### Route 53 Setup

```bash
#!/bin/bash

set -e

echo "🌐 DNS Configuration"
echo "===================="
echo ""

DOMAIN="aais.example.com"
ZONE_ID="Z1234567890ABC"
ALB_DNS="aais-alb-123456.us-east-1.elb.amazonaws.com"

# Create Route 53 record
echo "Creating Route 53 record..."
aws route53 change-resource-record-sets \
  --hosted-zone-id $ZONE_ID \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"CREATE\",
      \"ResourceRecordSet\": {
        \"Name\": \"$DOMAIN\",
        \"Type\": \"A\",
        \"AliasTarget\": {
          \"HostedZoneId\": \"Z35SXDOTRQ7X7K\",
          \"DNSName\": \"$ALB_DNS\",
          \"EvaluateTargetHealth\": true
        }
      }
    }]
  }"

echo "✓ Route 53 record created"

# Create www subdomain
echo "Creating www subdomain..."
aws route53 change-resource-record-sets \
  --hosted-zone-id $ZONE_ID \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"CREATE\",
      \"ResourceRecordSet\": {
        \"Name\": \"www.$DOMAIN\",
        \"Type\": \"CNAME\",
        \"TTL\": 300,
        \"ResourceRecords\": [{\"Value\": \"$DOMAIN\"}]
      }
    }]
  }"

echo "✓ www subdomain created"

echo ""
echo "✅ DNS configuration complete!"
echo "Domain: $DOMAIN"
```

---

## 6. SSL/TLS Setup

### ACM Certificate and ALB Configuration

```bash
#!/bin/bash

set -e

echo "🔐 SSL/TLS Setup"
echo "================"
echo ""

DOMAIN="aais.example.com"
REGION="us-east-1"
ALB_ARN="arn:aws:elasticloadbalancing:$REGION:$ACCOUNT_ID:loadbalancer/app/aais-alb/xxx"

# Request ACM certificate
echo "Requesting ACM certificate..."
CERT_ARN=$(aws acm request-certificate \
  --domain-name $DOMAIN \
  --subject-alternative-names www.$DOMAIN \
  --validation-method DNS \
  --region $REGION \
  --query 'CertificateArn' \
  --output text)

echo "✓ Certificate requested: $CERT_ARN"

# Wait for certificate validation
echo "Waiting for certificate validation..."
for i in {1..60}; do
  STATUS=$(aws acm describe-certificate \
    --certificate-arn $CERT_ARN \
    --region $REGION \
    --query 'Certificate.Status' \
    --output text)
  
  if [ "$STATUS" = "ISSUED" ]; then
    echo "✓ Certificate issued"
    break
  fi
  
  echo "Status: $STATUS... waiting ($i/60)"
  sleep 10
done

# Create HTTPS listener
echo "Creating HTTPS listener..."
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:$REGION:$ACCOUNT_ID:targetgroup/aais-backend/xxx \
  --ssl-policy ELBSecurityPolicy-TLS-1-2-2017-01 \
  --region $REGION

echo "✓ HTTPS listener created"

# Redirect HTTP to HTTPS
echo "Configuring HTTP to HTTPS redirect..."
HTTP_LISTENER=$(aws elbv2 describe-listeners \
  --load-balancer-arn $ALB_ARN \
  --region $REGION \
  --query 'Listeners[?Port==`80`].ListenerArn' \
  --output text)

aws elbv2 modify-listener \
  --listener-arn $HTTP_LISTENER \
  --default-actions Type=redirect,RedirectConfig='{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}' \
  --region $REGION

echo "✓ HTTP to HTTPS redirect configured"

echo ""
echo "✅ SSL/TLS setup complete!"
```

---

## 7. Monitoring Activation

### Enable Monitoring and Alerts

```bash
#!/bin/bash

set -e

echo "📊 Monitoring Activation"
echo "======================="
echo ""

REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Enable CloudWatch Container Insights
echo "Enabling Container Insights..."
aws ecs update-cluster-settings \
  --cluster aais-prod \
  --settings name=containerInsights,value=enabled \
  --region $REGION

echo "✓ Container Insights enabled"

# Create SNS topic for alerts
echo "Creating SNS topic..."
SNS_TOPIC=$(aws sns create-topic \
  --name aais-prod-alerts \
  --region $REGION \
  --query 'TopicArn' \
  --output text)

echo "✓ SNS topic created: $SNS_TOPIC"

# Subscribe to alerts
echo "Subscribing to alerts..."
aws sns subscribe \
  --topic-arn $SNS_TOPIC \
  --protocol email \
  --notification-endpoint ops@example.com \
  --region $REGION

echo "✓ Email subscription created"

# Create CloudWatch alarms
echo "Creating CloudWatch alarms..."
aws cloudwatch put-metric-alarm \
  --alarm-name aais-prod-cpu-high \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions $SNS_TOPIC \
  --region $REGION

echo "✓ CPU alarm created"

aws cloudwatch put-metric-alarm \
  --alarm-name aais-prod-error-rate-high \
  --alarm-description "Alert when error rate exceeds 1%" \
  --metric-name ErrorRate \
  --namespace AAIS \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions $SNS_TOPIC \
  --region $REGION

echo "✓ Error rate alarm created"

echo ""
echo "✅ Monitoring activation complete!"
```

---

## 8. Health Checks

### Verify Production Deployment

```bash
#!/bin/bash

set -e

echo "✅ Production Health Checks"
echo "==========================="
echo ""

DOMAIN="aais.example.com"

# Check API health
echo "Checking API health..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ API is healthy (HTTP $HTTP_CODE)"
else
  echo "❌ API health check failed (HTTP $HTTP_CODE)"
  exit 1
fi

# Check database connectivity
echo "Checking database connectivity..."
DB_RESPONSE=$(curl -s https://$DOMAIN/api/health | jq '.database')

if [ "$DB_RESPONSE" = "true" ]; then
  echo "✓ Database is connected"
else
  echo "❌ Database connection failed"
  exit 1
fi

# Check cache connectivity
echo "Checking cache connectivity..."
CACHE_RESPONSE=$(curl -s https://$DOMAIN/api/health | jq '.cache')

if [ "$CACHE_RESPONSE" = "true" ]; then
  echo "✓ Cache is connected"
else
  echo "❌ Cache connection failed"
  exit 1
fi

# Check response time
echo "Checking response time..."
RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null https://$DOMAIN/api/health)
RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc)

echo "✓ Response time: ${RESPONSE_MS}ms"

if (( $(echo "$RESPONSE_MS < 200" | bc -l) )); then
  echo "✓ Response time is within target (< 200ms)"
else
  echo "⚠️ Response time exceeds target (> 200ms)"
fi

echo ""
echo "✅ All health checks passed!"
echo "Production deployment is live at: https://$DOMAIN"
```

---

## 9. Rollback Procedures

### Emergency Rollback

```bash
#!/bin/bash

set -e

echo "🔄 Rollback Procedure"
echo "===================="
echo ""

REGION="us-east-1"
CLUSTER="aais-prod"
SERVICE="aais-backend"
PREVIOUS_TASK_DEF="aais-backend:2"  # Previous task definition

echo "⚠️ Starting rollback..."
echo ""

# Get current task definition
echo "Getting current task definition..."
CURRENT_TASK=$(aws ecs describe-services \
  --cluster $CLUSTER \
  --services $SERVICE \
  --region $REGION \
  --query 'services[0].taskDefinition' \
  --output text)

echo "Current task definition: $CURRENT_TASK"

# Update service to use previous task definition
echo "Rolling back to previous version..."
aws ecs update-service \
  --cluster $CLUSTER \
  --service $SERVICE \
  --task-definition $PREVIOUS_TASK_DEF \
  --region $REGION

echo "✓ Service updated to previous version"

# Wait for service to stabilize
echo "Waiting for service to stabilize..."
aws ecs wait services-stable \
  --cluster $CLUSTER \
  --services $SERVICE \
  --region $REGION

echo "✓ Service is stable"

# Verify health
echo "Verifying health..."
DOMAIN="aais.example.com"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Service is healthy"
else
  echo "❌ Service health check failed"
  exit 1
fi

echo ""
echo "✅ Rollback complete!"
echo "Service rolled back to: $PREVIOUS_TASK_DEF"
```

---

## 10. Production Deployment Checklist

- [ ] Security review completed
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database created and migrated
- [ ] Redis cluster created
- [ ] ECS cluster created
- [ ] Task definitions registered
- [ ] Services created
- [ ] Load balancer configured
- [ ] DNS records created
- [ ] HTTPS listener configured
- [ ] HTTP to HTTPS redirect enabled
- [ ] CloudWatch monitoring enabled
- [ ] Alarms configured
- [ ] Health checks passing
- [ ] Performance baseline established
- [ ] Backup strategy enabled
- [ ] Disaster recovery tested
- [ ] Team trained
- [ ] Documentation updated

---

## Support

- AWS ECS: https://docs.aws.amazon.com/ecs/
- AWS RDS: https://docs.aws.amazon.com/rds/
- AWS Route 53: https://docs.aws.amazon.com/route53/
- AWS ACM: https://docs.aws.amazon.com/acm/
