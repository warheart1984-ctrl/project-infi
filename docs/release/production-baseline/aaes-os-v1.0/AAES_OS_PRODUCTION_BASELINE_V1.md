# AAES-OS Production Baseline v1.0

**Baseline ID:** `AAES-OS-PRODUCTION-BASELINE-v1.0`  
**Status:** Release Candidate Frozen  
**Proof Surface Level:** P2-Verified (manifest/CI/config); P1-Implemented pending live-cluster reproduction for scaling & recovery  
**Frozen commit:** `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d`  
**Verification date:** 2026-07-20  
**Registry namespace (target):** `ghcr.io/warheart1984-ctrl/aaes-os`

---

## 1. Release identity

| Field | Value |
| --- | --- |
| Product | AAES-OS Operational Deployment Stack |
| Version | 1.0 |
| Kind | Production Baseline (operational reference environment) |
| Freeze notice | [AAES_OS_PRODUCTION_BASELINE_FREEZE.md](./AAES_OS_PRODUCTION_BASELINE_FREEZE.md) |
| Git commit | `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d` |
| Commit subject | Complete AAES-OS containerization and deployment stack |
| Commit timestamp | 2026-07-20 04:36:58 -0400 |

## 2. Stewardship chain

| Stage | v1.0 status |
| --- | --- |
| Architecture | Observed — deployment blueprint + network topology documented |
| Implementation | Observed — healthcheck middleware, Dockerfiles, compose, k8s manifests |
| Deployment | Observed — manifests + guides frozen; live apply pending operator cluster |
| Evidence | Observed — this package; cluster-execution slots pending |
| Independent Reproduction | Pending — third party must rebuild from freeze + evidence |
| Stewardship | Declared — change control in freeze notice §4 |

## 3. Reference topology

### 3.1 Services (v1.0 matrix)

| Service | Compose port | Role |
| --- | --- | --- |
| `platform-api` | 3000 | REST API |
| `platform-web` | 3002 | Dashboard |
| `ops-console` | 3001 | Telemetry / ops |
| `sovereign-control-plane` | 3003 | Constitutional control plane |
| `uss-api` | 3004 | USS API |

### 3.2 Kubernetes apply order (frozen)

```bash
kubectl apply -f k8s/network-policies.yaml
kubectl apply -f k8s/aaes-os-production.yaml
kubectl apply -f k8s/ingress-and-load-balancing.yaml
kubectl get hpa -n aaes-os
```

### 3.3 Health contracts (frozen)

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Liveness |
| `GET /ready` | Readiness |
| `GET /health/detailed` | Diagnostics |
| `GET /healthz`, `/readyz` | Kubernetes aliases |

## 4. Required evidence slots

Every v1.0 claim must map to an evidence file under `evidence/`:

1. **Immutable container image tags** → `image-tags.json`
2. **Kubernetes manifest version** → `k8s-manifest-checksums.json`
3. **Deployment evidence package** → `deployment-evidence-package.json`
4. **CI/CD provenance** → `cicd-provenance.json`
5. **Security validation results** → `security-validation.md`
6. **Health/readiness validation** → `health-readiness.md`
7. **Scaling validation** → `scaling-validation.md`
8. **Recovery/failure testing** → `recovery-failure.md`
9. **Runtime audit records** → `runtime-audit.md`
10. **Deployment receipt** → `deployment-receipt.json`

## 5. Known limitations

1. Manifests still contain placeholder `ghcr.io/your-org/aaes-os/*` in some docs/examples; operators must pin `ghcr.io/warheart1984-ctrl/aaes-os/<service>@sha256:<digest>`.
2. Live HPA / recovery / Trivy SARIF upload results require a cluster run and CI artifact retention — slots marked `pending-cluster-execution` until filled.
3. This baseline does not assert production completeness for unfinished package surfaces outside the five deployable services.
4. TLS depends on cert-manager + DNS; those are environmental prerequisites, not frozen in-repo certificates.

## 6. Truth boundary

**This baseline proves:** the operational stack at commit `7efa0c5f` is frozen, checksummed, and equipped with an evidence package structure suitable for independent reproduction.

**This baseline does not prove:** that every AAES-OS constitutional runtime package is production-ready, that a specific public cluster is currently running v1.0, or that Mythar/JACA/ESIF pilots are governed by this freeze.

## 7. Challenge surface

Evidence that would **invalidate** the v1.0 freeze claim:

- Manifest checksums diverge from `evidence/k8s-manifest-checksums.json` without a new version
- Images tagged `latest` are treated as the authoritative production pin (violates immutability policy)
- Network policies or HPA ranges change silently without version bump
- Health endpoints return success while readiness dependencies are unhealthy
- CI workflow no longer builds the five-service matrix or drops Trivy scanning

## 8. Independent reproduction checklist

1. Check out commit `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d`
2. Verify file hashes against `evidence/k8s-manifest-checksums.json`
3. Build or pull images per `evidence/image-tags.json` (digest pins preferred)
4. Confirm CI provenance fields against `.github/workflows/build-and-push.yml`
5. Apply manifests in frozen order; record kubectl outputs into the pending evidence slots
6. Execute health, scaling, and recovery procedures; attach results
7. Emit or update `deployment-receipt.json` verification timestamp

## 9. Next stewardship actions

1. Replace `your-org` placeholders with `warheart1984-ctrl` in manifests (v1.0.1 patch or v1.1)
2. Capture first live-cluster evidence pack (health, HPA, recovery)
3. Attach GHCR digests after first successful `build-and-push` on `main`
4. Optionally wire Mythar v0.2 as a pilot consumer of this baseline (out of freeze scope)
