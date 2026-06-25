# Governance

Governance is the constitutional layer of Nova. It consists of:

1. **Invariant Engine** — rules that must hold before any action
2. **Pattern Ledger** — cryptographically chained receipt log
3. **Continuity Substrate** — snapshots and replay
4. **Receipt Generator** — atomic unit of traceability

## Lawful Action

An action is lawful only if all registered invariants pass. Blocked actions still produce receipts (with `blocked: true`).

## API

- `governance.validateAction(action)`
- `governance.requireInvariant(inv)`
- `governance.getReceipt(id)`
- `governance.trace()`
- `governance.listReceipts()`

See [CRK-1 Spec](../../config/crk1-spec.md) for the full constitutional contract.
