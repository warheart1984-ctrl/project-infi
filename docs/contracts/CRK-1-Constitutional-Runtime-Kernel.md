# CRK-1 — Constitutional Runtime Kernel v0.1

**Foundational Specification**

| Field | Value |
|-------|-------|
| Class | Foundational Constitutional Artifact |
| Version | v0.1 (frozen) |
| Status | Normative |
| Implementation | `src/continuity/constitutional_runtime.py` |
| Related | [CONSTITUTIONAL_RUNTIME_V0_1.md](CONSTITUTIONAL_RUNTIME_V0_1.md), [UGR-CRK-T1](UGR-CRK-T1-Constitutional-Sufficiency.md), [UGR-RTC-1](UGR_RTC_1_RUNTIME_CONTRACT.md), [UGR-OUT-1](UGR_OUT_1_OUTCOME_OBJECT.md) |

---

## 1. Introduction

### 1.1 Purpose

Define the minimal kernel for a governed runtime: the objects, contracts, and state transitions required for a system to maintain **identity**, **legitimacy**, **evidence integrity**, **resource realism**, and **continuity** across time.

The Constitutional Runtime Kernel (CRK) is the constitutional equivalent of a CPU instruction set. Everything else — CIT, MIT, EIT-2, explainability, replay, continuity, adaptation, drift, attention — is **runtime behavior** derivable from the kernel, not a first-class primitive.

### 1.2 Scope

Applies to any system that claims to be a **constitutional runtime**: a governed substrate where state changes are lawful, replayable, and epoch-gated.

### 1.3 Non-Goals

This specification does **not** define:

- UI, cockpit layout, or operator tooling
- Model internals, agent architectures, or inference pipelines
- Discovery Pods, reputation markets, or tenant identity overlays (these are operator-layer artifacts, not kernel objects)
- Implementation language, storage engine, or deployment topology

### 1.4 Kernel Invariance (CRK-1.6)

A system is a valid constitutional runtime **if and only if**:

1. All persisted state objects are instances of the five canonical types (§2).
2. All operations obey the four constitutional contracts (§3).
3. All state changes occur through canonical transitions (§4).
4. All higher-order systems (CIT, MIT, EIT-2, AIT, replay, explainability) are **derivable** from the kernel (§5).

This is the constitutional equivalent of **kernel space vs userland**.

---

## 2. Core Object Model

The kernel consists of exactly **five** first-class objects. No other first-class objects are permitted in the kernel.

### 2.1 IdentityObject

**Role:** Encodes who we are and what cannot change without high-ceremony governance.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable identity identifier (e.g. `CIV-CORE-01`) |
| `mission` | string | Non-negotiable purpose statement |
| `values` | string[] | Ordered value commitments |
| `invariants` | string[] | Hard constraints on lawful behavior |
| `authority_model` | object | Actor → permitted decision types |

**Schema:** In-memory dataclass in `constitutional_runtime.py` (`IdentityObject`).  
**Ledger:** Law ledger (`law_ledger.py`) holds constitutional amendments; identity itself is not deleted.

### 2.2 EvidenceObject

**Role:** Encodes what we know and why we believe it.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Evidence identifier (`evidence_id` in implementation) |
| `claim` | string | What is asserted (derived from lineage in EIT-1 records) |
| `type` | enum | observation, simulation, derivation, testimony, import |
| `source` | string | Source lineage reference |
| `provenance` | object | Hash chain, dependencies, trace links |
| `confidence` | number | Admissibility weight ∈ [0, 1] |
| `validation` | string | Method used to validate |
| `linked_decisions` | string[] | Decisions citing this evidence |
| `epoch` | integer | Epoch of creation |
| `status` | enum | valid, superseded, quarantined |
| `notes` | string | Optional operator annotation |

**Schema:** `fixtures/continuity/evidence_record.schema.json` (`EvidenceRecord`).  
**Ledger:** `evidence_ledger.py`.

### 2.3 DecisionObject

**Role:** Encodes what we intend to do and under what authority.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Decision identifier |
| `actor_id` | string | Approving or proposing actor |
| `identity_id` | string | Governing identity reference |
| `intent` | string | Human-readable intent |
| `type` | string | Decision class (constitutional-change, operational, …) |
| `evidence_refs` | string[] | Required evidence identifiers |
| `risk_profile` | object | Risk classification |
| `governance_basis` | object | Authority and process citation |
| `resource_plan` | object | Planned resource allocation |
| `status` | enum | proposed → approved → executing → executed \| rejected \| cancelled |
| `epoch` | integer | Epoch scope |
| `tags` | string[] | Index tags |
| `notes` | string | Optional annotation |
| `created_at` | string | ISO timestamp |
| `updated_at` | string | ISO timestamp |

