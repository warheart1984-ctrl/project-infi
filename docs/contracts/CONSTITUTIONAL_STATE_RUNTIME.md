# Constitutional State Runtime — Article XV

**Class:** Constitutional Contract (Article XV — Shared Substrate of Governed State)

## Purpose

The Constitutional State Runtime defines the **durable constitutional state** of the system and the **legal transitions** that modify it.

It is not a domain runtime. It is the substrate that all runtimes write to and read from.

Responsibilities:

- Define constitutional state objects
- Define legal transitions between states
- Validate transitions against constitutional law
- Emit transition receipts (`TransitionReceiptV2`)
- Maintain continuity lineage
- Enable full state reconstruction and independent replay

Every state change is lawful, receipted, remediable, reconstructable, and independently verifiable.

**Implementations:**

- **Drop-in core:** `constitutional_state/` (`models.py`, `graph.py`, `ledger.py`, `runtime.py`, `amendment.py`, `observer.py`)
- **Receipt v2 + Operator:** `constitutional_substrate/` (extends core with `TransitionReceiptV2`, persistence, task wiring)
- **Operator shims:** `operator_kernel/csr.py`, `operator_kernel/constitutional_task.py`
- TypeScript: `aaes-os/packages/governed-memory/src/constitutional_state.ts`
- **12 runtime catalog:** [GOVERNED_RUNTIME_CATALOG.md](./GOVERNED_RUNTIME_CATALOG.md)

---

## State objects

Every governed entity is a **State Object**:

| Type | Domain |
|------|--------|
| `ClaimState` | Truth claims |
| `AuthorityState` | Sovereignty grants |
| `InstitutionState` | Institutional procedures |
| `DecisionState` | Governed decisions |
| `ContinuityState` | Event lineage |
| `SovereigntyState` | Delegation / jurisdiction |
| `RealityState` | Observed outcomes |
| `DomainState` | DAR-Z, Legal, Tribal, Simulation, Civilization |

Each State Object MUST declare: purpose, invariants, legal transitions, failure modes, receipts, accountability chain.

### Universal State Object schema

```yaml
state_id: string
state_type: string
version: integer
current_state: string

invariants: [string]
evidence_requirements: [string]
authority_model: [string]
reproducibility_requirements: [string]
impact_boundaries: [string]
accountability_chain: [string]

history:
  - transition_id: string
    from_state: string
    to_state: string
    receipt_id: string
    timestamp: RFC3339
    legal_basis: string?
    receipt_ids_used: [string]?
```

---

## Events, receipts, transitions, state

| Concept | Role |
|---------|------|
| **Events** | Raw occurrences |
| **Receipts** | Governed evidence of events (Receipt v2) |
| **Transitions** | Legal state changes |
| **State** | Durable constitutional truth |

**Receipts do not define state.** Receipts justify transitions that modify state.

---

## Universal legal transition graph

```
Proposed
  ↓
Evaluated
  ↓
Approved
  ↓
Executed
  ↓
Observed
  ↓
Challenged ──→ Closed (direct from Observed when no challenge)
  ↓
Arbitrated
  ↓
Remediated
  ↓
Closed
```

### Domain mappings (examples)

| Runtime | Domain labels → Universal graph |
|---------|--------------------------------|
| Truth | Supported→Evaluated, Verified→Approved, Diverged→Challenged |
| Sovereignty | Requested→Proposed, Delegated→Approved, Active→Executed |
| Institutional | Draft→Proposed, Audited→Challenged, Amended→Remediated |
| Continuity | EventRecorded→Executed |
| Reproduction | Reproduced→Executed, Diverged→Challenged |

Each transition MUST:

- Be legal under the Constitution
- Be justified by a Receipt v2
- Update the State Object and continuity lineage
- Be reproducible and accountable

---

## TransitionReceiptV2

Every legal transition MUST emit `TransitionReceiptV2` (extends Receipt v2):

```yaml
transition:
  from_state: string
  to_state: string
  legal_basis: string
  receipt_ids_used: [string]
  state_id: string?
  state_type: string?
```

`action_type` MUST be `state_transition`.

See also: [RECEIPT_V2_SPEC.md](./RECEIPT_V2_SPEC.md) (Article XIII–XIV).

---

## State reconstruction (§6)

Given an ordered sequence of `TransitionReceiptV2`:

1. Validate receipt integrity (`is_receipt_v2_complete`)
2. Validate legal transition (`validate_transition`)
3. Apply transition to State Object
4. Append to `history`

```python
from operator_kernel.constitutional_state import StateObject, reconstruct_state

final = reconstruct_state(receipts, state_obj)
```

`reconstruct_state_at(receipts, state_obj, at_index=n)` returns state at historical point *n*.

---

## State replay (§7)

Given the same receipts, an observer MUST reproduce the same final state:

```python
from operator_kernel.constitutional_state import replay_state

result = replay_state(receipts, canonical_state)
assert not result.diverged
```

On divergence, emit `ReproductionReceiptV2` per Article XIII.

---

## Constitutional alignment

- **Article XIII** — Six-Dimension Runtime Contract
- **Article XIV** — Remediation Lifecycle
- **Article XV** — Constitutional State Runtime (this document)
- **UGR-RTC-1** — Transition admissibility gate

Incomplete or illegal transitions MUST NOT modify durable constitutional state.
