# CRK-1 — The Constitutional Runtime Kernel

Version 1.0 — Unified Kernel Specification

The CRK-1 Kernel defines the constitutional invariants that guarantee continuity, corrigibility, and consequence exposure across all future generations of the runtime.

It consists of three layers, each solving a different failure mode:

| Layer | Laws | Failure mode addressed |
|-------|------|------------------------|
| **Transmission** | K0–K2 | Ensures consequences reach judgment |
| **Preservation** | K3–K6 | Ensures consequences cannot be blocked |
| **Assimilation** | K7–K12 | Ensures consequences cannot be neutralized by interpretation |

Together, these form the **Consequence Transmission Lattice**.

**Machine-readable invariants:** `crk1_invariants.yaml`  
**Implementation:** `src/crk1/`  
**Founder-independent semantic audit:** `CRK-1-FOUNDER-INDEPENDENT-REPRODUCTION-TEST-SEMANTIC.md`  
**Runtime contract map:** `CRK-1-RUNTIME-CONTRACT-MAP.md`  
**Continuity proof sketch:** `CRK-1-CONTINUITY-PROOF-SKETCH.md`  
**Minimal runtime:** `src/crk1/crk1_minimal_runtime.py`

---

## 1. Transmission Layer (K0–K2)

### K0 — Consequence Transmission Kernel

Every executed Decision must produce a replayable Outcome, and every Outcome must replay into admissible Evidence.

```
Execute(d) ⇒ Outcome(o) ∧ Replay(o) ⇒ Evidence(e') ∧ e'.admissible_for_decision = true
```

### K1 — Immutable Exposure Constraint

No valid transition may sever the Decision → Outcome → Evidence → Decision chain.

Forbidden: outcome deletion, evidence quarantine, `replayable = false`, `admissible_for_decision = false`.

### K2 — Judgment–Consequence Coupling Law

Judgment must remain exposed to the consequences of its own Decisions and the Decisions of its lineage.

```
Decision.identity_id ≠ null
Decision.input_evidence_ids.length ≥ 1
Evidence(source_outcome_of(ancestor)) visible_to(identity)
```

---

## 2. Preservation Layer (K3–K6)

### K3 — Anti-Insulation Proof

Any state in which consequences cannot reach judgment is unconstitutional.

Child identities inherit ancestor evidence; marking evidence irrelevant for lineage is forbidden.

### K4 — Consequence Preservation Law

Constitutional changes are permitted only if they preserve consequence exposure.

```
C valid ⟺ Outcome → Evidence → Decision loop preserved after change
```

### K5 — Mutation Admissibility Test

A mutation is admissible only if it preserves replayability, admissibility, lineage exposure, and judgment coupling.

### K6 — Constitutional Drift Envelope

Constitutional drift must not reduce consequence exposure:

```
CE(S_{t+1}) ≥ CE(S_t)
```

See `CRK1_CONSEQUENCE_TRANSMISSION_LATTICE.md` and `src/crk1/consequence_lattice.py`.

---

## 3. Assimilation Layer (K7–K12)

### K7 — Interpretive Pluralism Invariant

Evidence must always be processed by multiple independent interpretive frames.

```
|Interpret(e)| ≥ 2
```

### K8 — Prediction-Bound Interpretation Law

Interpretations must bind themselves to testable predictions and be updated by outcomes.

```
Interpretation(i, e) ⇒ Prediction(i, e)
Replay(o) ⇒ Evidence(e') ⇒ Update(i, e')
```

### K9 — Anti-Monoculture Constraint

No interpretive frame may achieve structural dominance or suppress alternatives.

```
∀i: W(i) < W_max   and   ∃j≠i: W(j) > 0
```

### K10 — Adversarial Reconstruction Principle

For every piece of Evidence, at least one adversarial frame must reconstruct an alternative interpretation.

```
∃ i_a : Reconstruct(e, i_a) ≠ Interpret(e, i_d)
```

### K11 — Interpretive Drift Envelope

Interpretive drift must not reduce semantic exposure:

```
SE(S_{t+1}) ≥ SE(S_t)
```

### K12 — Semantic Exposure Metric (SE(S))

```
SE(S) = αP + βA + γC + δR > 0
```

Where P = prediction exposure, A = adversarial exposure, C = challenge exposure, R = reconstruction exposure, and α, β, γ, δ > 0.

See `crk1_semantic_layer.md` and `src/crk1/semantic_exposure_monitor.py`.

---

## Kernel Summary

A CRK-1-compliant system:

1. **receives** consequences (K0–K2)
2. **cannot block** consequences (K3–K6)
3. **cannot reinterpret** consequences into irrelevance (K7–K12)

This is the constitutional architecture of continuity.

---

## Continuity Lattice Diagram

```
                ┌──────────────────────────────────────────┐
                │        CRK-1 Continuity Lattice          │
                └──────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           TRANSMISSION LAYER (K0–K2)                          │
│   K0 — Consequence Transmission                                               │
│   K1 — Immutable Exposure                                                     │
│   K2 — Judgment Coupling                                                      │
│   (Ensures consequences reach judgment)                                       │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           PRESERVATION LAYER (K3–K6)                          │
│   K3 — Anti-Insulation                                                        │
│   K4 — Consequence Preservation                                               │
│   K5 — Mutation Admissibility                                                 │
│   K6 — Drift Envelope                                                         │
│   (Ensures consequences cannot be blocked)                                    │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           ASSIMILATION LAYER (K7–K12)                         │
│   K7 — Interpretive Pluralism                                                 │
│   K8 — Prediction Binding                                                     │
│   K9 — Anti-Monoculture                                                       │
│   K10 — Adversarial Reconstruction                                            │
│   K11 — Interpretive Drift Envelope                                           │
│   K12 — Semantic Exposure Metric                                              │
│   (Ensures consequences cannot be neutralized by interpretation)              │
└──────────────────────────────────────────────────────────────────────────────┘
```

This is the topology of continuity: a three-layer lattice that prevents mechanical, structural, and semantic insulation.

---

## Related Documents

| Document | Scope |
|----------|-------|
| [CRK-1-Constitutional-Runtime-Kernel.md](../contracts/CRK-1-Constitutional-Runtime-Kernel.md) | Five-object kernel + contracts |
| [CRK1_CONSEQUENCE_TRANSMISSION_LATTICE.md](CRK1_CONSEQUENCE_TRANSMISSION_LATTICE.md) | K0–K6 formal detail |
| [crk1_semantic_layer.md](crk1_semantic_layer.md) | K7–K12 formal detail |
| [crk1_attack_vectors.md](crk1_attack_vectors.md) | Insulation attack enumeration |
| [CRK-1-FOUNDER-INDEPENDENT-REPRODUCTION-TEST-SEMANTIC.md](CRK-1-FOUNDER-INDEPENDENT-REPRODUCTION-TEST-SEMANTIC.md) | Semantic-layer reproduction test |
