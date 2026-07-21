# AAES-OS Docker Quick Reference

## Quick Start

**Development environment:**
```bash
docker compose up -d
docker compose ps
```

**View logs:**
```bash
docker compose logs -f platform-api
docker compose logs -f platform-web
```

**Stop all services:**
```bash
docker compose down
```

## Building Individual Images

**Build a specific service:**
```bash
docker build --build-arg SERVICE=platform-api -t aaes-os/platform-api:dev .
docker build --build-arg SERVICE=platform-web -t aaes-os/platform-web:dev .
docker build --build-arg SERVICE=ops-console -t aaes-os/ops-console:dev .
```

**Run standalone:**
```bash
docker run -p 3000:3000 -e NODE_ENV=development aaes-os/platform-api:dev
```

## Services & Ports

| Service | Port | Purpose |
|---------|------|---------|
| platform-api | 3000 | REST API |
| ops-console | 3001 | Telemetry/HTTP surface |
| platform-web | 3002 | Next.js dashboard |
| sovereign-control | 3003 | Control plane |
| uss-api | 3004 | USS API |

## Kubernetes Deployment

**Apply the manifest:**
```bash
kubectl apply -f k8s/aaes-os-production.yaml
```

**Check deployment status:**
```bash
kubectl get deployments -n aaes-os
kubectl get pods -n aaes-os
kubectl describe deployment platform-api -n aaes-os
```

**View logs:**
```bash
kubectl logs -f deployment/platform-api -n aaes-os
```

**Update deployment image:**
```bash
kubectl set image deployment/platform-api platform-api=ghcr.io/your-org/aaes-os/platform-api:v1.0 -n aaes-os
```

## CI/CD Pipeline

GitHub Actions workflow: `.github/workflows/build-and-push.yml`

**Triggers:**
- Push to `main` or `develop`
- Git tags (v*)
- Pull requests

**Jobs:**
- Build and push to `ghcr.io`
- Run tests and linting
- Security scanning with Trivy

## Environment Variables

Create `.env` file in root:
```bash
NODE_ENV=development
SOVREN_LAW_KEY=your-key-here
LOG_LEVEL=info
```

## Health Checks

All services expose `/health` and `/ready` endpoints:
```bash
curl http://localhost:3000/health
curl http://localhost:3001/health
```

## Troubleshooting

**Container won't start:**
```bash
docker compose logs platform-api
docker inspect <container-id>
```

**Port already in use:**
```bash
# Change port in docker-compose.yml
# Or kill the service: docker compose down -v
```

**Rebuild from scratch:**
```bash
docker compose down -v
docker system prune -a
docker compose up -d --build
```

**Network issues:**
```bash
docker network inspect aaes-mesh
docker exec <container-id> wget -O- http://platform-api:3000/health
```

## Image Optimization

- **Multi-stage build**: ~200MB for Node.js service
- **Alpine Linux**: Reduced attack surface
- **Non-root user**: Running as `nodejs:1001`
- **Layer caching**: pnpm lock, dependencies, then source

## Registry & Tagging

**Push to Docker Hub:**
```bash
docker tag aaes-os/platform-api:latest myregistry/platform-api:1.0.0
docker push myregistry/platform-api:1.0.0
```

**Push to ghcr.io (GitHub Container Registry):**
```bash
docker tag aaes-os/platform-api:latest ghcr.io/your-org/aaes-os/platform-api:latest
docker push ghcr.io/your-org/aaes-os/platform-api:latest
```

## Security Best Practices

✅ Multi-stage builds to minimize final image size
✅ Non-root user (nodejs:1001)
✅ Read-only root filesystem in k8s
✅ Security context and capabilities drops
✅ Pod security policies via RBAC
✅ Resource requests/limits
✅ Network policies (can be added)
✅ Trivy vulnerability scanning in CI/CD
✅ dumb-init for proper signal handling

## Docker Buildx (Optional: Multi-platform builds)

```bash
docker buildx create --name aaes-builder
docker buildx use aaes-builder
docker buildx build --platform linux/amd64,linux/arm64 \
  --build-arg SERVICE=platform-api \
  -t ghcr.io/your-org/aaes-os/platform-api:latest \
  --push .
```
