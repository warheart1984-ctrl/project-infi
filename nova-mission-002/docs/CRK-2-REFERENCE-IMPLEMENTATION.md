# CRK-2 Reference Implementation

**Version:** 1.0  
**Purpose:** Language-agnostic modular reference mapped to `crk2/` TypeScript modules.

---

## Directory Layout

```
crk2/
  kernel/
    index.ts
    dlap.ts
    pit-engine.ts
    constraint-engine.ts
    panic-handler.ts
  invariants/
    engine.ts
  continuity/
    substrate.ts
    crp.ts
    replay.ts
  ledger/
    ledger-v2.ts
  cluster/
    macc.ts
```

---

## Core Modules

### dLAP

```ts
export function dLAP(action, context) {
  const clusterState = clusterView()
  const local = invariantEngine.checkAll(action, context)
  if (!local.ok) return { ok: false, reason: "local-invariant", detail: local }
  const cluster = checkClusterInvariants(action, clusterState)
  if (!cluster.ok) return { ok: false, reason: "cluster-invariant", detail: cluster }
  const constraints = constraintEngine.check(action, context, clusterState)
  if (!constraints.ok) return { ok: false, reason: "constraint", detail: constraints }
  return { ok: true }
}
```

### Continuity v2 + CRP

See `crk2/continuity/substrate.ts` and `crk2/continuity/crp.ts`.

### Ledger v2

See `crk2/ledger/ledger-v2.ts`.

### MACC

See `crk2/cluster/macc.ts`.

---

## Related

- [CRK-2 Spec](./CRK-2-SPEC.md)