**Schema:** `fixtures/continuity/decision_record.schema.json`.  
**Ledger:** `decision_ledger.py`.

### 2.4 ResourceObject

**Role:** Encodes what we can actually spend or move, including attention as a finite resource.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Resource identifier |
| `type` | string | time, money, people, infra, attention, other |
| `quantity` | object | `{ total, allocated, unit }` |
| `constraints` | object[] | Hard/soft limits |
| `allocations` | object[] | Active allocations by decision |
| `epoch` | integer | Epoch scope |
| `status` | enum | active, exhausted, frozen, retired |

**Schema:** `fixtures/continuity/resource_record.schema.json`.  
**Ledger:** `resource_ledger.py`.  
**Contract:** `resource_contract.py` — RC-1 through RC-4 (non-oversubscription, status semantics, attention parity, decision linkage).

### 2.5 OutcomeObject

**Role:** Encodes what reality did in response to a decision.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Outcome identifier |
| `decision_id` | string | Parent decision (required) |
| `expected` | object | Predicted metrics |
| `observed` | object | Measured metrics |
| `variance` | object | Computed delta and classification |
| `lessons` | string[] | Integratable feedback |
| `epoch` | integer | Epoch scope |
| `timestamp` | string | ISO timestamp |
| `status` | enum | recorded, disputed, superseded |

**Schema:** `fixtures/continuity/outcome_record.schema.json`.  
**Ledger:** `outcome_ledger.py`.

---

## 3. Constitutional Contracts

Each object is governed by a corresponding contract. Contracts define **instruction semantics** — preconditions, postconditions, and rejection rules.

### 3.1 Evidence Contract

**Guarantees:**

- Evidence has recoverable provenance (**EIT-1**).
- Evidence lineages converge across operators and time (**EIT-2**).

**Preconditions for use in decisions:**

- `status = valid` (or equivalent admissible state).
- `confidence ≥` configured threshold.
- No higher-confidence contradictory evidence without explicit override.

**Implementation:** `EvidenceContract` in `constitutional_runtime.py`.

### 3.2 Governance Contract

**Guarantees:**

- Only authorized actors can approve decisions.
- Decisions do not violate `IdentityObject.invariants`.
- Decisions follow lifecycle: **proposed → approved → executed** or **rejected / cancelled**.

**Implementation:** `GovernanceContract` in `constitutional_runtime.py`.

### 3.3 Resource Contract

**Guarantees:**

- Resources are not oversubscribed.
- Attention is treated as a finite resource.
- Allocations respect constraints and priorities.
- Every allocation references a valid DecisionObject (RC-4).

**Implementation:** `ResourceContract` in `resource_contract.py`; `ResourceLedgerStore` in `resource_ledger.py`.

### 3.4 Runtime Contract

**Guarantees:**

- All state transitions are explicit and replayable.
- Epoch advancement is gated by **spine health**.
- Ledgers remain internally consistent.

**Spine health** aggregates **derivable fitness projections** (CIT, MIT, EIT-2, SIT, GIT, PIT, outcome drift). Block tokens: `CIT-BLOCK`, `MIT-BLOCK`, `EIT-BLOCK`, `SIT-BLOCK`, `GIT-BLOCK`, `PIT-BLOCK`, `OIT-BLOCK`.

**Implementation:** `RuntimeContract` in `constitutional_runtime.py`; `build_spine_health()` in `evidence_fitness.py`.

---

## 4. Canonical State Transitions

State changes occur only through these transitions. Each transition MUST define preconditions, postconditions, and ledger effects.

### 4.1 IdentityObject

| Transition | Gate | Effect |
|------------|------|--------|
| `InitializeIdentity` | Bootstrap | Create canonical identity |
| `AmendIdentity` | Governance (high ceremony) | Append amendment; invariants preserved |

### 4.2 EvidenceObject

| Transition | Gate | Effect |
|------------|------|--------|
| `CreateEvidence` | Provenance present | Append evidence record |
| `ValidateEvidence` | Validation method | Set confidence, status |
| `ConvergeLineage` | EIT-2 replay | Record convergence proof |
| `SupersedeEvidence` | Higher-confidence successor | Mark prior superseded |

### 4.3 DecisionObject

| Transition | Gate | Effect |
|------------|------|--------|
| `ProposeDecision` | Governance invariants | `status = proposed` |
| `ApproveDecision` | Governance + Evidence contracts | `status = approved` |
| `AllocateResources` | Resource contract | Bind resource plan |
| `ExecuteDecision` | Runtime ready + resources | Execute; require outcome |
| `RejectDecision` / `CancelDecision` | Authority | Terminal status |

