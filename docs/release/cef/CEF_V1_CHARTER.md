# Constitutional Evidence Framework (CEF) — Charter v1.0

**Status:** Constitutional Charter — Frozen for CEF v1.0  
**Effective date:** 2026-07-20  
**Invariant:** No claim may exceed its evidence.

---

## Preamble

The Constitutional Evidence Framework (CEF) establishes the unified architecture for evidence generation, verification, promotion, replay, audit, and stewardship across governed systems. CEF ensures that all claims, actions, deployments, research outputs, linguistic artifacts, and model evaluations adhere to the constitutional invariant:

**No claim may exceed its evidence.**

CEF is grounded in the recognition that systems must coexist with reality rather than attempt to dominate it. Evidence serves as the constitutional interface between intention and the world as it actually behaves.

## Article I — Purpose and Scope

1. CEF provides a single abstract evidence model.
2. All evidence systems (CREC, OEL, CEL, Security, ModelEval) are **profiles** of CEF.
3. CEF governs evidence across research, operations, language, security, model evaluation, certification, and stewardship.
4. CEF ensures reproducibility, auditability, and constitutional integrity.

## Article II — Constitutional Invariants

1. No claim may exceed its evidence.
2. All evidence must be replayable.
3. All evidence must be auditable.
4. All evidence must be bound to authority.
5. All evidence must be versioned.
6. All evidence must be promotable only through governed decisions.

## Article III — Foundational Axiom: Reality as the Senior Engineer

### Axiom I — Reality is the final arbiter of system behavior

All constitutional evidence must reflect the system as it actually behaves, not as it was intended to behave.

### Axiom II — Evidence must incorporate correction from reality

Systems, models, deployments, and research must allow real-world behavior to correct assumptions, refine invariants, and update evidence records.

### Axiom III — Engineering discipline requires alignment with reality

CEF recognizes that the deepest engineering discipline is not control, but harmonization — designing systems that survive contact with reality because they were shaped by it.

### Axiom IV — Evidence is the mechanism of alignment

Evidence binds constitutional intent to operational truth. Evidence is how systems learn, adapt, and remain trustworthy.

This axiom applies uniformly across all profiles:

| Profile | Domain |
| --- | --- |
| **CREC** | Research |
| **OEL** | Operations |
| **CEL** | Linguistic / Constitutional |
| **Security** | Security Evidence |
| **ModelEval** | Model Evaluation Evidence |

Every profile must treat reality as the authoritative source of correction.

## Article III-A — Foundational Epistemic Cycle

### Epistemic Cycle of Constitutional Engineering

Constitutional engineering proceeds through a closed corrective cycle:

1. **Imagination** — Conceive what the system might become.
2. **Design** — Specify structure, invariants, and intended behavior.
3. **Implementation** — Realize the design in operable form.
4. **Verification** — Test claims against defined checks and gates.
5. **Reality** — Encounter the world as it actually behaves.
6. **Evidence** — Record what reality revealed, replayably and auditably.
7. **Understanding** — Revise beliefs in light of evidence.
8. **Improved Design** — Feed corrected understanding back into design.

The cycle does not end at Improved Design; it returns to Imagination and Design as systems evolve under stewardship.

### Axiom V — Systems must allow reality to correct them

Evidence is the constitutional mechanism through which reality informs understanding and improves design. No system may claim correctness without passing through this cycle.

## Article IV — Evidence Object Requirements

All evidence objects must include:

| Field | Meaning |
| --- | --- |
| `id` | Globally unique identifier |
| `type` | Profile type |
| `version` | Schema / record version |
| `authority` | CAR reference (carId, actorId, role) |
| `context` | Domain-specific metadata |
| `inputs` | Data, artifacts, advisory outputs |
| `verification` | Checks, gates, validations |
| `lineage` | Parent evidence, prior versions |
| `replay` | Deterministic reconstruction instructions |
| `audit` | Visibility and disclosure metadata |
| `promotion` | Decision, signature, timestamp |

## Article V — Profiles

CEF defines the following profiles:

| Profile | Domain |
| --- | --- |
| **CREC** | Research Evidence |
| **OEL** | Operational Evidence |
| **CEL** | Linguistic / Constitutional Evidence |
| **Security** | SBOM, supply chain, vulnerability, policy gates |
| **ModelEval** | Benchmarks, risk, uncertainty, lineage |

Each profile inherits CEF core invariants and extends the evidence object model with domain-specific fields.

## Article VI — Certification Engine

1. Promotion requires authority, verification, replay, audit, and signature.
2. Certificates are immutable once promoted.
3. Certificates enter stewardship upon promotion.

## Article VII — Stewardship

1. Evidence and certificates must be preserved.
2. Stewardship includes monitoring, renewal, revocation, replay, and audit.
3. Stewardship ensures continuity across versions and domains.

## Ratification

This Charter is the normative constitutional source for CEF v1.0. Companion specifications, schemas, workflows, and implementations MUST remain subordinate to Articles I–VII (including Article III-A).

**Related:** [Specification](./CEF_V1_SPECIFICATION.md) · [Index](./README.md)
