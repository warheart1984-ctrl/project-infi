# Heroku Deployment Guide

## Quick Start

### Prerequisites

- Heroku Account (free tier available)
- Heroku CLI installed
- Git repository

### Installation

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login

# Create Heroku app
heroku create aais-app

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis addon
heroku addons:create heroku-redis:premium-0
```

## Backend Deployment

### 1. Create Procfile

```bash
cat > Procfile << 'EOF'
web: python -m src.main --mode api --host 0.0.0.0 --port $PORT
EOF
```

### 2. Create runtime.txt

```bash
echo "python-3.10.13" > runtime.txt
```

### 3. Configure Environment Variables

```bash
heroku config:set ENVIRONMENT=production
heroku config:set DEBUG=False
heroku config:set LOG_LEVEL=INFO
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
heroku config:set RATE_LIMIT=60
```

### 4. Deploy Backend

```bash
# Add Heroku remote
heroku git:remote -a aais-app

# Deploy
git push heroku main

# View logs
heroku logs --tail

# Check status
heroku ps
```

## Frontend Deployment

### Option 1: Deploy with Backend

```bash
# Update Procfile
cat > Procfile << 'EOF'
web: python -m src.main --mode api --host 0.0.0.0 --port $PORT
release: npm run build --prefix frontend
EOF

# Deploy
git push heroku main
```

### Option 2: Deploy to Netlify (Recommended)

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy frontend
cd frontend
netlify deploy --prod
```

## Database Setup

### Run Migrations

```bash
# Connect to database
heroku pg:psql

# Or run migrations
heroku run python -m src.database
```

### Backup Database

```bash
# Create backup
heroku pg:backups:capture

# List backups
heroku pg:backups

# Download backup
heroku pg:backups:download
```

## Scaling

### Dyno Types

```bash
# Free tier (sleeps after 30 min inactivity)
heroku ps:type free

# Hobby tier ($7/month, always on)
heroku ps:type hobby

# Standard tier ($50/month, better performance)
heroku ps:type standard-1x
```

### Scale Dynos

```bash
# Scale to 2 dynos
heroku ps:scale web=2

# View current dynos
heroku ps
```

## Monitoring

### View Logs

```bash
# Real-time logs
heroku logs --tail

# Specific number of lines
heroku logs -n 100

# Filter by process
heroku logs --dyno web
```

### Metrics

```bash
# View metrics
heroku metrics

# View dyno stats
heroku ps:exec
```

## Custom Domain

```bash
# Add domain
heroku domains:add www.aais.example.com

# Update DNS records
# Point to: aais-app.herokuapp.com

# Verify domain
heroku domains
```

## Environment Variables

```bash
# Set variable
heroku config:set KEY=value

# View all variables
heroku config

# Remove variable
heroku config:unset KEY
```

## Addons

### Available Addons

```bash
# PostgreSQL
heroku addons:create heroku-postgresql:standard-0

# Redis
heroku addons:create heroku-redis:premium-0

# Monitoring
heroku addons:create papertrail:choklad

# Email
heroku addons:create sendgrid:starter

# View addons
heroku addons
```

## Continuous Deployment

### GitHub Integration

1. Go to Heroku Dashboard
2. Select app
3. Go to Deploy tab
4. Connect GitHub
5. Select repository
6. Enable auto-deploy

### GitLab Integration

```bash
# Add Heroku remote
heroku git:remote -a aais-app

# Push to deploy
git push heroku main
```

## Troubleshooting

### App Won't Start

```bash
# Check logs
heroku logs --tail

# Check dyno status
heroku ps

# Restart dyno
heroku restart
```

### Database Connection Error

```bash
# Check database URL
heroku config:get DATABASE_URL

# Connect to database
heroku pg:psql

# Check database status
heroku pg:info
```

### Out of Memory

```bash
# Upgrade dyno type
heroku ps:type standard-1x

# Check memory usage
heroku ps:exec
```

## Cost Breakdown

- **Free Tier**: $0 (sleeps after 30 min)
- **Hobby Dyno**: $7/month
- **Standard Dyno**: $50/month
- **PostgreSQL**: $9-50/month
- **Redis**: $15-50/month
- **Total**: $31-157/month

## Production Checklist

- [ ] Set DEBUG=False
- [ ] Set strong SECRET_KEY
- [ ] Configure database backups
- [ ] Setup monitoring
- [ ] Configure custom domain
- [ ] Enable HTTPS
- [ ] Setup error tracking
- [ ] Configure email service
- [ ] Setup logging
- [ ] Test disaster recovery

## Useful Commands

```bash
# Open app in browser
heroku open

# Run one-off command
heroku run python script.py

# Access shell
heroku run bash

# View app info
heroku apps:info

# Rename app
heroku apps:rename new-name

# Delete app
heroku apps:destroy
```

## Support

- Heroku Dashboard: https://dashboard.heroku.com
- Heroku Documentation: https://devcenter.heroku.com
- Heroku Support: https://help.heroku.com
