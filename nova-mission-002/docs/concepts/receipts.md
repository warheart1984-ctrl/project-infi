# Receipts

Every meaningful action produces a `GovernanceReceipt`:

- `id` — UUID
- `timestamp` — Unix ms
- `action` — the governed action
- `invariantsChecked` — IDs of invariants evaluated
- `continuityHash` — workspace state hash
- `ledgerHash` — chained hash in pattern ledger

Blocked actions include `blocked: true` and `blockReason`.
