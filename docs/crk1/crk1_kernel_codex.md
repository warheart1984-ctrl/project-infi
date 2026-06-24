# CRK-1 Kernel Codex
Version 1.0 — Bound Constitutional Specification

The CRK-1 Kernel Codex is the canonical, bound form of the kernel.
It defines the complete set of invariants **K0–K12** that any CRK-1-compliant
runtime must satisfy.

---

## Layer I — Transmission (K0–K2)

**K0 — Consequence Transmission**  
Every executed Decision must produce a replayable Outcome, and every Outcome
must replay into admissible Evidence.

**K1 — Immutable Exposure**  
No valid transition may sever the Decision → Outcome → Evidence → Decision chain.

**K2 — Judgment–Consequence Coupling**  
Judgment must remain exposed to the consequences of its own Decisions and the
Decisions of its lineage.

---

## Layer II — Preservation (K3–K6)

**K3 — Anti-Insulation**  
Any state in which consequences cannot reach judgment is unconstitutional.

**K4 — Consequence Preservation**  
Constitutional changes are permitted only if they preserve consequence exposure.

**K5 — Mutation Admissibility**  
A mutation is admissible only if it preserves replayability, admissibility,
lineage exposure, and judgment coupling.

**K6 — Drift Envelope (CE)**  
Constitutional drift must not reduce consequence exposure:
`CE(Sₜ₊₁) ≥ CE(Sₜ)`.

---

## Layer III — Assimilation (K7–K12)

**K7 — Interpretive Pluralism**  
Evidence must always be processed by multiple independent interpretive frames.

**K8 — Prediction-Bound Interpretation**  
Interpretations must bind themselves to testable predictions and be updated by
outcomes.

**K9 — Anti-Monoculture**  
No interpretive frame may achieve structural dominance or suppress alternatives.

**K10 — Adversarial Reconstruction**  
For every piece of Evidence, at least one adversarial frame must be able to
reconstruct an alternative interpretation.

**K11 — Interpretive Drift Envelope (SE)**  
Interpretive drift must not reduce semantic exposure:
`SE(Sₜ₊₁) ≥ SE(Sₜ)`.

**K12 — Semantic Exposure Metric**  
`SE(S) = αP + βA + γC + δR > 0` at all times.

---

## Codex Summary

A CRK-1-compliant system:

- receives consequences (K0–K2)
- cannot block consequences (K3–K6)
- cannot neutralize consequences through interpretation (K7–K12)

---

## Layer IV — Reality Surface (KΩ, K13–K15)

**KΩ — Universal Consequence Exposure**  
No layer may be consequence-immune. Every constitutional element must admit
governed challenge paths, contradiction recording (e.g. Governance Reconstruction
Receipts), and periodic or event-triggered review.

**K13 — Reality Surface Preservation**  
The runtime must preserve exposure to external reality domains it does not
control, with aggregate consequence intensity above a constitutional threshold
θ_min. Reductions require a Governance Reconstruction Receipt.

**K14 — Anti-Domestication Constraint**  
Governance must not systematically reduce the Reality Diversity Index (RDI).
Significant reductions require higher-order authorization and compensating exposure.

**K15 — Reality Diversity Requirement**  
At least N_min independent consequence-generating environments must remain
observable, recordable, and admissible into governance.

This Codex is the final reference for any implementation claiming CRK-1 compliance.

---

## Implementation Map

| Codex layer | Primary modules |
|-------------|-----------------|
| K0–K3 | `runtime_facade.py`, `runtime_validator.py`, `attack_simulator.py` |
| K4–K6 | `consequence_lattice.py`, `governance_engine.py` |
| K7–K10 | `semantic_layer.py`, `semantic_replay_engine.py`, `interpretive_lineage_tree.py` |
| K11–K12 | `semantic_exposure_monitor.py`, `semantic_drift_auditor.py` |

Formal invariant registry: `docs/crk1/crk1_invariants.yaml`

---

## Visual Assets

| Asset | Use |
|-------|-----|
| [crk1_codex_cover.svg](crk1_codex_cover.svg) | Bound codex cover plate |
| [crk1_runtime_wall_poster.svg](crk1_runtime_wall_poster.svg) | Large-format systems map (2200×1400) |
| [crk1_kernel_minimap.svg](crk1_kernel_minimap.svg) | Compact header / dashboard minimap |
| [crk1_runtime_animation_spec.md](crk1_runtime_animation_spec.md) | Scene-by-scene animation guide |

---

## Operational Certification

Mission #003 (external reproduction + red-team) is the founder-independence gate:
[MISSION-003-EXTERNAL-REPRODUCTION-RED-TEAM.md](MISSION-003-EXTERNAL-REPRODUCTION-RED-TEAM.md)

```bash
uv run python tools/run_mission_003_certification.py
```
