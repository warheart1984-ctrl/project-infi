# Operational Evidence Layer (OEL) v1.0

**Status:** Specified — Companion to AAES-OS Production Baseline v1.0  
**CEF profile:** `OEL` (see [Constitutional Evidence Framework](../cef/CONSTITUTIONAL_EVIDENCE_FRAMEWORK.md))  
**Effective date:** 2026-07-20  
**Layer position:** Deployment → **Evidence Record** → Promotion Decision → Stewardship

## Purpose

The Operational Evidence Layer applies the same governance philosophy used in constitutional runtime work to **operations**.

Instead of asserting:

> Version 1.8 deployed.

Operators emit a **Deployment Certificate** backed by an **Evidence Record**:

| Field | Example |
| --- | --- |
| Deployment Certificate | `AAES-OS-DEPLOY-CERT-v1.0.0-7efa0c5f` |
| Image Digest | ✓ pinned |
| SBOM Verified | ✓ |
| Conformance Tests | 147/147 |
| Security Scan | PASS |
| Policy Validation | PASS |
| Promotion Authority | AAES Constitutional Runtime |
| Timestamp | ISO-8601 |

Configuration without evidence is not a verified deployment. Evidence without a promotion decision is not stewardship.

## Separation of concerns

```text
Deployment
    │
    ▼
Evidence Record
    ├── Version
    ├── Commit SHA
    ├── Container Digest(s)
    ├── SBOM
    ├── Vulnerability Scan
    ├── Conformance Tests
    ├── Runtime Health
    ├── Promotion Decision
    └── Approval Signature
    │
    ▼
Deployment Certificate (human + machine projection)
```

| Concern | Owns | Must not own |
| --- | --- | --- |
| Deployment | What was applied (manifests, images, cluster) | Whether it is constitutionally promotable |
| Evidence Record | Measurable facts about that deployment | Marketing claims |
| Promotion Decision | Allow / deny / conditional under authority | Rewriting evidence |
| Deployment Certificate | Signed projection of evidence + decision | Mutating underlying facts |

## Mapping to CREC

OEL is the **operational projection** of the Canonical Replay & Evidence Contract:

| CREC field | OEL counterpart |
| --- | --- |
| Intent | Deployment intent / change ticket / baseline ID |
| Authority | Promotion Authority (e.g. AAES Constitutional Runtime steward) |
| Evidence | Digests, SBOM, scan, tests, health snapshots |
| Verification | Certificate checks + independent reproduction |
| Compliance | Policy validation + NetworkPolicy / RBAC conformance |
| Truth Boundary | Explicit non-claims (what the certificate does not prove) |
| Replay Record | Commit + digest + manifest checksum set |
| Audit Trail | Runtime audit packets + CI run URLs |
| Failure Path | Recovery/failure procedures from Production Baseline |
| Proof Surface Level | P0–P5 on the certificate |
| Challenge Surface | What would invalidate the certificate |

## Recurring architectural motif

The same separation of concerns reappears across domains. This is intentional motif, not duplication:

| Domain | Constitution / Norm | Execution / Language | Evidence / Audit |
| --- | --- | --- | --- |
| **Mythar** | Constitutional Registry | Language → Compiler/Runtime | ISF + AAES envelope + conformance |
| **Sovereign X OS** | SOCK / CIS constitutional kernel | Intent → Execution | Execution proof + audit |
| **AAES-OS Ops** | Production Baseline freeze | Deployment → Runtime | **OEL Evidence Record + Certificate** |

Shared pattern:

```text
Normative Layer  →  Operational Layer  →  Evidence Layer  →  Stewardship
```

Each domain instantiates the motif with domain-specific artifacts, but the governance rule is identical: **no claim may exceed its evidence**.

## Required artifacts

| Artifact | Path |
| --- | --- |
| This specification | [OPERATIONAL_EVIDENCE_LAYER.md](./OPERATIONAL_EVIDENCE_LAYER.md) (this file) |
| Evidence Record schema | [operational-evidence-record.schema.json](./operational-evidence-record.schema.json) |
| Deployment Certificate schema | [deployment-certificate.schema.json](./deployment-certificate.schema.json) |
| Certificate template (markdown) | [DEPLOYMENT_CERTIFICATE_TEMPLATE.md](./DEPLOYMENT_CERTIFICATE_TEMPLATE.md) |
| Example certificate (Baseline v1.0) | [examples/aaes-os-production-baseline-v1.0.certificate.md](./examples/aaes-os-production-baseline-v1.0.certificate.md) |
| Example evidence record (JSON) | [examples/aaes-os-production-baseline-v1.0.evidence-record.json](./examples/aaes-os-production-baseline-v1.0.evidence-record.json) |

## Promotion gates

A Promotion Decision of `promote` REQUIRES:

1. Commit SHA matches the intended baseline or release boundary
2. Every production container is digest-pinned (not `latest` alone)
3. SBOM present or explicitly waived with authority + expiry
4. Vulnerability scan status is `PASS` or `PASS_WITH_ACCEPTED_RISK` (documented)
5. Conformance tests meet the declared threshold
6. Runtime health: required services Ready
7. Policy validation PASS
8. Approval signature present (steward identity + timestamp)

A Promotion Decision of `deny` or `hold` MUST record the failing gate(s) without mutating evidence fields.

## Truth boundary

OEL proves that a deployment instance was measured and (optionally) promoted under named authority.  
It does **not** prove constitutional completeness of unfinished runtime packages, nor that Mythar/Sovereign X product claims are true by association.

## Change control

OEL v1.0 is versioned with the Production Baseline family. Breaking schema changes require OEL v1.1+ and must not silently rewrite historical certificates.
