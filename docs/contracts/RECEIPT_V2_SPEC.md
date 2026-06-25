# Receipt v2 — Unified Specification (Six‑Dimension Runtime Contract)

**Class:** Constitutional Contract (Article XIII — Universal Runtime Contract)

## Overview

Receipt v2 is the canonical audit artifact for all governed runtimes in the unified architecture.

Every governed action **MUST** emit one or more Receipt v2 objects. Each receipt declares the **Six‑Dimension Runtime Contract**:

| Dimension | Question |
|-----------|----------|
| **Invariant** | What invariant does this runtime protect? |
| **Evidence** | What evidence does it use? |
| **Authority** | What authority permits the action? |
| **Reproducibility** | Can an independent observer reproduce the result? |
| **Impact Boundary** | What impact boundary does it operate within? |
| **Accountability** | Who is accountable for the outcome? |

An action lacking one or more dimensions is **constitutionally incomplete** and MUST be treated as invalid or provisional.

**Implementations:**

- Python: `operator_kernel/receipts_v2.py`
- TypeScript: `aaes-os/packages/governed-memory/src/receipts_v2.ts`

**Related:** Article XIV — Remediation Lifecycle (below); Article XV — [Constitutional State Runtime](./CONSTITUTIONAL_STATE_RUNTIME.md)

---

## BaseReceiptV2

All receipts inherit the following structure.

```yaml
receipt_id: string
runtime: string                    # e.g. constitutional, continuity, truth, sovereignty, institutional, reality, controltower, cognitive, arbitration, reproduction, operator
timestamp: RFC3339
action_type: string                # e.g. claim_verification, authority_grant, event_record, decision_execution, tool_governance

inputs:
  request_id: string
  payload_hash: string
  context:
    mission_id: string?
    task_id: string?
    observer_id: string?

outputs:
  status: string                   # approved, rejected, executed, failed, diverged, allow, deny, revise
  result_hash: string
  notes: string?

invariant:
  name: string
  description: string
  satisfied: boolean

evidence:
  bundle_id: string
  sources:
    - id: string
      type: string                 # document, api, database, measurement, testimony, model_output
      provenance: string
  modalities: [string]
  chain_of_custody:
    - holder: string
      timestamp: RFC3339
      action: string               # collected, transformed, validated, transferred
  sufficiency:
    continuity: boolean
    truth: boolean
    sovereignty: boolean
    institutional: boolean

authority:
  source: string
  jurisdiction: string
  delegation_chain:
    - from: string
      to: string
      scope: string
      timestamp: RFC3339
  consent:
    granted_by: string?
    timestamp: RFC3339?
    terms: string?
  legitimacy_basis: string         # constitutional article, policy id, treaty id

reproducibility:
  is_reproducible: boolean
  mode: exact | structural | approximate | non_reproducible
  constraints: string?
  reproduction_reference_id: string?

impact_boundary:
  scope_in: [string]
  scope_out: [string]
  notes: string?

accountability:
  primary_accountable_party: string
  accountability_chain:
    - role: string
      party_id: string
      responsibility_scope: string
      escalation_path: string?

signatures:
  runtime_signature: string
  observer_signature: string?

continuity:
  previous_receipt_id: string?
  thread_id: string?
  lineage_hash: string

lifecycle:                           # Article XIV — added to all governed receipts
  stage: decision | observation | divergence | remediation | closure
  previous_stage_receipt_id: string?
  next_stage_expected: string?
```

### Required fields (minimum)

Every Receipt v2 MUST include:

- `receipt_id`
- `runtime`
- `timestamp`
- `action_type`
- `inputs`
- `outputs`
- `invariant`
- `evidence.bundle_id` and `evidence.sufficiency`
- `authority.source` and `authority.legitimacy_basis`
- `reproducibility.is_reproducible` and `reproducibility.mode`
- `impact_boundary.scope_in` and `impact_boundary.scope_out`
- `accountability.primary_accountable_party`
- `continuity.lineage_hash`
- `lifecycle.stage`

---

## Runtime‑Specific Extensions

Each runtime extends `BaseReceiptV2` with domain-specific fields only.

### TruthReceiptV2

```yaml
claim:
  claim_id: string
  claim_type: factual | procedural | authority | continuity | reality
  statement: string

verification:
  method: string
  confidence: number
  evidence_used: [string]
  contradictions: [string]?
```

**Purpose:** Captures how a claim was evaluated, what evidence was used, and why the truth runtime accepted or rejected it.

### SovereigntyReceiptV2

