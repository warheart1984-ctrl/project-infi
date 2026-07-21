# Civilization OS — Vertical Slice v0.1

**Status:** Implemented and tested (LIRL v0.1) — **not** “Civilization OS live”  
**Law:** Drive-G-1  
**Date:** 2026-07-20 (implemented 2026-07-21)

---

## Slice name

**Lawful Intent Receipt Loop (LIRL)**

```
intent → law gate → memory write → receipt/evidence → operator view
```

---

## Implementation (evidence)

| Step | Module | Package / path |
|------|--------|----------------|
| Intent API | `LirlRuntime.processIntent()` | `packages/lirl/src/loop.ts` |
| Law gate | `LirlLawGate` + `InvariantEngine` | `packages/lirl/src/lawGate.ts`, `@aaes-os/aaes-governance` |
| Memory write | `GovernedMemoryStore` | `packages/lirl/src/memory.ts` → `.runtime/lirl/memory/memory.jsonl` |
| Receipt | `LirlReceiptService` + `createEvidenceReceipt` | `packages/lirl/src/receipts.ts`, `@aaes-os/evidence-receipts` |
| Operator view | `buildOperatorSnapshot()` + HTML file | `packages/lirl/src/operatorView.ts` → `.runtime/lirl/operator.html` |
| HTTP surface | `POST /v1/lirl/intents`, `GET /v1/lirl/memory/:key`, `GET /v1/lirl/operator` | `services/platform-api/src/lirlRoutes.ts` |

**Tests:** `packages/lirl/src/lirl.test.ts` (3 cases) + `services/platform-api/src/lirl.test.ts` (2 HTTP cases)

```bash
cd project-infi
corepack pnpm --filter @aaes-os/lirl test
corepack pnpm --filter @aaes-os/platform-api test
corepack pnpm --filter @aaes-os/platform-cli test
```

## CLI (local, no platform-api)

```bash
cd project-infi
corepack pnpm --filter @aaes-os/platform-cli exec organism lirl intent \
  --action memory.write --actor operator-alpha --key greeting --value '{"text":"ma-la"}'
```

---

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Happy path: accept → memory row → receipt id → operator view | **pass** (`accepts lawful memory.write`) |
| 2 | Reject path: unlawful → no memory → rejection receipt | **pass** (`rejects unlawful intent`) |
| 3 | Docs list exact modules | **this file** |
| 4 | Scorecard note | **see** `docs/scorecards/project-infi.md` § Vertical slice |

---

## Example (package)

```typescript
import { LirlRuntime } from '@aaes-os/lirl';

const runtime = new LirlRuntime();
const result = await runtime.processIntent({
  actorId: 'operator-alpha',
  action: 'memory.write',
  payload: { key: 'greeting', value: { text: 'ma-la' } },
});
// result.receiptId, result.operatorView.html, runtime.operatorHtmlPath
```

## Example (HTTP via platform-api)

```http
POST /v1/lirl/intents
x-session-id: <session from /v1/auth/login>

{
  "action": "memory.write",
  "payload": { "key": "greeting", "value": { "text": "ma-la" } }
}
```

---

## Non-goals (still out of scope)

- Multi-organism mesh
- Full 7-layer ULX stack
- Mythar commercial licensing
- Replacing CIH/SRE
- Production-hardened operator UI (current operator view is static HTML snapshot)

---

## Related

- `IDENTITY.md`  
- `ORGAN_LEDGER.md`  
- `DOMAIN_BINDING_MYTHAR_SRE.md`
