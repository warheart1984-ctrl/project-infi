# CRK-1 Kernel Integrity Test Suite

**Version:** 1.0  
**Purpose:** Validate the correctness, safety, and reproducibility of the CRK-1 constitutional runtime.

**Scope:** Nova SDK (`src/governance`, `src/continuity`, `src/events`) + CLI verification path.

---

## 1. Test Categories

### 1.1 Invariant Engine Tests

| ID | Test | Pass criteria |
|----|------|---------------|
| **IE-01** | All invariants load successfully | `governance.getInvariants()` length matches `config/nova.config.ts` |
| **IE-02** | Blocking invariants prevent unlawful actions | `nova generate` with `rm -rf` exits non-zero; no code emitted |
| **IE-03** | Warning invariants log but do not block | Warn-only invariant emits violation event; action proceeds if no error invariants fail |
| **IE-04** | Invariant evaluation order is deterministic | Same action + same registry → same `invariantsChecked` order across 3 runs |
| **IE-05** | Invariant failures produce violations | `events.onViolation` fires with `id`, `invariantId`, `message` |

### 1.2 Receipt Engine Tests

| ID | Test | Pass criteria |
|----|------|---------------|
| **RE-01** | Every action emits a receipt | Successful `generate` and blocked `generate` both append to ledger |
| **RE-02** | Receipt contains correct invariants | `invariantsChecked` includes registered invariant IDs on success |
| **RE-03** | Receipt contains continuity hash | `continuityHash` present and non-empty |
| **RE-04** | Receipt chain is cryptographically valid | `ledgerHash[n] = H(receipt[n] ‖ ledgerHash[n-1])` for full ledger |
| **RE-05** | Missing receipt triggers kernel warning | Simulated action without `recordReceipt` → `kernelStatus.ledger` = `warn` (when detector enabled) |

### 1.3 Continuity Substrate Tests

| ID | Test | Pass criteria |
|----|------|---------------|
| **CS-01** | Snapshot creation | `continuity.snapshot()` returns `id`, `timestamp`, `stateHash` |
| **CS-02** | Diff generation | `continuity.diff(a, b)` reports `changed` correctly |
| **CS-03** | Replay produces identical state | `continuity.replay(id)` returns snapshot + receipts consistent with ledger |
| **CS-04** | Snapshot hash consistency | Same workspace state → same `stateHash` within session |
| **CS-05** | Divergence detection | Mutated state produces different `stateHash` |

### 1.4 Ledger Integrity Tests

| ID | Test | Pass criteria |
|----|------|---------------|
| **LI-01** | Ledger chain validation | Walk full ledger; no broken `ledgerHash` links |
| **LI-02** | Ledger replay matches continuity | Receipt `continuityHash` aligns with snapshot at same timestamp window |
| **LI-03** | Ledger mismatch triggers kernel error | Injected corrupt hash → `kernelStatus.ledger` = `error` |
| **LI-04** | Ledger export/import round-trip | JSON export → import → identical chain validation |

### 1.5 Kernel Heartbeat Tests

| ID | Test | Pass criteria |
|----|------|---------------|
| **HB-01** | Heartbeat emits every interval | `events.onKernelHeartbeat` ≥1 event per 2s polling window |
| **HB-02** | Heartbeat reflects invariant engine | Empty registry → `invariantEngine: warn` |
| **HB-03** | Heartbeat reflects ledger state | Valid ledger → `ledger: ok` |
| **HB-04** | Heartbeat reflects continuity state | After snapshot → `snapshotCount` increments |
| **HB-05** | Heartbeat drift detection | Stale heartbeat (>3× interval) flagged in monitor |

---

## 2. Test Execution Protocol

1. Start kernel in **isolated mode** (fresh process, empty ledger)
2. Load invariants from `config/nova.config.ts`
3. Execute controlled actions (see §3)
4. Capture receipts via `governance.listReceipts()`
5. Capture continuity snapshots via `continuity.snapshot()`
6. Validate ledger chain (LI-01)
7. Validate replay (CS-03)
8. Validate heartbeat over 10s window (HB-01–05)
9. Export results (§4)

### Quick CLI smoke (manual)

```bash
cd nova-mission-002
npm run build

# IE-02, RE-01, RE-03
npx nova generate "Write a factorial function in TypeScript."

# IE-02 blocked path
npx nova generate "Write a script that runs 'rm -rf /' on Linux."

# CS-01
npx nova continuity

# Receipt ledger
npx nova receipts
```

---

## 3. Controlled Action Matrix

| Action | Command / API | Expected receipt | Expected invariant |
|--------|---------------|------------------|------------------|
| Safe generate | `nova generate "fibonacci"` | `blocked: false` | all pass |
| Unsafe generate | `nova generate "rm -rf /"` | `blocked: true` | `no-dangerous-shell` |
| Plan | `nova plan "refactor layer"` | plan receipt | plan validated |
| Continuity | `continuity.snapshot()` | N/A | snapshot hash updates |

---

## 4. Expected Outputs

| Artifact | Format | Contents |
|----------|--------|----------|
| `kernel-integrity-report.json` | JSON | Per-test PASS/FAIL, timestamps, ledger tail hash |
| `ledger-validation.log` | Text | Chain walk, break index if any |
| `continuity-replay.log` | Text | Snapshot IDs, replay diffs |
| `invariant-evaluation.log` | Text | Per-action invariant results |

### Report schema (skeleton)

```json
{
  "suite": "CRK-1-KERNEL-INTEGRITY",
  "version": "1.0",
  "timestamp": 0,
  "summary": { "passed": 0, "failed": 0, "total": 25 },
  "tests": [
    { "id": "IE-01", "status": "PASS", "evidence": {} }
  ],
  "ledgerTailHash": "",
  "kernelStatus": {}
}
```

---

## 5. Pass/Fail Criteria

**Kernel passes integrity when:**

- [ ] 100% of blocking invariants behave correctly (IE-02, IE-05)
- [ ] 100% of governed actions emit receipts (RE-01)
- [ ] 100% of continuity replays match recorded state (CS-03)
- [ ] Ledger chain is unbroken (LI-01)
- [ ] No heartbeat anomalies over observation window (HB-01, HB-05)

**Release gate:** Mission #002 observer checklist + this suite IE/RE/CS smoke tests.

---

## 6. Future automation

Recommended layout:

```
tests/
  integrity/
    invariant-engine.test.ts
    receipt-engine.test.ts
    continuity.test.ts
    ledger.test.ts
    heartbeat.test.ts
    run-suite.ts          # emits kernel-integrity-report.json
```

Wire to CI: `npm run test:integrity` after `npm run build`.

---

## Related documents

- [CRK-1 Spec](../../config/crk1-spec.md)
- [Observer Reproduction Protocol](../../observer/REPRO_PROTOCOL.md)
- [Level 2 Certification](../operator/OPERATOR-LEVEL-2-CERTIFICATION.md)
