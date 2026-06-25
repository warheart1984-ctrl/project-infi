# Article XVI — Constitutional Amendment Process

**Class:** Constitutional Contract

## Purpose

The Constitutional Amendment Process defines how the Constitution may be changed, extended, corrected, or repaired. It ensures amendments are:

- lawful
- receipted
- reproducible
- accountable
- governed by a fixed lifecycle
- never made silently or implicitly

## Amendment Triggers

An amendment may be triggered only by a typed receipt:

| Trigger | Condition |
|---------|-----------|
| Remediation Receipt | `constitutional_trigger = true` |
| Arbitration Receipt | constitutional conflict identified |
| Continuity Receipt | structural break (`continuity_satisfied = false`) |
| Sovereignty Receipt | illegitimate authority (`validated = false`) |
| Truth Receipt | invariant cannot be satisfied |
| Institutional Receipt | procedural contradiction |
| Observer Petition | `action_type = observer_petition` with sufficient evidence |
| Foundational Invariant Violation | `action_type = foundational_invariant_violation` |

No amendment may occur without a triggering receipt.

## Amendment Lifecycle

```
Proposed → Evaluated → Ratified → Implemented → Observed → Closed
```

Each stage emits a typed `AmendmentReceiptV2` specialization:

| Stage | Receipt type |
|-------|----------------|
| Proposed | `AmendmentProposalReceiptV2` |
| Evaluated | `AmendmentEvaluationReceiptV2` |
| Ratified | `AmendmentRatificationReceiptV2` |
| Implemented | `AmendmentImplementationReceiptV2` |
| Observed | `AmendmentObservationReceiptV2` |
| Closed | `AmendmentClosureReceiptV2` |

### Amendment payload

```json
{
  "amendment": {
    "article": "string",
    "change_type": "addition | modification | removal",
    "justification": "string",
    "trigger_receipt_id": "string",
    "amendment_stage": "proposed | evaluated | ratified | implemented | observed | closed",
    "immutable_override": false,
    "unanimous_sovereign_ratification": false
  }
}
```

## Immutable Core

Articles `XIII`, `XIV`, `XV`, `XVI`, and `SEVEN_INVARIANTS` are immutable core. Modification or removal requires:

- `immutable_override: true`
- `unanimous_sovereign_ratification: true`

Additions to immutable articles remain permitted without override.

## Amendment Replay

Any observer must be able to replay the amendment sequence and verify legality, authority, evidence, accountability, and reproducibility. If replay diverges from canonical state, the amendment is invalid.

**Implementation:** `operator_kernel/amendments.py`

```python
from operator_kernel.amendments import process_amendment_receipts, replay_amendment
from operator_kernel.receipts_v2 import is_amendment_trigger_receipt
```

**Related:**

- [Constitutional Transition Ledger](./CONSTITUTIONAL_TRANSITION_LEDGER.md)
- [Observer Verification Handbook](./OBSERVER_VERIFICATION_HANDBOOK.md)
- [Runtime Specification Template](./RUNTIME_SPECIFICATION_TEMPLATE.md)
