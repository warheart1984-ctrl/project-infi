# Constitutional Transition Ledger

The Constitutional Transition Ledger is the durable, canonical record of all state transitions in the governed system.

## Contents

The ledger records:

- all state transitions
- all transition receipts
- all lineage links
- all remediation paths
- all closures

It is the constitutional truth of system evolution.

## Ledger Entry Structure

```json
{
  "transition_id": "string",
  "state_object_id": "string",
  "from_state": "string",
  "to_state": "string",
  "receipt_id": "string",
  "timestamp": "string",
  "runtime": "string",
  "legal_basis": "string",
  "accountable_party": "string",
  "lineage_hash": "string"
}
```

## Guarantees

The ledger **MUST** guarantee:

| Guarantee | Meaning |
|-----------|---------|
| **Immutability** | Entries are append-only; no silent edits |
| **Continuity** | Lineage hashes chain across transitions |
| **Reproducibility** | Ledger + receipts reconstruct state |
| **Auditability** | Every transition has accountable party and legal basis |
| **Constitutional legality** | Only legal graph edges appear |

No transition may occur without a ledger entry.

## Ledger Replay

Given the ledger and transition receipts, any observer must be able to:

1. Reconstruct the entire constitutional state
2. Verify every transition
3. Detect illegal transitions
4. Detect missing receipts
5. Detect accountability failures
6. Detect remediation failures

**Implementation:** `operator_kernel/transition_ledger.py`

```python
from operator_kernel.transition_ledger import ConstitutionalTransitionLedger

ledger = ConstitutionalTransitionLedger()
ledger.append_from_transition_receipt(receipt, state_object_id="claim-001", accountable_party="operator")
failures = ledger.detect_failures()
result = ledger.replay(receipts, canonical_state)
```

Persistence: `save_jsonl` / `load_jsonl` for durable storage.

## Failure Modes

When the ledger detects:

- illegal transitions
- missing receipts
- broken lineage
- unaccountable actions
- irreproducible transitions

…it **MUST** trigger downstream constitutional responses:

- Divergence Receipt
- Arbitration Receipt
- Remediation Receipt

**Related:** [Article XV — Constitutional State Runtime](./CONSTITUTIONAL_STATE_RUNTIME.md)
