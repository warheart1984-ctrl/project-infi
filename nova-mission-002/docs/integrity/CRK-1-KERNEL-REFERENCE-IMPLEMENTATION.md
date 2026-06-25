# CRK-1 Constitutional Runtime Kernel — Reference Implementation

**Version:** 1.0  
**Purpose:** Modular, language-agnostic reference for CRK-1.

Implementation: `agent/` (Nova SDK) maps to this layout.

---

## 1. Kernel Architecture

| Component | Role |
|-----------|------|
| Law Kernel (K_LAW) | Constitutional law enforcement |
| Law Ledger | Append-only law history |
| Lawful Action Predicate (LAP) | Conjunction of invariant checks |
| Invariant Engine | Registry + evaluation |
| Continuity Substrate | Snapshots, diffs, replay |
| Pattern Ledger | Chained governance receipts |
| PIT-Band Evolution Engine | Evidence → band transitions |
| Lineage Engine | Identity and provenance |
| Governance Engine | Proposals, amendments |
| Panic Handler | Fail-closed recovery |

---

## 2. Module Layout

```
src/
  governance/     → invariants, validator, receipts, ledger
  continuity/     → substrate, snapshot
  core/           → planner, generator, agent
  events/         → lifecycle hooks
```

---

## 3. Core Pseudocode

### Lawful Action Predicate

```ts
function lawfulAction(action, context) {
  const invariants = invariantEngine.getActive()
  for (const inv of invariants) {
    const result = inv.check(action, context)
    if (result === "error") return { ok: false, invariant: inv.id }
  }
  return { ok: true }
}
```

### Continuity Snapshot

```ts
function takeSnapshot(state) {
  const hash = hashState(state)
  const snapshot = { id: uuid(), hash, state, ts: now() }
  continuityStore.append(snapshot)
  return snapshot
}
```

### Ledger Append

```ts
function appendReceipt(receipt) {
  const last = ledger.getLast()
  const newHash = hash(last.hash + JSON.stringify(receipt))
  ledger.append({ ...receipt, hash: newHash })
}
```

---

## 4. Constitutional Amendment Protocol

1. Freeze kernel
2. Export constitutional state
3. Apply amendment
4. Validate invariants, ledger, continuity
5. Restart kernel

---

## 5. Guarantees

Deterministic · Replayable · Drift-detecting · Fail-closed · Constitutional by construction
