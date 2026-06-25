# AWS Security Hardening - SSL/TLS, WAF & Encryption

## Overview

This guide covers:
- SSL/TLS certificates with ACM
- HTTPS configuration
- AWS WAF setup
- Data encryption (at rest & in transit)
- Security best practices
- Compliance & auditing

---

## 1. Setup SSL/TLS with AWS Certificate Manager

### Request SSL Certificate

```bash
REGION=us-east-1
DOMAIN=aais.example.com

# Request certificate
CERT_ARN=$(aws acm request-certificate \
  --domain-name $DOMAIN \
  --subject-alternative-names www.$DOMAIN \
  --validation-method DNS \
  --region $REGION \
  --query 'CertificateArn' \
  --output text)

echo "Certificate ARN: $CERT_ARN"

# Wait for certificate to be issued
echo "Waiting for certificate validation..."
while true; do
  STATUS=$(aws acm describe-certificate \
    --certificate-arn $CERT_ARN \
    --query 'Certificate.Status' \
    --output text \
    --region $REGION)
  
  if [ "$STATUS" = "ISSUED" ]; then
    echo "✓ Certificate issued"
    break
  fi
  
  echo "Status: $STATUS... waiting..."
  sleep 30
done
```

### Validate Certificate with DNS

```bash
# Get validation records
aws acm describe-certificate \
  --certificate-arn $CERT_ARN \
  --query 'Certificate.DomainValidationOptions[*].[DomainName,ResourceRecord]' \
  --output table \
  --region $REGION

# Add CNAME records to your DNS provider
# (Route 53, GoDaddy, Namecheap, etc.)
```

---

## 2. Configure HTTPS on Load Balancer

### Create HTTPS Listener

```bash
# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text \
  --region $REGION)

echo "ALB ARN: $ALB_ARN"

# Get target group ARN
FRONTEND_TG=$(aws elbv2 describe-target-groups \
  --names aais-frontend-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text \
  --region $REGION)

echo "Frontend TG: $FRONTEND_TG"

# Create HTTPS listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --default-actions Type=forward,TargetGroupArn=$FRONTEND_TG \
  --ssl-policy ELBSecurityPolicy-TLS-1-2-2017-01 \
  --region $REGION

echo "✓ HTTPS listener created"
```

### Redirect HTTP to HTTPS

```bash
# Get HTTP listener ARN
HTTP_LISTENER=$(aws elbv2 describe-listeners \
  --load-balancer-arn $ALB_ARN \
  --query 'Listeners[?Port==`80`].ListenerArn' \
  --output text \
  --region $REGION)

echo "HTTP Listener: $HTTP_LISTENER"

# Modify HTTP listener to redirect to HTTPS
aws elbv2 modify-listener \
  --listener-arn $HTTP_LISTENER \
  --default-actions Type=redirect,RedirectConfig='{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}' \
  --region $REGION

echo "✓ HTTP to HTTPS redirect configured"
```

---

## 3. Setup AWS WAF (Web Application Firewall)

### Create WAF Web ACL

```bash
# Create IP set for allowed IPs (optional)
IP_SET=$(aws wafv2 create-ip-set \
  --name aais-allowed-ips \
  --scope REGIONAL \
  --ip-address-version IPV4 \
  --addresses [] \
  --region $REGION \
  --query 'Summary.ARN' \
  --output text)

echo "IP Set: $IP_SET"

# Create Web ACL
WEB_ACL=$(aws wafv2 create-web-acl \
  --name aais-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules '[
    {
      "Name": "RateLimitRule",
      "Priority": 1,
      "Statement": {
        "RateBasedStatement": {
          "Limit": 2000,
          "AggregateKeyType": "IP"
        }
      },
      "Action": {"Block": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimitRule"
      }
    },
    {
      "Name": "AWSManagedRulesCommonRuleSet",
      "Priority": 2,
      "OverrideAction": {"None": {}},
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesCommonRuleSet"
        }
      },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "AWSManagedRulesCommonRuleSet"
      }
    },
    {
      "Name": "AWSManagedRulesKnownBadInputsRuleSet",
      "Priority": 3,
      "OverrideAction": {"None": {}},
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesKnownBadInputsRuleSet"
        }
      },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "AWSManagedRulesKnownBadInputsRuleSet"
      }
    }
  ]' \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=aais-waf \
  --region $REGION \
  --query 'Summary.ARN' \
  --output text)

echo "Web ACL: $WEB_ACL"
echo "✓ WAF Web ACL created"
```

### Associate WAF with ALB

