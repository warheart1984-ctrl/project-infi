# Security Validation Results — AAES-OS Production Baseline v1.0

**Baseline:** `AAES-OS-PRODUCTION-BASELINE-v1.0`  
**Frozen commit:** `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d`  
**Status:** Controls declared and frozen; live scan artifacts pending

## In-scope controls

| Control | Source | Expected outcome |
| --- | --- | --- |
| Container FS vulnerability scan | `.github/workflows/build-and-push.yml` → Trivy | SARIF uploaded on push/PR |
| Zero-trust networking | `k8s/network-policies.yaml` | Default deny; explicit allow only |
| Non-root runtime | `k8s/aaes-os-production.yaml` | `runAsNonRoot: true`, UID 1001 |
| Read-only root FS | production Deployment containers | `readOnlyRootFilesystem: true` |
| Drop capabilities | production containers | `capabilities.drop: [ALL]` |
| No privilege escalation | production containers | `allowPrivilegeEscalation: false` |
| Minimal RBAC | Role + RoleBinding `aaes-os` | configmaps get/list/watch; secrets get |
| TLS termination | ingress + cert-manager | HTTPS at edge (env prerequisite) |
| Rate limiting | ingress annotations | 100 req/s, 10 concurrent (as documented) |

## Validation procedure

```bash
# 1. Confirm Trivy job exists and ran for the freeze commit
# Attach: Actions run URL + trivy-results.sarif

# 2. After apply, describe policies
kubectl get networkpolicy -n aaes-os
kubectl describe networkpolicy -n aaes-os

# 3. Confirm securityContext on a running pod
kubectl get pod -n aaes-os -l app=platform-api -o jsonpath='{.items[0].spec.securityContext}'
kubectl get pod -n aaes-os -l app=platform-api -o jsonpath='{.items[0].spec.containers[0].securityContext}'
```

## Results log

| Check | Result | Evidence |
| --- | --- | --- |
| Trivy workflow present | Pass (frozen) | `cicd-provenance.json` |
| NetworkPolicy manifests frozen | Pass | `k8s-manifest-checksums.json` |
| Pod security fields in manifest | Pass | `aaes-os-production.yaml` |
| Live Trivy SARIF for `7efa0c5f` | Pending | Attach CI artifact |
| Live NetworkPolicy deny test | Pending | `pending-cluster-execution` |

## Truth boundary

Declared controls are part of the frozen baseline. Passing this document without attached SARIF / cluster deny tests does **not** equal a completed security audit.
