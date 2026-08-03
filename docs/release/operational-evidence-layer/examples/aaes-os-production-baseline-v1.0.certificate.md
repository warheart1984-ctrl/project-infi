# Deployment Certificate — AAES-OS Production Baseline v1.0

| Field | Value |
| --- | --- |
| **Deployment Certificate** | `AAES-OS-DEPLOY-CERT-baseline-v1.0-7efa0c5f` |
| **Version** | Production Baseline v1.0 |
| **Commit SHA** | `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d` |
| **Image Digest** | ☐ pending — digests not yet pinned from GHCR push |
| **SBOM Verified** | ☐ pending — SBOM artifact not yet attached |
| **Conformance Tests** | PENDING / declared suites not yet bound to this cert |
| **Security Scan** | PENDING — Trivy workflow frozen; SARIF not yet attached |
| **Policy Validation** | PASS (manifest-level) — NetworkPolicy + pod security frozen in baseline |
| **Runtime Health** | pending — awaiting cluster probe snapshot |
| **Promotion Authority** | AAES Constitutional Runtime |
| **Promotion Decision** | **hold** — awaiting digest, SBOM, scan, health gates |
| **Approval Signature** | pending — steward sign-off after gates clear |
| **Timestamp** | `2026-07-20T15:54:00Z` |
| **Overall Status** | **DRAFT** (evidence structure certified; deployment instance not yet promoted) |
| **Proof Surface Level** | P2 (baseline freeze) → P3 when live gates filled |

### Why this is not “Version 1.0 deployed”

The Production Baseline freezes the **operational stack**. This certificate refuses the shorthand claim “deployed” until digests, SBOM, scan, conformance, and health are evidenced. That is the same governance rule as constitutional proof surfaces: **claims may not exceed evidence**.

### Truth boundary

This certificate proves the OEL record exists for baseline `AAES-OS-PRODUCTION-BASELINE-v1.0` at commit `7efa0c5f`. It does **not** prove a live cluster is running a promoted production release.

### Challenge surface

- Any production pin using mutable `latest` without digest
- Checksum drift against `docs/release/production-baseline/aaes-os-v1.0/evidence/k8s-manifest-checksums.json`
- Promotion Decision flipped to `promote` while gates remain pending

### Evidence record reference

[aaes-os-production-baseline-v1.0.evidence-record.json](./aaes-os-production-baseline-v1.0.evidence-record.json)

### Related baseline

[../../production-baseline/aaes-os-v1.0/INDEX.md](../../production-baseline/aaes-os-v1.0/INDEX.md)
