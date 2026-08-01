# AAES-OS Production Baseline v1.0 Freeze Notice

**Release family:** AAES-OS operational baseline  
**Status:** Frozen  
**Effective date:** 2026-07-20  
**Scope:** Containerization, CI/CD registry push, Kubernetes production manifests, health/readiness, network policy, ingress/HPA  
**Frozen commit:** `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d`  
**Freeze message:** Complete AAES-OS containerization and deployment stack

---

## 1. Freeze declaration

AAES-OS Production Baseline v1.0 is hereby designated **Frozen** and constitutes the first **operational** baseline for the AAES-OS deployment stack.

This freeze establishes the normative foundation for deployment evidence, independent reproduction, security validation, and stewardship of the reference environment.

It is the operational counterpart to constitutional freezes such as CIS Core v1.0: constitutional baselines govern normative requirements; this baseline governs **how the platform is deployed, verified, and reproduced**.

## 2. Frozen baseline

The frozen operational baseline is represented by the following release artifacts:

### 2.1 Normative documents

- [INDEX.md](./INDEX.md)
- [AAES_OS_PRODUCTION_BASELINE_V1.md](./AAES_OS_PRODUCTION_BASELINE_V1.md)
- [evidence/deployment-receipt.json](./evidence/deployment-receipt.json)
- [evidence/deployment-evidence-package.json](./evidence/deployment-evidence-package.json)

### 2.2 Frozen deployment sources (commit `7efa0c5f`)

| Path | Role |
| --- | --- |
| `k8s/aaes-os-production.yaml` | Namespace, Deployments, Services, RBAC, PDBs |
| `k8s/network-policies.yaml` | Zero-trust NetworkPolicy set |
| `k8s/ingress-and-load-balancing.yaml` | Ingress, TLS hooks, HPA |
| `docker-compose.yml` | Local reference compose stack |
| `.github/workflows/build-and-push.yml` | GHCR build/push + Trivy scan |
| `packages/healthcheck-middleware/` | Liveness/readiness middleware |
| `DEPLOYMENT_GUIDE.md` | Operator deployment procedure |
| `REGISTRY_SETUP.md` | Registry authentication & tagging |
| `IMPLEMENTATION_SUMMARY.md` | Stack completion record |

Checksums for these sources are frozen in [evidence/k8s-manifest-checksums.json](./evidence/k8s-manifest-checksums.json).

## 3. Operational meaning

This baseline is the sole authoritative **operational** source for:

1. Which container images and tag policy constitute a reproducible deploy
2. Which Kubernetes manifests define the v1.0 reference topology
3. Which CI/CD workflow produces provenance for images
4. Which health/readiness contracts operators must satisfy
5. Which security controls (network policy, pod security, scanning) are in scope
6. Which evidence slots must be filled before claiming independent reproduction

Downstream profiles, pilots (including Mythar AAES integration), and rapid evolution **must remain traceable** to this frozen operational baseline.

## 4. Change control

Any change to frozen manifests, image-tag policy, health contracts, network policy semantics, or HPA ranges that alters the v1.0 reference environment must:

1. Open a governed change record (CCR-style or CRR amendment)
2. Produce a new baseline version (`v1.1` or `v2.0`) — **do not mutate v1.0 in place**
3. Re-emit the evidence package and deployment receipt
4. Preserve v1.0 artifacts for historical independent reproduction

No informal agreement, local cluster tweak, or downstream pilot may alter the frozen v1.0 baseline documents without versioning.

## 5. Relationship to companion surfaces

| Surface | Relationship |
| --- | --- |
| CIS Core / SOCK constitutional specs | Normative authority remains constitutional; this freeze does not redefine CIS terms |
| `docs/release/production-hardening/` | Package-level replay/audit evidence; complementary, not superseded |
| Launch readiness specification | This baseline is one Release Candidate Frozen artifact under that lifecycle |
| Mythar / JACA / ESIF pilots | May consume this environment; must not redefine its freeze boundary |

## 6. Stewardship rule

**Configuration without evidence is not a baseline.**  
Operators may apply the manifests; stewardship requires the evidence package slots to be filled or explicitly marked pending with a reproduction plan.
