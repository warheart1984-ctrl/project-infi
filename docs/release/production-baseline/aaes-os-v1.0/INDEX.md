# AAES-OS Production Baseline v1.0 — Index

**Baseline ID:** `AAES-OS-PRODUCTION-BASELINE-v1.0`  
**Status:** Release Candidate Frozen (operational stack)  
**Frozen commit:** `7efa0c5f766bc0b30b6eef820d198be3a6bf1a5d`  
**Effective date:** 2026-07-20  
**Lifecycle position:** Deployment → Evidence → Independent Reproduction → Stewardship

## Purpose

Freeze the AAES-OS containerization and Kubernetes deployment stack as an **evidence-producing reference environment**, not merely a production configuration.

This baseline advances the stewardship chain:

```text
Architecture → Implementation → Deployment → Evidence → Independent Reproduction → Stewardship
```

## Canonical artifacts

| Artifact | Path |
| --- | --- |
| Freeze notice | [AAES_OS_PRODUCTION_BASELINE_FREEZE.md](./AAES_OS_PRODUCTION_BASELINE_FREEZE.md) |
| Baseline body | [AAES_OS_PRODUCTION_BASELINE_V1.md](./AAES_OS_PRODUCTION_BASELINE_V1.md) |
| Deployment receipt | [evidence/deployment-receipt.json](./evidence/deployment-receipt.json) |
| Evidence package | [evidence/](./evidence/) |
| CEF v1.0 | [../../cef/README.md](../../cef/README.md) |
| OEL Profile v1.0 | [../../operational-evidence-layer/CEF_PROFILE_OEL_V1.md](../../operational-evidence-layer/CEF_PROFILE_OEL_V1.md) |
| Baseline Certificate DRAFT | [../../operational-evidence-layer/certificates/baseline-v1.0.certificate.yaml](../../operational-evidence-layer/certificates/baseline-v1.0.certificate.yaml) |

## Evidence package contents

| Slot | File | Claim |
| --- | --- | --- |
| Immutable container image tags | [evidence/image-tags.json](./evidence/image-tags.json) | Tag immutability contract + digest policy |
| Kubernetes manifest version | [evidence/k8s-manifest-checksums.json](./evidence/k8s-manifest-checksums.json) | Frozen SHA-256 of deploy manifests |
| CI/CD provenance | [evidence/cicd-provenance.json](./evidence/cicd-provenance.json) | Workflow identity + build matrix |
| Security validation | [evidence/security-validation.md](./evidence/security-validation.md) | Trivy, network policy, pod security |
| Health/readiness validation | [evidence/health-readiness.md](./evidence/health-readiness.md) | Probe contracts + middleware |
| Scaling validation | [evidence/scaling-validation.md](./evidence/scaling-validation.md) | HPA ranges + verification procedure |
| Recovery/failure testing | [evidence/recovery-failure.md](./evidence/recovery-failure.md) | Failure contracts + rollback |
| Runtime audit records | [evidence/runtime-audit.md](./evidence/runtime-audit.md) | Audit surface + ledger linkage |
| Deployment evidence package | [evidence/deployment-evidence-package.json](./evidence/deployment-evidence-package.json) | Aggregate evidence index |
| Checksum re-verify (2026-07-31) | [evidence/checksum-reverify.json](./evidence/checksum-reverify.json) | Manifest hashes still match freeze |
| OEL evidence (cef-core validated) | [evidence/oel-evidence-validated.json](./evidence/oel-evidence-validated.json) | Schema + invariants; promotion **hold** |
| CEF validation receipt | [evidence/cef-core-validation-receipt.json](./evidence/cef-core-validation-receipt.json) | `@aaes-os/cef-core` test + validate receipt |
| Reproduction runbook | [evidence/REPRODUCTION_RUNBOOK.md](./evidence/REPRODUCTION_RUNBOOK.md) | Independent reproduction checklist |
| Live evidence pack | [evidence/live/](./evidence/live/) | Cluster capture (`STATUS.json`); pending until kubectl run |

## Related surfaces

- Deployment guide: [`DEPLOYMENT_GUIDE.md`](../../../../DEPLOYMENT_GUIDE.md)
- Implementation summary: [`IMPLEMENTATION_SUMMARY.md`](../../../../IMPLEMENTATION_SUMMARY.md)
- Registry setup: [`REGISTRY_SETUP.md`](../../../../REGISTRY_SETUP.md)
- Launch readiness: [`../launch-readiness-specification.md`](../launch-readiness-specification.md)
- Package production hardening: [`../production-hardening/README.md`](../production-hardening/README.md)
- Constitutional release receipt contract: [`../constitutional-release-receipt.md`](../constitutional-release-receipt.md)
- Operational Evidence Layer: [`../../operational-evidence-layer/OPERATIONAL_EVIDENCE_LAYER.md`](../../operational-evidence-layer/OPERATIONAL_EVIDENCE_LAYER.md)
- Recurring motif (Mythar / Sovereign X / Ops): [`../../operational-evidence-layer/RECURRING_ARCHITECTURAL_MOTIF.md`](../../operational-evidence-layer/RECURRING_ARCHITECTURAL_MOTIF.md)

## Truth boundary

This baseline freezes the **operational deployment stack** at commit `7efa0c5f`. It does **not** promote unfinished runtime package surfaces to production-complete status.

**ESFR gate (2026-07-31):** Independent reproduction (GHCR digests, live cluster capture, authority-signed ACTIVE certificate) is **waived** for PromotionEligibility. Those paths remain optional backlog under `evidence/live/` and the CI digest-merge job — not blockers for the current ESFR pass.

**Audience note (Drive-G-2):** Operator readiness for applying frozen manifests is **partial** (structure frozen; live digests/cluster optional). User/commercial self-serve readiness is **not** claimed by this baseline.
