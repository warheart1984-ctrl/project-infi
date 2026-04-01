# AWS Deployment Guide

## Architecture Overview

```
Route 53 (DNS)
    ↓
CloudFront (CDN)
    ↓
ALB (Load Balancer)
    ↓
ECS Cluster
├── Backend Service (Fargate)
├── Frontend Service (Fargate)
└── RDS (PostgreSQL)
└── ElastiCache (Redis)
```

## Prerequisites

- AWS Account
- AWS CLI configured
- Docker images pushed to ECR
- Domain name (optional)

## Step 1: Create ECR Repositories

```bash
# Create ECR repositories
aws ecr create-repository --repository-name aais-backend --region us-east-1
aws ecr create-repository --repository-name aais-frontend --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push images
docker tag aais-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/aais-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/aais-backend:latest

docker tag aais-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/aais-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/aais-frontend:latest
```

## Step 2: Create RDS Database

```bash
aws rds create-db-instance \
  --db-instance-identifier aais-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username aais \
  --master-user-password <strong-password> \
  --allocated-storage 20 \
  --publicly-accessible false \
  --region us-east-1
```

## Step 3: Create ElastiCache Redis

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id aais-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --region us-east-1
```

## Step 4: Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name aais-cluster --region us-east-1

# Create task execution role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

## Step 5: Create Task Definitions

### Backend Task Definition

```bash
aws ecs register-task-definition \
  --family aais-backend \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 256 \
  --memory 512 \
  --execution-role-arn arn:aws:iam::<account-id>:role/ecsTaskExecutionRole \
  --container-definitions file://backend-task-def.json
```

### Frontend Task Definition

```bash
aws ecs register-task-definition \
  --family aais-frontend \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 256 \
  --memory 512 \
  --execution-role-arn arn:aws:iam::<account-id>:role/ecsTaskExecutionRole \
  --container-definitions file://frontend-task-def.json
```

## Step 6: Create Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name aais-alb \
  --subnets subnet-12345678 subnet-87654321 \
  --security-groups sg-12345678 \
  --scheme internet-facing \
  --type application

# Create target groups
aws elbv2 create-target-group \
  --name aais-backend \
  --protocol HTTP \
  --port 5000 \
  --vpc-id vpc-12345678

aws elbv2 create-target-group \
  --name aais-frontend \
  --protocol HTTP \
  --port 3000 \
  --vpc-id vpc-12345678
```

## Step 7: Create ECS Services

```bash
# Backend service
aws ecs create-service \
  --cluster aais-cluster \
  --service-name aais-backend \
  --task-definition aais-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345678,subnet-87654321],securityGroups=[sg-12345678],assignPublicIp=DISABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/aais-backend/1234567890abcdef,containerName=backend,containerPort=5000

# Frontend service
aws ecs create-service \
  --cluster aais-cluster \
  --service-name aais-frontend \
  --task-definition aais-frontend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345678,subnet-87654321],securityGroups=[sg-12345678],assignPublicIp=DISABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/aais-frontend/1234567890abcdef,containerName=frontend,containerPort=3000
```

## Step 8: Setup Auto Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/aais-cluster/aais-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name aais-backend-scaling \
  --service-namespace ecs \
  --resource-id service/aais-cluster/aais-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

## Step 9: Setup CloudFront CDN

```bash
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

## Step 10: Setup Route 53 DNS

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://route53-changes.json
```

## Monitoring & Logging

### CloudWatch Logs

```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/aais-backend
aws logs create-log-group --log-group-name /ecs/aais-frontend

# View logs
aws logs tail /ecs/aais-backend --follow
```

### CloudWatch Alarms

```bash
# CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name aais-backend-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

## Cost Optimization

1. **Use Fargate Spot** for non-critical workloads (70% savings)
2. **Reserved Instances** for predictable workloads
3. **S3 for static assets** instead of serving from containers
4. **CloudFront caching** to reduce origin requests
5. **RDS Multi-AZ** only for production

## Backup & Disaster Recovery

```bash
# Enable RDS automated backups
aws rds modify-db-instance \
  --db-instance-identifier aais-db \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"

# Create snapshot
aws rds create-db-snapshot \
  --db-instance-identifier aais-db \
  --db-snapshot-identifier aais-db-snapshot-$(date +%Y%m%d)
```

## Cleanup

```bash
# Delete ECS services
aws ecs delete-service --cluster aais-cluster --service aais-backend --force
aws ecs delete-service --cluster aais-cluster --service aais-frontend --force

# Delete cluster
aws ecs delete-cluster --cluster aais-cluster

# Delete RDS
aws rds delete-db-instance --db-instance-identifier aais-db --skip-final-snapshot

# Delete ElastiCache
aws elasticache delete-cache-cluster --cache-cluster-id aais-redis
```

## Estimated Monthly Cost

- ECS Fargate: $50-100
- RDS db.t3.micro: $30-50
- ElastiCache: $20-30
- ALB: $20-30
- Data transfer: $10-20
- **Total: ~$130-230/month**

## Support

For AWS support:
- AWS Console: https://console.aws.amazon.com
- AWS Documentation: https://docs.aws.amazon.com
- AWS Support: https://console.aws.amazon.com/support
