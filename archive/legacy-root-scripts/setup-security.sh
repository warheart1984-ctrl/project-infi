#!/bin/bash

# AWS Security Setup Script

set -e

echo "🔐 AWS Security Hardening Setup"
echo "================================="
echo ""

# Get configuration
REGION=${1:-us-east-1}
DOMAIN=${2:-aais.example.com}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Region: $REGION"
echo "Domain: $DOMAIN"
echo "Account ID: $ACCOUNT_ID"
echo ""

# Step 1: Request SSL Certificate
echo "🔐 Requesting SSL certificate..."
CERT_ARN=$(aws acm request-certificate \
  --domain-name $DOMAIN \
  --subject-alternative-names www.$DOMAIN \
  --validation-method DNS \
  --region $REGION \
  --query 'CertificateArn' \
  --output text)

echo "Certificate ARN: $CERT_ARN"
echo "✓ Certificate requested"
echo ""

# Step 2: Create WAF Web ACL
echo "🚨 Creating WAF Web ACL..."
WEB_ACL=$(aws wafv2 create-web-acl \
  --name aais-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules '[
    {
      "Name": "RateLimitRule",
      "Priority": 1,
      "Statement": {"RateBasedStatement": {"Limit": 2000, "AggregateKeyType": "IP"}},
      "Action": {"Block": {}},
      "VisibilityConfig": {"SampledRequestsEnabled": true, "CloudWatchMetricsEnabled": true, "MetricName": "RateLimitRule"}
    },
    {
      "Name": "AWSManagedRulesCommonRuleSet",
      "Priority": 2,
      "OverrideAction": {"None": {}},
      "Statement": {"ManagedRuleGroupStatement": {"VendorName": "AWS", "Name": "AWSManagedRulesCommonRuleSet"}},
      "VisibilityConfig": {"SampledRequestsEnabled": true, "CloudWatchMetricsEnabled": true, "MetricName": "AWSManagedRulesCommonRuleSet"}
    }
  ]' \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=aais-waf \
  --region $REGION \
  --query 'Summary.ARN' \
  --output text)

echo "Web ACL: $WEB_ACL"
echo "✓ WAF Web ACL created"
echo ""

# Step 3: Create Secrets
echo "🔐 Creating secrets in Secrets Manager..."
aws secretsmanager create-secret \
  --name aais/db/password \
  --description "AAIS database password" \
  --secret-string YourStrongPassword123! \
  --region $REGION 2>/dev/null || echo "Database secret exists"

aws secretsmanager create-secret \
  --name aais/api/secret-key \
  --description "AAIS API secret key" \
  --secret-string $(openssl rand -hex 32) \
  --region $REGION 2>/dev/null || echo "API secret exists"

echo "✓ Secrets created"
echo ""

# Step 4: Enable CloudTrail
echo "📚 Enabling CloudTrail..."
aws s3 mb s3://aais-cloudtrail-logs-$ACCOUNT_ID --region $REGION 2>/dev/null || echo "S3 bucket exists"

aws cloudtrail create-trail \
  --name aais-trail \
  --s3-bucket-name aais-cloudtrail-logs-$ACCOUNT_ID \
  --is-multi-region-trail \
  --region $REGION 2>/dev/null || echo "Trail exists"

aws cloudtrail start-logging \
  --trail-name aais-trail \
  --region $REGION 2>/dev/null || echo "Logging already started"

echo "✓ CloudTrail enabled"
echo ""

# Step 5: Enable EBS Encryption
echo "🔐 Enabling EBS encryption..."
aws ec2 enable-ebs-encryption-by-default --region $REGION
echo "✓ EBS encryption enabled"
echo ""

echo "✅ Security setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Validate SSL certificate in ACM console"
echo "2. Add CNAME records to your DNS provider"
echo "3. Update ALB with HTTPS listener"
echo "4. Associate WAF with ALB"
echo "5. Update secrets with real values"
echo "6. Enable encryption on RDS and ElastiCache"
echo ""
echo "Certificate ARN: $CERT_ARN"
echo "Web ACL ARN: $WEB_ACL"
echo ""
