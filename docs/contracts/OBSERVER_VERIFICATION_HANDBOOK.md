# Observer Verification Handbook

Operational procedure for independent observers to verify the entire governed system.

## Observer Rights

Observers have the right to:

- inspect all receipts
- inspect all state objects
- inspect the transition ledger
- replay all transitions
- challenge any decision
- request arbitration
- request remediation
- verify closure
- verify amendments

## Verification Procedure

### Step 1 — Collect Receipts

Gather all Receipt v2 objects relevant to the object or decision under review.

### Step 2 — Validate Six-Dimension Contract

For each receipt, verify:

| Dimension | Check |
|-----------|-------|
| Invariant | Named and satisfied or explicitly failed |
| Evidence | Bundle present with sufficiency flags |
| Authority | Source and legitimacy basis declared |
| Reproducibility | Mode and reproducibility flag set |
| Impact Boundary | scope_in and scope_out non-empty |
| Accountability | primary_accountable_party set |

Use `is_receipt_v2_complete(receipt)` for machine validation.

### Step 3 — Validate Transition Legality

Confirm each transition is allowed by the Constitutional Transition Graph (Article XV).

### Step 4 — Reconstruct State

Use the Constitutional State Runtime to rebuild state from transition receipts.

### Step 5 — Replay State

Replay transitions and compare to canonical state. Divergence invalidates the lineage.

### Step 6 — Check Remediation Lifecycle

If any failure occurred, verify:

- divergence receipt issued
- arbitration (if required)
- remediation receipt with accountable party
- closure receipt

### Step 7 — Check Amendment Path

If constitutional triggers occurred, verify full amendment lifecycle through closure.

### Step 8 — Issue Observer Receipt

On success, emit `ObserverVerificationReceiptV2` and `ObserverClosureReceiptV2`.

On failure, emit `ObserverDivergenceReceiptV2` and `ObserverRemediationRequestReceiptV2`.

## Observer Verification Receipt

```json
{
  "receipt_id": "string",
  "runtime": "observer",
  "timestamp": "string",
  "action_type": "observer_verification",
  "verification": {
    "state_reconstructed": true,
    "state_replayed": true,
    "divergence_detected": false,
    "remediation_valid": true,
    "amendments_valid": true,
    "target_id": "string"
  },
  "observer_accountability": {
    "responsible_parties": ["string"]
  }
}
```

## Implementation

```python
from operator_kernel.observer_verification import (
    ObserverVerificationContext,
    run_observer_verification,
)

report = run_observer_verification(
    ObserverVerificationContext(
        target_id="claim-001",
        receipts=[...],
        transition_receipts=[...],
        canonical_state=state,
        ledger=ledger,
    )
)
```

**TypeScript:** `aaes-os/packages/governed-memory/src/observer_verification.ts`

**Related:**

- [Article XVI — Constitutional Amendment Process](./CONSTITUTIONAL_AMENDMENT_PROCESS.md)
- [Constitutional Transition Ledger](./CONSTITUTIONAL_TRANSITION_LEDGER.md)
- [Receipt v2 Specification](./RECEIPT_V2_SPEC.md)
