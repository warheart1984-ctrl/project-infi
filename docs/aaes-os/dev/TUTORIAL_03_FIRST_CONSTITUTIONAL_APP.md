# Tutorial 3 — Building Your First Constitutional App

## Goal

Create a governed run that produces a verifiable receipt.

## Steps

1. **Submit a run** through UCRRuntime or CRK-1 lawful path
2. **Emit spans** for init → execute → finalize
3. **Pass governance** — InvariantEngine pre-check and post-step validation
4. **Record receipt** in RunLedgerStore

## Minimal flow

```typescript
// aaes-os/packages/ucr-runtime — see integration tests
import { UCRRuntime } from "@aaes-os/ucr-runtime";

const runtime = new UCRRuntime();
const result = await runtime.execute({ payload: { task: "hello" } });
```

## Receipt verification

- Hash receipt content
- Validate invariant compliance
- Confirm ledger entry exists

## Governance rule

**Receipts, or it didn't happen.** Any new behavior must integrate with the ledger.
