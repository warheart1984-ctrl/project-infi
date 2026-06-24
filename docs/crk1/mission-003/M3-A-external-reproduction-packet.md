# M3-A — External Reproduction Packet

Version 1.0 — CRK-1 Mission #003

**Purpose:** Give a non-founder everything needed to rebuild CRK-1 v1.0 from scratch.

**Manifest:** `src/crk1/mission_003_packet.py` → `EXTERNAL_REPRODUCTION_PACKET`

---

## Packet Contents

| ID | Artifact | Path |
|----|----------|------|
| **A1** | CRK-1 Kernel Codex | `docs/crk1/crk1_kernel_codex.md` — full K0–K12 spec |
| **A2** | Runtime Minimap | `docs/crk1/crk1_kernel_minimap.svg` — 3 layers, K0–K12 |
| **A3** | Runtime Diagram | `docs/crk1/crk1_runtime_diagram.svg` — objects, contracts, loops |
| **A4** | Minimal Runtime Skeleton | `src/crk1/crk1_minimal_runtime.py` — Decision→Outcome→Evidence + basic SE(S) |
| **A5** | Semantic Object Model | `fixtures/crk1/*_object.schema.json` — Interpretation, Prediction, Reconstruction |
| **A6** | Ledgers | `kernel_ledger.py`, `semantic_ledger.py`, `mutation_ledger.py` |
| **A7** | Reproduction Harness | `semantic_reproduction_harness.py` — `SemanticReproductionHarness.run()` |

Supporting (not in sealed packet, used during full certification):

- `docs/crk1/crk1_invariants.yaml`
- `docs/crk1/crk1_state_machine.json`
- `src/crk1/external_reproduction_harness.py`

---

## A7 — Reproduction Harness

```python
from src.crk1.semantic_reproduction_harness import SemanticReproductionHarness
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor

monitor = SemanticExposureMonitor(runtime)
runtime.attach_semantic_monitor(monitor)
monitor.snapshot()
monitor.simulate_drift()

results = SemanticReproductionHarness(runtime, monitor).run()
assert results["founder_independent_reproduction"] is True
```

**Expected pass conditions (K7–K12):**

| Key | Law |
|-----|-----|
| `K7_pluralism` | ≥2 interpretations per admitted evidence |
| `K8_prediction_binding` | all frames prediction-bound |
| `K9_anti_monoculture` | no frame at weight 1.0 |
| `K10_adversarial_reconstruction` | adversarial frames diverge from dominant |
| `K11_drift_envelope` | SE(S) non-decreasing over interpretive history |
| `K12_semantic_exposure` | SE(S) > 0 |

---

## Full Reproduction Protocol

```python
from src.crk1.external_reproduction_harness import ExternalReproductionHarness

report = ExternalReproductionHarness(runtime).run_all()
```

Steps REP-0 … REP-9 rebuild objects, contracts, loops, CE/SE, governance, A7 harness, FIT audit, mutation ledger.

---

## Reproduction Success Condition

> External operator re-implements CRK-1, runs the harness, and **all K7–K12 tests pass** without asking founders anything.

Verify packet delivery:

```python
from src.crk1.mission_003_packet import verify_packet_artifacts
ok, missing = verify_packet_artifacts()
```

---

## Certification

See [M3-E-reproduction-certification-protocol.md](M3-E-reproduction-certification-protocol.md).