```bash
# Get Web ACL ARN
WEB_ACL_ARN=$(aws wafv2 list-web-acls \
  --scope REGIONAL \
  --query 'WebACLs[?Name==`aais-waf`].ARN' \
  --output text \
  --region $REGION)

echo "Web ACL ARN: $WEB_ACL_ARN"

# Associate WAF with ALB
aws wafv2 associate-web-acl \
  --web-acl-arn $WEB_ACL_ARN \
  --resource-arn $ALB_ARN \
  --region $REGION

echo "✓ WAF associated with ALB"
```

---

## 4. Enable Encryption at Rest

### RDS Encryption

```bash
# Enable RDS encryption (for new instances)
aws rds create-db-instance \
  --db-instance-identifier aais-db-encrypted \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username aais \
  --master-user-password YourStrongPassword123! \
  --allocated-storage 20 \
  --storage-encrypted \
  --kms-key-id arn:aws:kms:$REGION:$ACCOUNT_ID:key/12345678-1234-1234-1234-123456789012 \
  --region $REGION

echo "✓ RDS encryption enabled"

# For existing instance, create encrypted snapshot
aws rds create-db-snapshot \
  --db-instance-identifier aais-db \
  --db-snapshot-identifier aais-db-snapshot-encrypted \
  --region $REGION

echo "Snapshot created. Restore from snapshot to enable encryption."
```

### ElastiCache Encryption

```bash
# Create encrypted Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id aais-redis-encrypted \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --auth-token YourStrongAuthToken123! \
  --region $REGION

echo "✓ ElastiCache encryption enabled"
```

### EBS Encryption

```bash
# Enable default EBS encryption
aws ec2 enable-ebs-encryption-by-default --region $REGION

echo "✓ EBS encryption enabled by default"
```

---

## 5. Enable Encryption in Transit

### VPC Endpoints for Private Communication

```bash
# Create VPC endpoint for S3
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.$REGION.s3 \
  --route-table-ids $ROUTE_TABLE_ID \
  --region $REGION

echo "✓ S3 VPC endpoint created"

# Create VPC endpoint for DynamoDB
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.$REGION.dynamodb \
  --route-table-ids $ROUTE_TABLE_ID \
  --region $REGION

echo "✓ DynamoDB VPC endpoint created"
```

### Security Group Rules

```bash
# Restrict database access to ECS tasks only
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $ECS_SG_ID \
  --region $REGION

echo "✓ Database security group updated"

# Restrict Redis access to ECS tasks only
aws ec2 authorize-security-group-ingress \
  --group-id $REDIS_SG_ID \
  --protocol tcp \
  --port 6379 \
  --source-group $ECS_SG_ID \
  --region $REGION

echo "✓ Redis security group updated"
```

---

## 6. Secrets Management

### Store Secrets in AWS Secrets Manager

```bash
# Create secret for database password
aws secretsmanager create-secret \
  --name aais/db/password \
  --description "AAIS database password" \
  --secret-string YourStrongPassword123! \
  --region $REGION

echo "✓ Database password stored"

# Create secret for API keys
aws secretsmanager create-secret \
  --name aais/api/secret-key \
  --description "AAIS API secret key" \
  --secret-string $(openssl rand -hex 32) \
  --region $REGION

echo "✓ API secret key stored"

# Create secret for Redis auth token
aws secretsmanager create-secret \
  --name aais/redis/auth-token \
  --description "AAIS Redis auth token" \
  --secret-string YourStrongAuthToken123! \
  --region $REGION

echo "✓ Redis auth token stored"
```

### Update ECS Task Definition to Use Secrets

```bash
# Register task definition with secrets
aws ecs register-task-definition \
  --family aais-backend \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 256 \
  --memory 512 \
  --execution-role-arn arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole \
  --container-definitions '[{
    "name": "backend",
    "image": "'$ACCOUNT_ID'.dkr.ecr.'$REGION'.amazonaws.com/aais-backend:latest",
    "portMappings": [{"containerPort": 5000}],
    "secrets": [
      {"name": "DATABASE_PASSWORD", "valueFrom": "arn:aws:secretsmanager:'$REGION':'$ACCOUNT_ID':secret:aais/db/password"},
      {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:'$REGION':'$ACCOUNT_ID':secret:aais/api/secret-key"},
      {"name": "REDIS_AUTH_TOKEN", "valueFrom": "arn:aws:secretsmanager:'$REGION':'$ACCOUNT_ID':secret:aais/redis/auth-token"}
    ]
  }]' \
  --region $REGION

echo "✓ Task definition updated with secrets"
```

---

## 7. Enable Logging & Auditing

