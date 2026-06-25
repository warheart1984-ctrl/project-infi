# Tutorial 4 — Writing an Invariant in AAES-OS

## What an invariant is

A non-negotiable rule that must hold for every run. Violations produce FaultReceipts and block execution.

## Where invariants live

```
aaes-os/packages/aaes-governance/src/invariantEngine.ts
```

Governance docs: [INVARIANTS.md](../governance/INVARIANTS.md)

## Example: no empty payload

```typescript
export const noEmptyPayload: Invariant = {
  id: "INV.NO_EMPTY_PAYLOAD",
  description: "Run payload must not be empty.",
  severity: "error",
  check(ctx) {
    const payload = ctx.run.payload;
    if (!payload || Object.keys(payload).length === 0) {
      return { ok: false, message: "Run payload is empty." };
    }
    return { ok: true };
  },
};
```

## CTS coverage

Every invariant needs a conformance test:

```bash
cd aaes-os && pnpm test
```

## Governance notes

- Document in `docs/aaes-os/governance/INVARIANTS.md`
- No new invariants in v1.0 without Council approval
- Must be deterministic (no time, randomness, or external state)