**Kernel mapping:** `propose_decision`, `approve_decision`, `execute_decision` on `ConstitutionalRuntime`.

### 4.4 ResourceObject

| Transition | Gate | Effect |
|------------|------|--------|
| `AllocateResource` | Resource contract | Decrement available; record allocation |
| `ReleaseResource` | Valid allocation | Return capacity |
| `UpdateResource` | Governance | Adjust constraints or caps |

### 4.5 OutcomeObject

| Transition | Gate | Effect |
|------------|------|--------|
| `RecordOutcome` | Valid executed decision | Immutable expected/observed |
| `AnalyzeVariance` | Outcome recorded | Compute variance classification |
| `IntegrateOutcome` | Variance analyzed | Feed spine / lessons |

**Kernel mapping:** `execute_decision` records outcome via `OutcomeLedgerStore.record()`.

### 4.6 Epoch

| Transition | Gate | Effect |
|------------|------|--------|
| `AdvanceEpoch` | Runtime contract: spine health OK | `epoch += 1`; snapshot fitness |

**Kernel mapping:** `advance_epoch()` on `ConstitutionalRuntime`.

---

## 5. Derivable Systems

The following systems **MUST NOT** exist as first-class kernel primitives:

| System | Derivation |
|--------|------------|
| **CIT** (Comprehension Invariance) | Projection over EvidenceObject + comprehension ledger under Evidence Contract |
| **MIT** (Meaning Invariance) | Projection over EvidenceObject + meaning ledger |
| **EIT-2** (Evidence Lineage Convergence) | Evidence Contract convergence checks + `build_spine_health` EIT strip |
| **Explainability** | Trace links on EvidenceObject + decision/outcome replay |
| **Replay** | Ledger reconstruction from canonical transitions |
| **Continuity** | Epoch + ledger append-only semantics |
| **Adaptation** | Outcome integration + governance-gated identity amendments |
| **Drift** | Variance analysis on OutcomeObject + fitness thresholds |
| **Attention (AIT)** | ResourceObject subtype under Resource Contract |

**Rule:** No new first-class objects may be added to the kernel. New capability MUST be expressed as contract refinement, transition constraint, or userland projection.

---

## 6. Reference Implementation (v0.1)

Minimal skeleton (Python). Full implementation: `src/continuity/constitutional_runtime.py`.

```python
class ConstitutionalLedgers:
    identity: IdentityObject
    evidence_store: EvidenceLedgerStore
    decisions: DecisionLedgerStore
    resources: ResourceLedgerStore
    outcomes: OutcomeLedgerStore
    epoch: int


class ConstitutionalRuntime:
    def propose_decision(self, draft: DecisionRecord) -> DecisionRecord: ...
    def approve_decision(self, decision_id: str) -> DecisionRecord: ...
    def execute_decision(
        self, decision_id, *, expected, observed, lessons=None
    ) -> OutcomeRecord: ...
    def advance_epoch(self) -> dict: ...
```

**Kernel loop:**

```
Identity → Evidence → Decision → Resource → Outcome → Epoch → fitness projections
```

Everything else (cockpit strips, agents, discovery pods) lives in **userland**.

---

## 7. Conformance and Testing

Property-based conformance tests live in `tests/crk1/`:

| Suite | Validates |
|-------|-----------|
| `test_crk1_objects.py` | Object invariants (§2) |
| `test_crk1_contracts.py` | Contract rejection rules (§3) |
| `test_crk1_transitions.py` | Transition pre/postconditions (§4) |
| `test_k0_consequence_transmission.py` | K0 — execution→outcome→replay→evidence |
| `test_k1_immutable_exposure.py` | K1 — no outcome drop, quarantine, or replay bypass |
| `test_k2_judgment_consequence_coupling.py` | K2 — identity/evidence coupling + lineage |
| `test_k3_anti_insulation.py` | K3 — anti-insulation / lineage escape |
| `test_insulation_attack_suite.py` | Unified continuity health check (all attacks must fail) |

A runtime passes CRK-1 conformance when all suites pass against its reference implementation.

### 7.1 K0–K3 JSON Schema Constraints

Wire-level consequence transmission objects are defined in `fixtures/crk1/`:

| Schema | File | Encodes |
|--------|------|---------|
| `OutcomeObject` | `outcome_object.schema.json` | `replayable: true` (const), `decision_id` required |
| `EvidenceObject` | `evidence_object.schema.json` | `admissible_for_decision: true` (const), outcome link |
| `DecisionObject` | `decision_object.schema.json` | `identity_id`, `input_evidence_ids.minItems: 1` |
| `IdentityObject` | `identity_object.schema.json` | `parent_identity_id` for lineage (K2/K3) |

