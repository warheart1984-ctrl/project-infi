# Health / Readiness Validation — AAES-OS Production Baseline v1.0

**Baseline:** `AAES-OS-PRODUCTION-BASELINE-v1.0`  
**Frozen commit:** `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d`  
**Middleware package:** `@aaes-os/healthcheck-middleware`

## Frozen contracts

| Endpoint | Semantics | Probe use |
| --- | --- | --- |
| `GET /health` | Process alive | Liveness |
| `GET /ready` | Dependencies healthy | Readiness |
| `GET /health/detailed` | Memory, uptime, check timings | Diagnostics |
| `GET /healthz` | Alias of `/health` | K8s-compatible |
| `GET /readyz` | Alias of `/ready` | K8s-compatible |

## Manifest probe mapping

From `k8s/aaes-os-production.yaml` (frozen):

- `platform-api`: liveness `/health`, readiness `/ready`
- `platform-web`: liveness/readiness `/` (UI surface)
- `ops-console`: liveness/readiness `/health`

Compose healthchecks use `wget` against `/health` (or `/` for platform-web).

## Validation procedure

```bash
# Local reference environment
docker compose up -d
curl -sf http://localhost:3000/health
curl -sf http://localhost:3000/ready
curl -sf http://localhost:3000/health/detailed

# Cluster
kubectl get pods -n aaes-os
kubectl describe pod -n aaes-os -l app=platform-api | findstr /i "Liveness Readiness"
```

## Results log

| Check | Result | Evidence |
| --- | --- | --- |
| Middleware package present | Pass | `packages/healthcheck-middleware/` |
| Manifest probes wired | Pass | production YAML checksum |
| Local compose probe success | Pending | operator attach |
| Cluster Ready=True all services | Pending | `pending-cluster-execution` |

## Failure contract

- Liveness failure → container restart
- Readiness failure → removed from Service endpoints; traffic must not route to not-ready pods
- `/ready` must not return 200 when declared dependency checks fail
