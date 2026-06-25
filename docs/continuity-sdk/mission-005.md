# Mission #005 — Calibration Lineage Stress Test

Multi-steward calibration lineage stress test.

## Purpose

Prove that **three independent stewards** can:

1. Emit different expectations
2. Receive the same reality contradiction
3. Produce separate CRR-1 receipts
4. Ingest into a **shared CLG-1**
5. Reconstruct lineage for future stewards

## CLI

```bash
continuity mission 005
```

Expected:

```
Running Calibration Lineage Stress Test...
3 stewards
3 corrections
3 CRR-1 receipts
Lineage reconstructed
Status: PASSED
```

## Python

```python
from continuity_sdk import run_mission_005_calibration_lineage_stress

report = run_mission_005_calibration_lineage_stress()
assert report.passed
print(report.crr_ids)
```

## Stewards

| Steward | Prediction | Δ vs 0.3s observed |
|---------|------------|-------------------|
| steward_llm | 1.0s | 0.7 |
| steward_human | 0.8s | 0.5 |
| steward_agent | 1.2s | 0.9 |

## Pass criteria

- 3 CRR-1 receipts validated
- 3 CalibrationEvent nodes in CLG-1
- Lineage reconstructible per steward
- No steward insulated (zero calibration events)
- Total drift within threshold

## Spec

Normative: [`crk1/mission-005/MISSION-005-CALIBRATION-LINEAGE-STRESS.md`](../crk1/mission-005/MISSION-005-CALIBRATION-LINEAGE-STRESS.md)

## Related

- [CLG-1 Lineage](../continuity-os/architecture/clg1-lineage.md)
- [Lineage Queries](../reference/lineage-queries.md)
