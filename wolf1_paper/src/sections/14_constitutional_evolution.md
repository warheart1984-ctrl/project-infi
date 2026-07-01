# 14. Constitutional Evolution Protocol

Diagram reference: `assets/diagrams/constitutional_evolution_protocol.mmd`

A constitutional system must evolve safely.
WOLF‑1 defines a mutation protocol for updating invariants, policies, and CRK‑1 logic.

---

## 14.1 Mutation Types

| Type | Description |
|-------|-------------|
| **M0** | Policy update (non‑constitutional) |
| **M1** | Invariant addition |
| **M2** | Invariant removal |
| **M3** | Invariant modification |
| **M4** | CRK‑1 evaluator update |

---

## 14.2 Preconditions

A mutation requires:

- ground‑signed authorization
- invariant‑set hash match
- drift‑free state
- SAFE‑MODE S3
- quorum of redundant evaluators

---

## 14.3 Mutation Ledger Entry

Each mutation is recorded with:

- mutation type
- before/after invariant sets
- justification
- empirical evidence
- expected impact
- rollback path

---

## 14.4 Rollback Protocol

If a mutation causes:

- increased fault rate
- increased anomaly rate
- evaluator divergence
- constitutional drift

…the system automatically rolls back to the previous invariant set.

---

## 14.5 Evolution Safety Guarantees

- No mutation during active burns
- No mutation during cognitive runs
- No mutation bypasses CRK‑1
- All mutations are replayable on ground

---