```yaml
delegation:
  granted_by: string
  granted_to: string
  scope: string
  jurisdiction: string
  terms: string?

legitimacy:
  basis: string
  validated: boolean
  conflicts: [string]?
```

**Purpose:** Records authority decisions, delegation chains, and legitimacy checks.

### ReproductionReceiptV2

```yaml
reproduction:
  reference_receipt_id: string
  divergence:
    diverged: boolean
    divergence_points: [string]?
    structural_match: boolean
    output_match: boolean
```

**Purpose:** Captures whether a run was reproducible, where it diverged, and why.

### ContinuityReceiptV2

```yaml
event:
  event_id: string
  event_type: string
  timestamp_observed: string

lineage:
  chain_of_custody: [string]
  continuity_satisfied: boolean
```

### InstitutionalReceiptV2

```yaml
procedure:
  procedure_id: string
  version: string
  steps_followed: [string]
  deviations: [string]?

compliance:
  compliant: boolean
  violations: [string]?
```

### ArbitrationReceiptV2

```yaml
conflict:
  runtimes_in_conflict: [string]
  conflict_type: string
  evidence_presented: [string]

resolution:
  winning_runtime: string
  rationale: string
  precedence_rule: string
```

---

## Article XIV — Remediation Lifecycle

**Class:** Constitutional Obligation (attached to Accountability)

The Remediation Lifecycle is not a separate runtime. It is an obligation bound to accountability and enforced through the **Institutional Runtime** and **Constitutional Runtime**.

### Lifecycle stages

Every governed decision may pass through up to five remediation stages. Each stage emits its own Receipt v2 subtype.

| Stage | Receipt type | Purpose |
|-------|--------------|---------|
| 1 | **Decision** | Original governed action (Six Dimensions) |
| 2 | **Observation** | What actually occurred in reality |
| 3 | **Divergence** | Observed reality contradicts expected outcome |
| 4 | **Remediation** | Corrective action, restitution, escalation |
| 5 | **Closure** | Remediation satisfied; lineage terminal |

### Lifecycle field (on BaseReceiptV2)

```yaml
lifecycle:
  stage: decision | observation | divergence | remediation | closure
  previous_stage_receipt_id: string?
  next_stage_expected: string?
```

### Lifecycle receipt types

#### DecisionReceiptV2

```yaml
lifecycle:
  stage: decision
  previous_stage_receipt_id: null
  next_stage_expected: observation
```

#### ObservationReceiptV2

```yaml
lifecycle:
  stage: observation
  previous_stage_receipt_id: "<decision_receipt_id>"
  next_stage_expected: divergence_or_closure

observation:
  observed_status: string
  observed_at: RFC3339
  observer_jurisdiction: string
  notes: string?
```

#### DivergenceReceiptV2

```yaml
lifecycle:
  stage: divergence
  previous_stage_receipt_id: "<observation_receipt_id>"
  next_stage_expected: remediation

divergence:
  nature: string
  magnitude: string
  evidence_receipt_ids: [string]
  expected_outcome_hash: string?
  observed_outcome_hash: string?
```

#### RemediationReceiptV2

```yaml
lifecycle:
  stage: remediation
  previous_stage_receipt_id: "<divergence_receipt_id>"
  next_stage_expected: closure

remediation:
  required_actions: [string]
  responsible_party: string
  restitution: string?
  escalation_path: string?
  constitutional_trigger: false
  deadline: RFC3339?
```

#### ClosureReceiptV2

```yaml
lifecycle:
  stage: closure
  previous_stage_receipt_id: "<remediation_receipt_id>"
  next_stage_expected: null

closure:
  remediation_completed: true
  restitution_delivered: boolean
  institutional_review_performed: boolean
  reviewing_body: string
  constitutional_amendment_id: string?
```

### Transition rules

| Rule | Transition | Requirement |
|------|------------|-------------|
| 1 | Decision → Observation | Every Decision Receipt MUST eventually be followed by Observation |
| 2 | Observation → Divergence or Closure | Match → Closure; mismatch → Divergence |
| 3 | Divergence → Remediation | Divergence triggers remediation unless Institutional Runtime waives |
| 4 | Remediation → Closure | Remediation MUST produce Closure |
| 5 | Closure is terminal | No further receipts for the same decision lineage |

### Constitutional obligations

