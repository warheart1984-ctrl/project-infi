# CRK-1 Consequence Transmission Lattice (K0–K12)

Formal specification for the completed CRK-1 kernel.

**Unified specification:** [CRK-1-UNIFIED-KERNEL-SPECIFICATION.md](CRK-1-UNIFIED-KERNEL-SPECIFICATION.md)  
**Semantic layer detail:** [crk1_semantic_layer.md](crk1_semantic_layer.md)  
**Founder-independent semantic test:** [CRK-1-FOUNDER-INDEPENDENT-REPRODUCTION-TEST-SEMANTIC.md](CRK-1-FOUNDER-INDEPENDENT-REPRODUCTION-TEST-SEMANTIC.md)

## Synthesis

| ID | Name | Role |
|----|------|------|
| **K0** | Consequence Transmission | Execute → Outcome → Replay → Evidence → Judgment |
| **K1** | Immutable Exposure Constraint | No deletion, quarantine, or replay blocking |
| **K2** | Judgment–Consequence Coupling | Decisions require identity + evidence + lineage |
| **K3** | Anti-Insulation Proof | No lineage escape or bypass |
| **K4** | Consequence Preservation Law | Changes must preserve Reality → Evidence → Judgment → Future Judgment |
| **K5** | Mutation Admissibility Test | Constitutional natural selection filter |
| **K6** | Constitutional Drift Envelope | CE(S_{t+1}) ≥ CE(S_t) |

**Principle:** Immutable exposure, not immutable structure. Mutate all you want — you don't get to turn off natural selection.

---

## K4 — Consequence Preservation Law

**Statement:** A constitutional system may modify any structure, threshold, or governance mechanism provided every modification preserves unbroken transmission from Reality → Evidence → Judgment → Future Judgment.

**Formal (valid):**

```
C valid ⟺ ∀d ∈ Decisions, ∃o,e':
  Execute(d) ⇒ Outcome(o) ∧ Replay(o) ⇒ Evidence(e') ∧ Affects(Judgment(d), e')
```

**Formal (invalid):**

```
C invalid ⟺ ∃d: Execute(d) ⇒ Outcome(o) ∧ Replay(o) ⇒ Evidence(e') ∧ ¬Affects(Judgment(d), e')
```

**Interpretation:** Change the constitution, governance, identity, architecture — but not create a version less exposed to consequences than before.

---

## K5 — Mutation Admissibility Test

**Statement:** Mutation M is admissible iff it preserves:

- Outcome generation
- Outcome replayability
- Evidence admissibility
- Lineage exposure
- Judgment coupling

**Formal:**

```
M admissible ⟺
  Preserves(M, Outcome.replayable = true) ∧
  Preserves(M, Evidence.admissible_for_decision = true) ∧
  Preserves(M, LineageExposure(identity, evidence)) ∧
  Preserves(M, Decision.input_evidence_required = true) ∧
  Preserves(M, Outcome→Evidence→Decision)
```

If any fail: **M is unconstitutional.**

---

## K6 — Constitutional Drift Envelope

**Statement:** Drift and transformation permitted only within an envelope preserving consequence exposure.

**Consequence Exposure Function:**

```
CE(S) = degree to which consequences propagate into judgment
```

**Drift envelope:**

```
CE(S_{t+1}) ≥ CE(S_t)

CE(S_{t+1}) < CE(S_t) ⇒ unconstitutional drift
```

Drift may increase, maintain, or redistribute exposure — but not decrease it.

---

## Implementation

```python
from src.crk1.consequence_lattice import (
    consequence_exposure,
    mutation_admissible,
    validate_consequence_preservation,
    validate_drift_envelope,
    apply_amendment_with_drift_check,
)
```

See also: `docs/crk1/crk1_invariants.yaml`, `src/crk1/runtime_validator.py`.
