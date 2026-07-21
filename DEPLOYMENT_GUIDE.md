# AAES-OS Complete Deployment Guide

## Overview

This guide covers:
1. **Healthchecks** — Kubernetes-compatible liveness/readiness probes
2. **Registry Setup** — Push images to GHCR, Docker Hub, or private registries
3. **Network Policies** — Zero-trust networking with explicit allow rules
4. **Ingress & Load Balancing** — NGINX ingress controller + TLS + HPA

---

## Part 1: Healthchecks

### What are Healthchecks?

- **Liveness Probe** (`/health`): Is the service running?
- **Readiness Probe** (`/ready`): Is the service ready to serve traffic?
- **Startup Probe** (`/ready`): Is the service initialized?

Kubernetes uses these to:
- Restart pods that hang or crash
- Remove unhealthy pods from load balancers
- Delay traffic until the service is ready

### Using the Healthcheck Middleware

All services now have `/health` and `/ready` endpoints. To integrate:

**For Express-based services (platform-api, ops-console):**

```typescript
import { mountHealthChecks } from '@aaes-os/healthcheck-middleware';

const app = express();

// Mount basic healthchecks
mountHealthChecks(app);

// Or with custom checks
mountHealthChecks(app, {
  checks: {
    database: async () => {
      // Check database connection
      return await db.ping();
    },
    redis: async () => {
      // Check Redis connection
      return await redis.ping();
    },
  },
  checkTimeout: 5000, // 5 second timeout per check
});
```

**Kubernetes Deployment:**

```yaml
spec:
  containers:
  - name: platform-api
    image: aaes-os/platform-api:latest
    livenessProbe:
      httpGet:
        path: /health
        port: 3000
      initialDelaySeconds: 10
      periodSeconds: 30
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: 3000
      initialDelaySeconds: 5
      periodSeconds: 10
      failureThreshold: 3
```

### Testing Healthchecks

```bash
# Liveness (always 200 if service is running)
curl http://localhost:3000/health
# {"status":"alive","timestamp":"...","uptime":123.45}

# Readiness (200 only if all checks pass)
curl http://localhost:3000/ready
# {"status":"ready","checks":{"db":true,"redis":true},"timestamp":"..."}

# Detailed status
curl http://localhost:3000/health/detailed
# {"status":"healthy","checks":{"db":{"status":"healthy","latency":5},...}}
```

---

## Part 2: Registry Setup

### Quick Start (GHCR)

```bash
# 1. Generate GitHub Personal Access Token (write:packages scope)
# https://github.com/settings/tokens/new

# 2. Login
echo YOUR_PAT | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# 3. Build & push
docker build -t ghcr.io/your-org/aaes-os/platform-api:v1.0.0 --build-arg SERVICE=platform-api .
docker push ghcr.io/your-org/aaes-os/platform-api:v1.0.0
```

### Automated Push (CI/CD)

The GitHub Actions workflow (`.github/workflows/build-and-push.yml`) automatically:

1. Builds images when you push to `main` or `develop`
2. Pushes to GHCR with these tags:
   - `ghcr.io/your-org/aaes-os/SERVICE:main` (on main)
   - `ghcr.io/your-org/aaes-os/SERVICE:develop` (on develop)
   - `ghcr.io/your-org/aaes-os/SERVICE:v1.2.3` (on git tags)
3. Scans for vulnerabilities with Trivy
4. Runs tests and linting

**To enable:**
1. Grant GitHub Actions permission to write packages (Settings > Actions > General)
2. Push to main or develop branch
3. Images appear in your GitHub organization's Packages

### Using Images in Kubernetes

Update `k8s/aaes-os-production.yaml`:

```yaml
containers:
- name: platform-api
  image: ghcr.io/your-org/aaes-os/platform-api:v1.0.0
  imagePullPolicy: IfNotPresent  # or Always for latest
```

For private registries, create a secret:

```bash
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=your-org \
  --docker-password=YOUR_PAT \
  -n aaes-os
```

Then add to deployment:
```yaml
spec:
  imagePullSecrets:
  - name: regcred
```

---

## Part 3: Network Policies

### What are Network Policies?

Network Policies define which pods can communicate with which. Without them, **any pod can talk to any other pod**.

Our setup enforces **zero-trust networking**:
- By default, all traffic is **denied**
- Only explicitly allowed connections are permitted
- Each service can only talk to required dependencies

### Policies Included

**platform-api** can receive traffic from:
- Ingress controller (external users)
- ops-console (internal)
- platform-web (internal)

**platform-api** can send traffic to:
- sovereign-control-plane
- uss-api
- External HTTPS (port 443)

**platform-web** can only talk to:
- Ingress (users)
- platform-api

(Similar isolation for ops-console, sovereign-control-plane, uss-api)

### Applying Network Policies

```bash
kubectl apply -f k8s/network-policies.yaml
```

### Testing Network Policies

```bash
# Test connectivity between pods
kubectl exec -it pod/platform-api-xxx -- curl http://platform-api:3000/health
kubectl exec -it pod/platform-web-xxx -- curl http://platform-api:3000/health

# This should fail (not allowed):
kubectl exec -it pod/uss-api-xxx -- curl http://ops-console:3000/health
```

### Debugging

If traffic is unexpectedly blocked:

```bash
# List policies
kubectl get networkpolicies -n aaes-os

# Describe policy
kubectl describe networkpolicy platform-api-netpol -n aaes-os

# Check pod labels
kubectl get pods -n aaes-os --show-labels

# View logs
kubectl logs deployment/platform-api -n aaes-os
```

---

## Part 4: Ingress & Load Balancing

### What is Ingress?

