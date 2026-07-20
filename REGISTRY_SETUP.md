# Docker Registry Push Configuration

## 1. GitHub Container Registry (GHCR)

### Authentication
```bash
# Generate a GitHub Personal Access Token (PAT) with `write:packages` scope
# https://github.com/settings/tokens/new

# Login to GHCR
echo $PAT | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Or use GitHub CLI
gh auth token | docker login ghcr.io -u $(gh api user -q .login) --password-stdin
```

### Push Images
```bash
# Tag and push
docker tag aaes-os/platform-api:latest ghcr.io/your-org/aaes-os/platform-api:latest
docker tag aaes-os/platform-api:latest ghcr.io/your-org/aaes-os/platform-api:v1.0.0

docker push ghcr.io/your-org/aaes-os/platform-api:latest
docker push ghcr.io/your-org/aaes-os/platform-api:v1.0.0
```

## 2. Docker Hub

### Authentication
```bash
# Login to Docker Hub
docker login

# Set your Docker Hub username as environment variable
export DOCKER_HUB_USER=your-username
```

### Push Images
```bash
docker tag aaes-os/platform-api:latest $DOCKER_HUB_USER/aaes-os/platform-api:latest
docker push $DOCKER_HUB_USER/aaes-os/platform-api:latest
```

## 3. Private Docker Registry

### Authentication
```bash
docker login registry.your-company.com -u username -p password

# Create Kubernetes secret
kubectl create secret docker-registry regcred \
  --docker-server=registry.your-company.com \
  --docker-username=username \
  --docker-password=password \
  --docker-email=user@example.com \
  -n aaes-os
```

### Push Images
```bash
docker tag aaes-os/platform-api:latest registry.your-company.com/aaes-os/platform-api:latest
docker push registry.your-company.com/aaes-os/platform-api:latest
```

## 4. Using `.docker/config.json` for Multiple Registries

Create ~/.docker/config.json:
```json
{
  "auths": {
    "ghcr.io": {
      "auth": "base64(username:token)"
    },
    "docker.io": {
      "auth": "base64(username:password)"
    },
    "registry.your-company.com": {
      "auth": "base64(username:password)"
    }
  }
}
```

## 5. CI/CD with GitHub Actions

Your .github/workflows/build-and-push.yml already handles this!

Key features:
- Builds on `push` to main/develop and on tags
- Pushes to GHCR (ghcr.io/your-org/aaes-os/...)
- Uses Docker Buildx for multi-platform support
- Runs tests and security scans (Trivy)

Example: After PR merge, images are automatically:
1. Built with multi-platform support
2. Pushed to GHCR as: `ghcr.io/your-org/aaes-os/platform-api:branch-name`
3. Scanned for vulnerabilities
4. Tagged as latest on main branch

## 6. Kubernetes Image Pull Secrets

If using a private registry, update k8s/aaes-os-production.yaml:

```yaml
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred  # Created via kubectl create secret docker-registry
      containers:
      - name: platform-api
        image: registry.your-company.com/aaes-os/platform-api:v1.0.0
```

## 7. Local Development with Docker Compose

Push to local registry or development registry:
```bash
# Build
docker compose build

# Push to your registry
docker compose push
```

## 8. Image Tagging Strategy

Recommended tagging:
```
ghcr.io/your-org/aaes-os/platform-api:latest       # Latest stable
ghcr.io/your-org/aaes-os/platform-api:v1.2.3       # Semantic version
ghcr.io/your-org/aaes-os/platform-api:develop      # Develop branch
ghcr.io/your-org/aaes-os/platform-api:main-abc123  # Main branch with commit
```

## 9. Security: Image Scanning

Trivy is already integrated in GitHub Actions. To scan locally:
```bash
trivy image ghcr.io/your-org/aaes-os/platform-api:latest

# Generate SBOM (Software Bill of Materials)
trivy image --format cyclonedx ghcr.io/your-org/aaes-os/platform-api:latest > sbom.json
```

## 10. Registry Comparison

| Feature | GHCR | Docker Hub | Private |
|---------|------|-----------|---------|
| Free tier | Yes (public) | Yes | No |
| Private repos | 500 free actions | Paid | Own |
| Bandwidth | Unlimited | 100GB/6h | Unlimited |
| CI/CD integration | Native | Via token | Via secret |
| Security scanning | Via Trivy | Paid | Via Trivy |
