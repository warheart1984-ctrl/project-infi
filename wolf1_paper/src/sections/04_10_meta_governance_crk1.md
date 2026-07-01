## 4.10 Meta‑Governance of CRK‑1

CRK‑1 is governed by a meta‑layer ensuring correctness.

### Redundant Evaluators
- Primary Evaluator (PE)
- Shadow Evaluator (SE)

Mismatch → Class A fault.

### Drift Detection
CRK‑1 maintains baseline signatures of evaluation behavior.

### Meta‑Receipts
Each evaluation produces:
- invariant set hash
- evaluator signatures
- drift metrics

### Ground‑Verifiable Determinism
Ground can replay any evaluation; mismatch → Class A fault.

Diagram: `assets/diagrams/meta_governance_crk1.mmd`

---