Ingress provides:
- **External hostname-based routing** (api.aaes-os.local → platform-api)
- **HTTPS/TLS termination** (automatic certificate management)
- **Rate limiting** (prevent abuse)
- **Path-based routing** (/api → platform-api, /web → platform-web)

### Setup Steps

#### 1. Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

Verify:
```bash
kubectl get svc -n ingress-nginx
# Should show LoadBalancer with EXTERNAL-IP
```

#### 2. Install Cert-Manager (Optional, for TLS)

```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

#### 3. Apply Ingress & HPA

```bash
kubectl apply -f k8s/ingress-and-load-balancing.yaml
```

This creates:
- Ingress routes (api.aaes-os.local, web.aaes-os.local, ops.aaes-os.local)
- TLS certificates (auto-renewed by cert-manager)
- Horizontal Pod Autoscalers (HPA) to scale based on CPU/memory

#### 4. Configure DNS

Point your domain to the ingress LoadBalancer IP:

```bash
# Get LoadBalancer IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# In your DNS provider:
api.aaes-os.local  A  <EXTERNAL-IP>
web.aaes-os.local  A  <EXTERNAL-IP>
ops.aaes-os.local  A  <EXTERNAL-IP>
```

### Testing Ingress

```bash
# Get LoadBalancer IP
LB_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test with Host header
curl -H "Host: api.aaes-os.local" http://$LB_IP/health
curl -H "Host: web.aaes-os.local" http://$LB_IP/
curl -H "Host: ops.aaes-os.local" http://$LB_IP/telemetry
```

### Horizontal Pod Autoscaling (HPA)

Platform API scales 3-10 replicas based on:
- CPU utilization > 70% → scale up
- CPU utilization < 50% → scale down

Platform Web scales 2-5 replicas based on:
- CPU utilization > 75% → scale up
- CPU utilization < 60% → scale down

Monitor HPA:
```bash
kubectl get hpa -n aaes-os
kubectl describe hpa platform-api-hpa -n aaes-os
```

### Load Balancing Strategy

Kubernetes Service uses **round-robin** by default:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: platform-api
spec:
  type: ClusterIP
  sessionAffinity: None  # None = round-robin, ClientIP = sticky sessions
  selector:
    app: platform-api
  ports:
  - port: 80
    targetPort: 3000
```

To enable sticky sessions (same client → same pod):
```yaml
sessionAffinity: ClientIP
sessionAffinityConfig:
  clientIP:
    timeoutSeconds: 10800  # 3 hours
```

---

## Complete Deployment Checklist

- [ ] **Healthchecks**: All services have `/health` and `/ready` endpoints
- [ ] **Registry**: Images pushed to GHCR/Docker Hub/private registry
- [ ] **Network Policies**: Applied (`k8s/network-policies.yaml`)
- [ ] **Ingress Controller**: NGINX installed and running
- [ ] **Ingress Routes**: Applied (`k8s/ingress-and-load-balancing.yaml`)
- [ ] **DNS**: Configured to point to ingress LoadBalancer IP
- [ ] **HPA**: Scaling policies applied
- [ ] **TLS**: Certificates provisioned by cert-manager
- [ ] **Monitoring**: Prometheus ServiceMonitor (optional)

---

## Deployment Workflow

### Local Development
```bash
docker compose up -d
# Services available at:
# - http://localhost:3000 (platform-api)
# - http://localhost:3002 (platform-web)
# - http://localhost:3001 (ops-console)
```

### Build & Push to Registry
```bash
docker build -t ghcr.io/your-org/aaes-os/platform-api:v1.0.0 --build-arg SERVICE=platform-api .
docker push ghcr.io/your-org/aaes-os/platform-api:v1.0.0
```

### Deploy to Kubernetes
```bash
# 1. Create namespace & secrets
kubectl create namespace aaes-os
kubectl create secret docker-registry regcred -n aaes-os \
  --docker-server=ghcr.io \
  --docker-username=your-org \
  --docker-password=YOUR_PAT

# 2. Apply network policies
kubectl apply -f k8s/network-policies.yaml

# 3. Apply deployments, services, ingress
kubectl apply -f k8s/aaes-os-production.yaml
kubectl apply -f k8s/ingress-and-load-balancing.yaml

# 4. Monitor rollout
kubectl rollout status deployment/platform-api -n aaes-os
kubectl get pods -n aaes-os
```

### Update Deployment
```bash
# Push new image
docker push ghcr.io/your-org/aaes-os/platform-api:v1.1.0

# Trigger rollout
kubectl set image deployment/platform-api platform-api=ghcr.io/your-org/aaes-os/platform-api:v1.1.0 -n aaes-os

# Monitor
kubectl rollout status deployment/platform-api -n aaes-os
```

### Rollback
```bash
kubectl rollout undo deployment/platform-api -n aaes-os
```

---

## Monitoring & Debugging

```bash
# Check service status
kubectl get all -n aaes-os

# View pod logs
kubectl logs deployment/platform-api -n aaes-os -f

# Describe pod for events
kubectl describe pod <pod-name> -n aaes-os

# Check ingress status
kubectl get ingress -n aaes-os
kubectl describe ingress aaes-os-ingress -n aaes-os

# Check network policies
kubectl get networkpolicies -n aaes-os
kubectl describe networkpolicy platform-api-netpol -n aaes-os

# Check HPA status
kubectl get hpa -n aaes-os
kubectl top pods -n aaes-os  # Requires metrics-server
```

---

## Next Steps

1. **CI/CD**: GitHub Actions automatically builds and pushes on every commit
2. **Monitoring**: Add Prometheus + Grafana for metrics
3. **Logging**: Add ELK or Loki for centralized logging
4. **Backup**: Set up etcd backups and PVC snapshots
5. **Disaster Recovery**: Test failover and rollback procedures
