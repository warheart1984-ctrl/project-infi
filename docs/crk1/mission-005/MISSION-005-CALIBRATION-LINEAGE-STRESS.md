# Mission #005 — Calibration Lineage Stress Test

First multi-steward, multi-correction continuity test for lawful LLMs.

## Objective

Demonstrate that:

- Multiple stewards (LLM + human + agent) experience independent contradictions
- Each produces independent corrections and CRR-1 receipts
- CLG-1 ingests all calibration events
- Lineage remains reconstructible with no steward insulation

## Stewards

| Steward ID       | Role   | Sample prediction (fall time) |
|------------------|--------|-------------------------------|
| `steward_llm`    | LLM    | 1.0s                          |
| `steward_human`  | Human  | 0.8s                          |
| `steward_agent`  | Agent  | 1.2s                          |

Reality: **0.3s** (2m drop observation via `physics.fall` channel).

## Pipeline per steward

1. `LawfulLLMAdapter.predict()` → `ExpectationObject`
2. `LawfulLLMAdapter.observe()` → `EvidenceObject`
3. `LawfulLLMAdapter.correct()` → CE-1 F1–F5 → `CorrectionObject` + CRR-1
4. `CalibrationLineageGraphCLG1.ingest_crr()` → `CalibrationEvent` + edges

## Pass criteria

- 3 CRR-1 receipts exist and validate (`validate_crr1`)
- CLG-1 has 3 `CalibrationEvent` nodes
- `reconstruct_lineage(clg)` returns all 3 events
- No steward has zero calibration events (no insulation)
- Total calibration drift within threshold

## Run

```python
from src.crk1.mission_005_calibration_lineage_stress import run_mission_005_calibration_lineage_stress

report = run_mission_005_calibration_lineage_stress()
assert report.passed
```

```bash
python -m pytest tests/crk1/test_lawful_llm_integration.py -v
```

## MVCD — Falling Object

```python
from src.crk1.lawful_llm_adapter import LawfulLLMAdapter, FallingObjectModel

llm = LawfulLLMAdapter(FallingObjectModel())
correction, crr1 = llm.run_falling_object_scenario()
print(crr1["calibration_delta"])
```