Validated by `src/crk1/schema_validator.py` (`CRK1SchemaValidator`).

### 7.2 Runtime Invariants (K0–K3)

Implemented in `src/crk1/runtime_facade.py` and `src/crk1/runtime_validator.py`:

| Law | Runtime check |
|-----|----------------|
| **K0** | `execute_decision` must produce outcome; `replay_outcome` yields admissible evidence |
| **K1** | `delete_outcome`, `mark_evidence_non_admissible` raise `ConstitutionalError` |
| **K2** | Decisions require evidence; `get_admissible_evidence` exposes lineage-bound replay evidence |
| **K3** | `mark_evidence_irrelevant_for_identity` forbidden; `proveAntiInsulation` in TS twin |

Full spec: `docs/crk1/CRK1_CONSEQUENCE_TRANSMISSION_LATTICE.md`, `continuity-engine/docs/CRK-1-WHITEPAPER-CONSEQUENCE-KERNEL.md`.

---

## 8. CRK-1 → CRK-2 Evolution Path

CRK-2 **must not** add first-class objects. It deepens semantics only.

| Track | Focus |
|-------|-------|
| **ID-2** | Formal amendment protocol for IdentityObject |
| **ID-3** | Multi-identity support (orgs, teams, projects) |
| **RT-2** | Federated kernels; consensus on decisions and evidence |
| **TIME-1** | Temporal semantics: backdating, delayed outcomes |
| **AIT-2** | Attention as kernel-level Resource Contract; canonical A(X) |

**CRK-2 invariants:**

- No new first-class objects.
- No breaking changes to CRK-1 object schemas.
- All new behavior expressible as new contracts, refined semantics, or additional transition constraints.

---

## Appendix A — Block Reason Tokens

| Token | Derivable layer | Meaning |
|-------|-----------------|---------|
| `CIT-BLOCK` | Comprehension fitness | Comprehension invariance failed |
| `MIT-BLOCK` | Meaning fitness | Meaning invariance failed |
| `EIT-BLOCK` | Evidence fitness | Evidence convergence / Omega threshold failed |
| `SIT-BLOCK` | Stewardship fitness | Stewardship invariance failed |
| `GIT-BLOCK` | Governance fitness | Governance integrity failed |
| `PIT-BLOCK` | Persistence fitness | Persistence reality check failed |
| `OIT-BLOCK` | Outcome drift | Outcome variance exceeds threshold |

These are **runtime projections**, not kernel objects.

---

## 9. CRK-T1 — Constitutional Sufficiency (Kernel Theorem)

**UGR-CRK-T1** states that if the five objects and four contracts exist with replayable transitions, the constitutional stack is **functionally complete** for governance. SIT, GIT, PIT, EIT, CIT, MIT, AIT, explainability, replay, continuity, and adaptation are **derivable** — not kernel primitives.

Full theorem: [UGR-CRK-T1-Constitutional-Sufficiency.md](UGR-CRK-T1-Constitutional-Sufficiency.md).

### 9.1 Sufficiency test (normative)

For any new proposal:

> Can it be expressed purely in terms of the five objects + four contracts + transitions?

| Answer | Placement |
|--------|-----------|
| Yes | Userland — fitness functional, projection, policy, cockpit panel |
| No | Kernel amendment (CRK-2+) |

### 9.2 Kernel vs userland

```
                ┌──────────────────────────────────────────┐
                │        CONSTITUTIONAL KERNEL (CRK-1)      │
                ├──────────────────────────────────────────┤
                │  Five Objects · Four Contracts            │
                │  Canonical Transitions · Replay           │
                └──────────────────────────────────────────┘
                                ▲
                                │  CRK-T1: Sufficiency
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                     CONSTITUTIONAL APPLICATION SPACE (USERLAND)            │
├────────────────────────────────────────────────────────────────────────────┤
│  Fitness: SIT, GIT, PIT, EIT, CIT, MIT, AIT                               │
│  Cockpit: Comprehension/Meaning/Evidence Fitness, Outcome Variance         │
│  Dashboards, agents, policies, discovery pods                            │
└────────────────────────────────────────────────────────────────────────────┘
```

Operator cockpit labeling follows this boundary — see `docs/operator/cockpit/README.md`.

**CRK-T2 (proposed):** [UGR-CRK-T2 — Constitutional Boundary Detection](UGR-CRK-T2-Constitutional-Boundary-Detection.md) — outer-loop control that detects kernel insufficiency and gates CRK-2+ amendments. Implementation: `src/continuity/crk2_boundary_control.py`.

---

## Appendix B — Document History

| Version | Date | Change |
|---------|------|--------|
| v0.1 | 2026-06 | Initial freeze; ResourceContract implemented; CRK-T1 adopted |
