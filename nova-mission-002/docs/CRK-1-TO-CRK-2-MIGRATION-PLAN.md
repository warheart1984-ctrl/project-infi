# CRK-1 → CRK-2 Constitutional Migration Plan

**Version:** 1.0  
**Purpose:** Safe, deterministic, continuity-preserving migration from CRK-1 to CRK-2.

---

## 1. Migration Goals

CRK-2 introduces: new constitutional objects, PIT-bands, continuity substrate, dLAP, lineage, invariant engine, ledger format.

Must preserve: continuity, ledger integrity, invariant semantics, PIT-band monotonicity, replay determinism.

---

## 2. Migration Phases

| Phase | Actions |
|-------|---------|
| 1 — Pre-Migration Audit | Validate CRK-1 invariants, ledger, continuity, PIT; freeze agents |
| 2 — Constitutional Export | Export objects, invariants, ledger, continuity, PIT, lineage |
| 3 — CRK-2 Initialization | Initialize new objects, PIT bands, substrate, ledger, dLAP |
| 4 — Constitutional Mapping | Map Identity, Evidence, Decision, Outcome, Resource |
| 5 — Continuity Reconciliation | Recompute hashes; validate replay, PIT, ledger chain |
| 6 — Kernel Restart | Restart kernel; resume agents; validate cluster coherence |
| 7 — Post-Migration Audit | Validate invariants, ledger, continuity, PIT, lineage |

---

## 3. Migration Guarantees

No loss of continuity · No loss of ledger integrity · No loss of invariants · No loss of PIT-bands · No loss of lineage · No drift

---

## Related

- [CRK-2 Spec](./CRK-2-SPEC.md)
- [Level 4 Operator Certification](./operator/OPERATOR-LEVEL-4-CERTIFICATION.md)
