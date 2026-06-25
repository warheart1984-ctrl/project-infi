# CAS → SDK Mapping

Developer-facing API over CAS objects. The SDK (`aaes-os/sdk/`) hides runtime internals while preserving constitutional guarantees.

**Dual-layer architecture:**

| Layer | Role |
|-------|------|
| **CTS** | Scientific spine — proves CAS is correct, deterministic, reproducible |
| **SDK** | Developer surface — ergonomic API over CAS objects |

---

## CAS Object → SDK API

### Identity

**CAS:**

```typescript
interface Identity {
  id: string;
  type: "agent" | "model" | "operator";
  metadata: Record<string, unknown>;
}
```

**SDK:**

```typescript
sdk.identity.create({ type, metadata })
sdk.identity.fromEnv()
sdk.identity.validate(identity)
```

### Run

**CAS:**

```typescript
interface Run {
  runId: string;
  identity: Identity;
  payload: Record<string, unknown>;
}
```

**SDK:**

```typescript
sdk.run.start({ identity, payload })
sdk.run.execute({ identity, payload })
sdk.run.fromReceipt(runId)
sdk.run.replay(runId)
```

### Span

**CAS:**

```typescript
interface Span {
  spanId: string;
  runId: string;
  type: string;
  timestamp: number;
  data?: Record<string, unknown>;
}
```

**SDK:**

```typescript
sdk.spans.list(runId)
sdk.spans.filter(runId, { type })
sdk.spans.timeline(runId)
```

### Receipt

**CAS:**

```typescript
interface Receipt {
  runId: string;
  hash: string;
  spans: Span[];
  result: unknown;
}
```

**SDK:**

```typescript
sdk.receipts.get(runId)
sdk.receipts.hash(runId)
sdk.receipts.compare(hashA, hashB)
sdk.receipts.export(runId)
```

### Fault

**CAS:**

```typescript
interface Fault {
  runId: string;
  invariantId: string;
  message: string;
}
```

**SDK:**

```typescript
sdk.faults.get(runId)
sdk.faults.list()
sdk.faults.explain(fault)
```

---

## High-Level SDK Examples

### Execute a run

```typescript
import { createSdk } from '../sdk/index.js';

const sdk = createSdk();
const result = await sdk.run.execute({
  identity: sdk.identity.fromEnv(),
  payload: { prompt: 'Hello' },
});
```

### Check determinism

```typescript
const hash1 = sdk.receipts.hash(runId);
const hash2 = sdk.receipts.hash(runId);
sdk.assert.equal(hash1, hash2);
```

### Inspect governance

```typescript
const faults = sdk.faults.list();
const invariants = sdk.governance.invariants();
```

### Run CDP-1

```typescript
const drift = await sdk.cdp1.runMinimal();
```

---

## CTS Structure

See [CAS 1.0 Spec](CAS_1_0_SPEC.md) and `aaes-os/tests/cts/`.

CTS validates:

1. **Object correctness** — identity, run, span, receipt, fault shapes
2. **Lifecycle correctness** — init → execute → finalize → receipt
3. **Governance correctness** — invariants enforced, faults journaled