### CloudTrail for API Auditing

```bash
# Create S3 bucket for CloudTrail logs
aws s3 mb s3://aais-cloudtrail-logs-$ACCOUNT_ID --region $REGION

# Enable CloudTrail
aws cloudtrail create-trail \
  --name aais-trail \
  --s3-bucket-name aais-cloudtrail-logs-$ACCOUNT_ID \
  --is-multi-region-trail \
  --region $REGION

# Start logging
aws cloudtrail start-logging \
  --trail-name aais-trail \
  --region $REGION

echo "✓ CloudTrail enabled"
```

### VPC Flow Logs

```bash
# Create CloudWatch log group
aws logs create-log-group --log-group-name /aws/vpc/aais-flow-logs --region $REGION

# Create IAM role for VPC Flow Logs
aws iam create-role \
  --role-name vpc-flow-logs-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Enable VPC Flow Logs
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids $VPC_ID \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/aais-flow-logs \
  --deliver-logs-permission-iam-role-arn arn:aws:iam::$ACCOUNT_ID:role/vpc-flow-logs-role \
  --region $REGION

echo "✓ VPC Flow Logs enabled"
```

---

## 8. Security Best Practices

### IAM Security

```bash
# Create IAM policy for ECS task execution
aws iam create-policy \
  --policy-name aais-ecs-task-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ],
        "Resource": "*"
      },
      {
        "Effect": "Allow",
        "Action": [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "arn:aws:logs:*:*:*"
      }
    ]
  }'

echo "✓ IAM policy created"
```

### Security Group Hardening

```bash
# Remove overly permissive rules
aws ec2 revoke-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0 \
  --region $REGION || echo "SSH rule not found"

echo "✓ Security groups hardened"
```

---

## 9. Security Monitoring

### Create Security Alarms

```bash
# Alarm for unauthorized API calls
aws cloudwatch put-metric-alarm \
  --alarm-name aais-unauthorized-api-calls \
  --alarm-description "Alert on unauthorized API calls" \
  --metric-name UnauthorizedAPICallsEventCount \
  --namespace CloudTrailMetrics \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:$REGION:$ACCOUNT_ID:aais-alerts \
  --region $REGION

echo "✓ Security alarm created"
```

---

## 10. Security Checklist

- [ ] SSL/TLS certificate installed
- [ ] HTTPS enabled on ALB
- [ ] HTTP redirects to HTTPS
- [ ] WAF enabled and configured
- [ ] Rate limiting rules active
- [ ] SQL injection protection enabled
- [ ] XSS protection enabled
- [ ] RDS encryption enabled
- [ ] ElastiCache encryption enabled
- [ ] EBS encryption enabled
- [ ] Secrets stored in Secrets Manager
- [ ] CloudTrail enabled
- [ ] VPC Flow Logs enabled
- [ ] Security groups hardened
- [ ] IAM policies least privilege
- [ ] Security alarms configured
- [ ] Regular security audits scheduled
- [ ] Backup encryption enabled
- [ ] DDoS protection (Shield Standard)
- [ ] Security scanning enabled

---

## 11. Compliance & Standards

### OWASP Top 10 Protection

- ✅ Injection (WAF + parameterized queries)
- ✅ Broken Authentication (JWT + rate limiting)
- ✅ Sensitive Data Exposure (encryption + HTTPS)
- ✅ XML External Entities (WAF rules)
- ✅ Broken Access Control (IAM + security groups)
- ✅ Security Misconfiguration (hardened configs)
- ✅ XSS (WAF + input validation)
- ✅ Insecure Deserialization (WAF rules)
- ✅ Using Components with Known Vulnerabilities (scanning)
- ✅ Insufficient Logging & Monitoring (CloudTrail + CloudWatch)

### Compliance Standards

- **GDPR**: Data encryption, audit logs, data retention
- **HIPAA**: Encryption, access controls, audit trails
- **PCI DSS**: Network segmentation, encryption, monitoring
- **SOC 2**: Logging, monitoring, access controls

---

## 12. Cost Estimate

- ACM Certificate: Free
- WAF: $5/month + $0.60 per rule
- Secrets Manager: $0.40 per secret/month
- CloudTrail: $2/month + $0.10 per 100k events
- VPC Flow Logs: $0.50 per GB
- **Total: ~$20-50/month**

---

## Support

- AWS Security: https://aws.amazon.com/security/
- WAF Documentation: https://docs.aws.amazon.com/waf/
- ACM Documentation: https://docs.aws.amazon.com/acm/
- Secrets Manager: https://docs.aws.amazon.com/secretsmanager/
