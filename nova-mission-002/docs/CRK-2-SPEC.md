# CRK-2 Constitutional Runtime Kernel — Formal Specification

**Version:** 2.0 (Draft)  
**Status:** Draft  
**Scope:** Kernel-level constitutional runtime for governed, multi-agent systems.

Implementation: `crk2/`

---

## 1. Purpose and Design Goals

| Goal | Description |
|------|-------------|
| Deterministic | Same inputs → same constitutional outcomes |
| Replayable | Every governed trajectory reconstructible |
| Drift-aware | Detect and correct divergence across agents |
| Fail-closed | On uncertainty, block actions |
| Distributed | Multi-agent coherence (cluster-aware) |
| Evolvable | Upgrades (CRK-1 → CRK-2 → CRK-3) without losing continuity |

---

## 2. Canonical Object Model

### 2.1 IdentityObject

```ts
IdentityObject {
  id: UUID
  kind: "agent" | "operator" | "kernel"
  lineageId: UUID
}
```

### 2.2 EvidenceObject

```ts
EvidenceObject {
  id: UUID
  domain: string
  payload: JSON
  ts: int
}
```

### 2.3 DecisionObject

```ts
DecisionObject {
  id: UUID
  actionId: UUID
  invariantsChecked: string[]
  pitBand: PITBand
  continuityHash: string
  clusterViewHash: string
  verdict: "allow" | "deny"
}
```

### 2.4 OutcomeObject

```ts
OutcomeObject {
  id: UUID
  decisionId: UUID
  stateDelta: DiffObject
  receipts: ReceiptObject[]
}
```

### 2.5 ConstraintObject (new)

```ts
ConstraintObject {
  id: UUID
  scope: "local" | "cluster"
  predicateRef: string
  severity: "error" | "warn"
  description: string
}
```

---

## 3. PIT-Band Model (PIT-1 → PIT-5)

| Band | Role |
|------|------|
| PIT-1 | Direct evidence |
| PIT-2 | Derived evidence |
| PIT-3 | Contextual evidence |
| PIT-4 | Self-evaluation |
| PIT-5 | Constitutional introspection (self-assessment, not self-modification) |

PIT transitions are monotonic and deterministic. PIT-5 may evaluate but not mutate constitutional law directly.

---

## 4. Distributed Lawful Action Predicate (dLAP)

\[
dLAP(a, c, S) = LAP_{local}(a, c) \land LAP_{cluster}(a, S) \land LAP_{constraints}(a, c, S)
\]

Properties: total, deterministic, side-effect free, fail-closed.

---

## 5. Continuity Substrate v2

### Snapshot

```ts
Snapshot {
  id: UUID
  hash: string
  partial: boolean
  state: JSON
  ts: int
}
```

### Constitutional Replay Proof (CRP)

```ts
CRP {
  snapshotId: UUID
  receipts: ReceiptObject[]
  pitTransitions: PITTransition[]
  hash: string
}
```

---

## 6. Ledger v2

Append-only, cryptographically chained, operator annotations, CRDT-style multi-agent merge.

---

## 7. Multi-Agent Constitutional Coherence (MACC)

Cluster state summary:

```ts
ClusterState {
  kernelVersion: "CRK-2"
  invariantSetHash: string
  constraintSetHash: string
  ledgerPrefixHash: string
  continuityAnchorHash: string
  pitDefinitionHash: string
}
```

---

## 8. Constitutional Amendments v2 (CA-2)

Freeze → export → apply amendment → validate dLAP, ledger, continuity, PIT → commit version → restart under CRK-2.

---

## 9. Kernel Guarantees

Deterministic decisions · Replayable trajectories (CRP) · Drift detection/correction · Fail-closed · Constitutional evolution with continuity preserved

---

## Related

- [CRK-2 Reference Implementation](./CRK-2-REFERENCE-IMPLEMENTATION.md)
- [CRK-1 → CRK-2 Migration](./CRK-1-TO-CRK-2-MIGRATION-PLAN.md)
- [CRK-2 → CRK-3 Roadmap](./CRK-2-TO-CRK-3-ROADMAP.md)
