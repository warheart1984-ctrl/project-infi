# Reproduction runbook — AAES-OS Production Baseline v1.0

**Status:** Optional backlog checklist. ESFR 2026-07-31 waived independent reproduction as a PromotionEligibility requirement.

## Prerequisites

- Checkout frozen commit: `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d`
- Cluster with NGINX ingress (or equivalent) and ability to create namespace `aaes-os`
- GHCR pull credentials for `ghcr.io/warheart1984-ctrl/aaes-os/*`

## Steps

1. Verify manifest checksums against [k8s-manifest-checksums.json](./k8s-manifest-checksums.json) (or latest [checksum-reverify.json](./checksum-reverify.json)).
2. Build or pull digest-pinned images; fill digests in [image-tags.json](./image-tags.json).
3. Create secrets (`platform-secrets`, e.g. `sovren-law-key`) per DEPLOYMENT_GUIDE.
4. Apply in order:
   - `kubectl apply -f k8s/network-policies.yaml`
   - `kubectl apply -f k8s/aaes-os-production.yaml`
   - `kubectl apply -f k8s/ingress-and-load-balancing.yaml`
5. Capture probe outputs for all five services → attach under `evidence/live/` (create when run).
6. Capture Trivy / GHCR scan artifacts → update [security-validation.md](./security-validation.md).
7. Capture HPA / scale test notes → [scaling-validation.md](./scaling-validation.md).
8. Run one failure/rollback drill → [recovery-failure.md](./recovery-failure.md).
9. Re-validate OEL evidence with `@aaes-os/cef-core` `validateProfile('OEL', …)`.
10. Only then consider promoting the OEL certificate from DRAFT / HOLD.

## Claim boundary

| Claim | When allowed |
|-------|----------------|
| Operational stack frozen | Checksums + freeze notice exist (current) |
| Independently reproduced ops | Steps 4–8 evidenced |
| Commercial / self-serve ready | Out of scope for this baseline |