- **Recognition** — Any runtime detecting divergence MUST issue a Divergence Receipt
- **Assignment** — Accountability determines who remediates; authority ≠ accountability
- **Governance** — Remediation procedures governed by Institutional Runtime; amendments by Constitutional Runtime
- **Traceability** — All remediation actions linked through `continuity.lineage_hash`
- **Closure** — No remediation complete without a Closure Receipt

### Constitutional amendment escalation

If remediation reveals a broken invariant, insufficient authority model, invalid impact boundary, or systemic failure:

1. Constitutional Runtime issues Remediation Receipt with `constitutional_trigger: true`
2. Amendment procedures initiated
3. Closure Receipt issued only after amendment ratified (`constitutional_amendment_id` set)

### Observer rights

Observers MUST be able to inspect remediation receipts, verify accountability chains, confirm restitution and closure, and challenge insufficient remediation.

---

## Article XV — TransitionReceiptV2

Every **legal constitutional state change** emits `TransitionReceiptV2` (see [CONSTITUTIONAL_STATE_RUNTIME.md](./CONSTITUTIONAL_STATE_RUNTIME.md)):

```yaml
action_type: state_transition

transition:
  from_state: string
  to_state: string
  legal_basis: string
  receipt_ids_used: [string]
  state_id: string?
  state_type: string?
```

---

## Article XVI — Constitutional Amendment Process

Amendments follow a six-stage lifecycle with typed receipts. See [CONSTITUTIONAL_AMENDMENT_PROCESS.md](./CONSTITUTIONAL_AMENDMENT_PROCESS.md).

```yaml
action_type: constitutional_amendment

amendment:
  article: string
  change_type: addition | modification | removal
  justification: string
  trigger_receipt_id: string
  amendment_stage: proposed | evaluated | ratified | implemented | observed | closed
  immutable_override: boolean?
  unanimous_sovereign_ratification: boolean?
```

Stage receipts: `AmendmentProposalReceiptV2` through `AmendmentClosureReceiptV2`.

**Immutable core:** Articles XIII, XIV, XV, XVI, and SEVEN_INVARIANTS require `immutable_override` and `unanimous_sovereign_ratification` for modification/removal.

**Implementation:** `operator_kernel/amendments.py`

---

## Constitutional Transition Ledger

All transitions are recorded in an append-only ledger. See [CONSTITUTIONAL_TRANSITION_LEDGER.md](./CONSTITUTIONAL_TRANSITION_LEDGER.md).

**Implementation:** `operator_kernel/transition_ledger.py`

---

## Observer Verification

Independent observers verify receipts, state, ledger, remediation, and amendments. See [OBSERVER_VERIFICATION_HANDBOOK.md](./OBSERVER_VERIFICATION_HANDBOOK.md).

Observer receipt types:

- `ObserverVerificationReceiptV2`
- `ObserverDivergenceReceiptV2`
- `ObserverRemediationRequestReceiptV2`
- `ObserverClosureReceiptV2`

**Implementation:** `operator_kernel/observer_verification.py`

---

## Unified Runtime Specification Template

Every runtime MUST be documented using the twelve-section template in [RUNTIME_SPECIFICATION_TEMPLATE.md](./RUNTIME_SPECIFICATION_TEMPLATE.md).

---

## Constitutional alignment

- **Article XIII** — Universal Runtime Contract (Six Dimensions)
- **Article XIV** — Remediation Lifecycle
- **Article XV** — Constitutional State Runtime ([CONSTITUTIONAL_STATE_RUNTIME.md](./CONSTITUTIONAL_STATE_RUNTIME.md))
- **Article XVI** — Constitutional Amendment Process ([CONSTITUTIONAL_AMENDMENT_PROCESS.md](./CONSTITUTIONAL_AMENDMENT_PROCESS.md))
- **UGR-RTC-1** — Runtime admissibility gate
- **Operator v1** — `law_receipt` events SHOULD upgrade to Receipt v2 at emission boundaries
- **Mission verification** — Sovereignty, Truth, Continuity, Institutional, Arbitration, and Reproduction runtimes emit specialized Receipt v2 variants

---

## Validation

Machine-readable validation:

```python
from operator_kernel.receipts_v2 import (
    BaseReceiptV2,
    DecisionReceiptV2,
    ObservationReceiptV2,
    DivergenceReceiptV2,
    RemediationReceiptV2,
    ClosureReceiptV2,
    is_receipt_v2_complete,
    validate_lifecycle_transition,
)

receipt = BaseReceiptV2.model_validate(payload)
assert is_receipt_v2_complete(receipt)
```

Incomplete receipts MUST NOT advance epoch state or execute irreversible side effects without explicit provisional handling.
