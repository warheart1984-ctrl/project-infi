# Constitutional Evidence Framework (CEF) — Specification v1.0

**Status:** Specified — v1.0  
**Charter:** [CEF_V1_CHARTER.md](./CEF_V1_CHARTER.md)  
**Effective date:** 2026-07-20

## 1. Purpose

CEF v1.0 defines a unified constitutional architecture for evidence across all governed systems. It provides a single abstract model with multiple specialized profiles, ensuring consistency, replayability, auditability, and stewardship.

## 2. Core Invariants

1. No claim may exceed its evidence.
2. All evidence must be replayable.
3. All evidence must be auditable.
4. All evidence must be bound to authority.
5. All evidence must be versioned.
6. All evidence must be promotable only through governed decisions.

(See also Charter Article II for the completeness / verifiability formulation.)

Foundational corrective cycle: Charter [Article III-A — Foundational Epistemic Cycle](./CEF_V1_CHARTER.md#article-iii-a--foundational-epistemic-cycle) (Imagination → Design → Implementation → Verification → Reality → Evidence → Understanding → Improved Design; Axiom V).

## 3. Evidence Object Model

Every evidence object MUST contain:

| Field | Description |
| --- | --- |
| `id` | Globally unique identifier |
| `type` | Profile type (`CREC`, `OEL`, `CEL`, `Security`, `ModelEval`) |
| `version` | Schema version |
| `authority` | CAR reference (`carId`, `actorId`, `role`) |
| `context` | Domain-specific metadata |
| `inputs` | Data, artifacts, advisory outputs |
| `verification` | Checks, gates, validations |
| `lineage` | Parent evidence, prior versions |
| `replay` | Deterministic reconstruction instructions |
| `audit` | Visibility and disclosure metadata |
| `promotion` | Decision, signature, timestamp |

Machine schema: [schemas/cef-core-evidence.schema.json](./schemas/cef-core-evidence.schema.json)

## 4. Profiles

| Profile | Role |
| --- | --- |
| **CREC** | Research Evidence |
| **OEL** | Operational Evidence |
| **CEL** | Linguistic / Constitutional Evidence |
| **Security** | SBOM, supply chain, vulnerability, policy gates |
| **ModelEval** | Benchmarks, risk, uncertainty, lineage |

Each profile inherits CEF core invariants and extends the evidence object model with domain-specific fields.

- OEL profile: [../operational-evidence-layer/CEF_PROFILE_OEL_V1.md](../operational-evidence-layer/CEF_PROFILE_OEL_V1.md)
- Registry: [cef-profile-registry.json](./cef-profile-registry.json)

## 5. Certification Engine

The Certification Engine is the constitutional mechanism that promotes evidence into certificates. It enforces:

- Authority
- Verification
- Replay
- Audit
- Stewardship

Certificates are immutable, signed, and reproducible.

Spec: [CERTIFICATION_ENGINE_V1.md](./CERTIFICATION_ENGINE_V1.md)

## 6. Architecture diagram

```text
                 Constitutional Evidence Framework (CEF)
                 ----------------------------------------
                                |   Core Invariants   |
                                |  Replay • Audit     |
                                |  Authority • Version|
                                -----------------------
        ---------------------------------------------------------------
        |                         Profiles                           |
        ---------------------------------------------------------------
        |                                                             |
        |   CREC (Research)     OEL (Operations)     CEL (Language)  |
        |                                                             |
        |   Security Evidence    ModelEval Evidence   Certification   |
        |                                                             |
        ---------------------------------------------------------------
                                |
                                v
                     -------------------------------
                     |     Certification Engine     |
                     |-------------------------------|
                     | Promotion Decision           |
                     | Verification Gates           |
                     | Authority Check (CAR)        |
                     | Signature + Replay Identity  |
                     -------------------------------
                                |
                                v
                     -------------------------------
                     |        Certificate           |
                     |-------------------------------|
                     | Immutable                    |
                     | Replayable                   |
                     | Auditable                    |
                     | Stewardship State            |
                     -------------------------------
                                |
                                v
                     -------------------------------
                     |         Stewardship          |
                     |-------------------------------|
                     | Renewal • Revocation         |
                     | Historical Replay            |
                     | Audit Disclosure             |
                     -------------------------------
```

Also: [CEF_V1_ARCHITECTURE.txt](./CEF_V1_ARCHITECTURE.txt)

## 7. Companion artifacts

| Artifact | Path |
| --- | --- |
| Charter | [CEF_V1_CHARTER.md](./CEF_V1_CHARTER.md) |
| Promotion Workflow | [PROMOTION_WORKFLOW_V1.md](./PROMOTION_WORKFLOW_V1.md) |
| Stewardship Protocol | [STEWARDSHIP_PROTOCOL_V1.md](./STEWARDSHIP_PROTOCOL_V1.md) |
| Implementation Plan | [CEF_V1_IMPLEMENTATION_PLAN.md](./CEF_V1_IMPLEMENTATION_PLAN.md) |
| Conformance Suite | [conformance/CEF_V1_CONFORMANCE_SUITE.md](./conformance/CEF_V1_CONFORMANCE_SUITE.md) |
| Stewardship Dashboard | [observability/CEF_V1_STEWARDSHIP_DASHBOARD.md](./observability/CEF_V1_STEWARDSHIP_DASHBOARD.md) |
| Core schema | [schemas/cef-core-evidence.schema.json](./schemas/cef-core-evidence.schema.json) |
| OEL schema | [schemas/cef-oel-evidence.schema.json](./schemas/cef-oel-evidence.schema.json) |
| Certificate schema | [schemas/cef-certificate.schema.json](./schemas/cef-certificate.schema.json) |
