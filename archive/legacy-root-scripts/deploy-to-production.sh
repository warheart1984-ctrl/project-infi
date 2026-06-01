#!/bin/bash

# Production deployment script

set -e

echo "🚀 AAIS Production Deployment"
echo "============================="
echo ""

# Configuration
REGION="us-east-1"
CLUSTER="aais-prod"
DOMAIN="aais.example.com"
ENVIRONMENT="production"

echo "Configuration:"
echo "  Region: $REGION"
echo "  Cluster: $CLUSTER"
echo "  Domain: $DOMAIN"
echo "  Environment: $ENVIRONMENT"
echo ""

# Step 1: Security checks
echo "Step 1: Running security checks..."
bash scripts/pre-deployment-security-check.sh
echo ""

# Step 2: Infrastructure setup
echo "Step 2: Setting up infrastructure..."
bash scripts/setup-infrastructure.sh
echo ""

# Step 3: Database migration
echo "Step 3: Running database migrations..."
bash scripts/database-migration.sh
echo ""

# Step 4: Application deployment
echo "Step 4: Deploying application..."
bash scripts/deploy-application.sh
echo ""

# Step 5: DNS configuration
echo "Step 5: Configuring DNS..."
bash scripts/configure-dns.sh
echo ""

# Step 6: SSL/TLS setup
echo "Step 6: Setting up SSL/TLS..."
bash scripts/setup-ssl.sh
echo ""

# Step 7: Monitoring activation
echo "Step 7: Activating monitoring..."
bash scripts/activate-monitoring.sh
echo ""

# Step 8: Health checks
echo "Step 8: Running health checks..."
bash scripts/health-checks.sh
echo ""

echo "🎉 Production deployment complete!"
echo ""
echo "Your AAIS system is now live at: https://$DOMAIN"
echo ""
echo "Next steps:"
echo "1. Verify all health checks"
echo "2. Monitor logs and metrics"
echo "3. Test all features"
echo "4. Notify team members"
echo "5. Update documentation"
echo ""
