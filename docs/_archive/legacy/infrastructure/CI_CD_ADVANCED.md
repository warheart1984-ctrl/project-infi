# Advanced CI/CD Pipeline Configuration

## Overview

This advanced CI/CD pipeline includes:
- Code validation and linting
- Comprehensive testing (unit, integration, performance)
- Security scanning (SAST, container, dependencies)
- Docker image building and pushing
- Multi-environment deployment
- Health monitoring and notifications

---

## Pipeline Stages

### 1. Validate Stage

**Purpose**: Check code quality and formatting

- **validate:lint** - Python code linting (flake8, black, isort, pylint)
- **validate:frontend** - Frontend linting (ESLint)
- **validate:docker** - Dockerfile validation (hadolint)

### 2. Test Stage

**Purpose**: Run comprehensive tests

- **test:backend** - Python unit tests with coverage
- **test:frontend** - React component tests
- **test:integration** - Docker Compose integration tests
- **test:performance** - Load testing with Locust

### 3. Build Stage

**Purpose**: Build and push Docker images

- **build:backend** - Build backend Docker image
- **build:frontend** - Build frontend Docker image
- **build:mobile** - Build mobile app (Android)

### 4. Security Stage

**Purpose**: Security scanning and vulnerability checks

- **security:sast** - Static Application Security Testing
- **security:container** - Container image scanning
- **security:dependency** - Dependency vulnerability scanning

### 5. Deploy Stage

**Purpose**: Deploy to staging and production

- **deploy:staging** - Deploy to staging environment
- **deploy:production** - Deploy to production environment
- **rollback:production** - Rollback production deployment

### 6. Monitor Stage

**Purpose**: Post-deployment monitoring

- **monitor:health** - Health checks
- **monitor:logs** - Log analysis
- **notify:slack** - Slack notifications

---

## Setup Instructions

### 1. Configure CI/CD Variables

Go to: **Project Settings → CI/CD → Variables**

```
CI_REGISTRY_USER          # GitLab registry username
CI_REGISTRY_PASSWORD      # GitLab registry password
STAGING_SERVER            # Staging server IP/hostname
STAGING_USER              # SSH user for staging
STAGING_SSH_KEY           # Base64 encoded SSH private key
PRODUCTION_SERVER         # Production server IP/hostname
PRODUCTION_USER           # SSH user for production
PRODUCTION_SSH_KEY        # Base64 encoded SSH private key
SLACK_WEBHOOK_URL         # Slack webhook for notifications
SONA_TOKEN                # SonarCloud token (optional)
```

### 2. Enable Advanced Features

```bash
# Copy advanced CI/CD configuration
cp .gitlab-ci-advanced.yml .gitlab-ci.yml

# Commit and push
git add .gitlab-ci.yml
git commit -m "Enable advanced CI/CD pipeline"
git push origin main
```

### 3. Setup Slack Notifications

1. Create Slack webhook: https://api.slack.com/messaging/webhooks
2. Add webhook URL to CI/CD variables
3. Pipeline will send notifications on deployment

---

## Pipeline Workflow

### Development Branch (develop)

```
Push → Validate → Test → Build → Security → Deploy:Staging (manual)
```

### Main Branch (main)

```
Push → Validate → Test → Build → Security → Deploy:Production (manual) → Monitor
```

### Release Tags

```
Tag → Validate → Test → Build → Security → Deploy:Production (manual) → Monitor
```

---

## Test Coverage Requirements

- **Backend**: Minimum 80% code coverage
- **Frontend**: Minimum 70% code coverage
- **Integration**: All critical paths tested
- **Performance**: Response time < 500ms (p95)

---

## Security Scanning

### SAST (Static Application Security Testing)

- Bandit: Python security issues
- Semgrep: Code pattern matching
- Safety: Dependency vulnerabilities

### Container Scanning

- Trivy: Container image vulnerabilities
- Checks for HIGH and CRITICAL severity issues

### Dependency Scanning

- pip-audit: Python package vulnerabilities
- npm audit: JavaScript package vulnerabilities

---

## Deployment Strategy

### Staging Deployment

1. Automatic on develop branch
2. Manual trigger required
3. Smoke tests run after deployment
4. Health checks verify deployment

### Production Deployment

1. Manual trigger required
2. Only from main branch or tags
3. Health checks verify deployment
4. Logs monitored for errors
5. Slack notification sent

### Rollback

1. Manual trigger available
2. Reverts to previous version
3. Health checks verify rollback
4. Slack notification sent

---

## Monitoring & Alerts

### Health Checks

```bash
# API health endpoint
curl http://server/health

# Analytics endpoint
curl http://server/api/analytics/performance
```

### Log Monitoring

```bash
# Check for errors
docker-compose logs --tail=100 backend | grep -i error
```

### Slack Notifications

- Deployment status
- Build failures
- Security issues
- Performance metrics

---

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Test Coverage | > 80% | ✓ |
| Build Time | < 10 min | ✓ |
| Deployment Time | < 5 min | ✓ |
| Health Check | < 30s | ✓ |
| Security Scan | < 2 min | ✓ |

---

## Troubleshooting

### Pipeline Fails at Validation

```bash
# Run linting locally
flake8 src/
black src/
isort src/
```

### Tests Failing

```bash
# Run tests locally
pytest tests/ -v
npm test
```

### Deployment Fails

```bash
# Check SSH connection
ssh -i ~/.ssh/id_rsa user@server

# Check Docker on server
docker ps
docker-compose ps
```

### Security Scan Issues

```bash
# Run security checks locally
bandit -r src/
safety check
semgrep --config=p/security-audit src/
```

---

## Best Practices

1. **Always test locally before pushing**
   ```bash
   pytest tests/
   npm test
   ```

2. **Use meaningful commit messages**
   ```
   feat: Add new feature
   fix: Fix bug
   docs: Update documentation
   ```

3. **Create merge requests for code review**
   - Tests must pass
   - Code review required
   - Security checks must pass

4. **Tag releases**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

5. **Monitor deployments**
   - Check health endpoints
   - Monitor error rates
   - Review logs
   - Be ready to rollback

---

## Cost Optimization

- Cache dependencies to reduce build time
- Parallel job execution
- Only build on relevant branches
- Cleanup old artifacts

---

## Support

- GitLab CI/CD Docs: https://docs.gitlab.com/ee/ci/
- Pipeline Configuration: https://docs.gitlab.com/ee/ci/yaml/
- Best Practices: https://docs.gitlab.com/ee/ci/pipelines/pipeline_efficiency.html
