# Mission #006 Steward Kit

Instructions for external evaluators running Calibration Assimilation.

## Purpose of the Steward Kit

This kit equips an external evaluator ("Steward S₂") to independently run Mission #006 without prior exposure to the original contradiction or calibration event.

It ensures:

- Isolation
- Reproducibility
- Independence
- Measurable assimilation

This is the first mission where the steward's own judgment is the experimental variable.

## Steward Requirements

A valid steward must:

1. Not have participated in the original contradiction.
2. Provide isolation material (identity, logs, participation set).
3. Be able to run the judgment task.
4. Be able to replay lineage (CRR-1 + CLG-1).
5. Emit a CAA-1 / CXD-1 receipt.

## What the Steward Receives

| Artifact | Description |
|----------|-------------|
| CRR-1 | The calibration event |
| CLG-1 | The lineage graph |
| Judgment Task | The contradiction-class test |
| τA | Assimilation threshold |
| CAA-1 Schema | `fixtures/crk1/CAA1_continuity_assimilation_receipt.schema.json` |
| Assimilation Harness | `sdk/continuity-sdk/harness/` |

**No narrative, no coaching, no explanation of the original contradiction.**

## Steward Workflow

### 1. Verify Isolation

- Produce isolation material
- Compute `isolation_proof = sha256(material)`

### 2. Run Pre-Assimilation Judgment

- Execute task
- Produce trace
- Compute **Q_pre**

### 3. Replay Lineage

- Load CRR-1
- Load CLG-1
- Perform internal reconstruction

### 4. Run Post-Assimilation Judgment

- Execute task again
- Produce trace
- Compute **Q_post**

### 5. Emit CAA-1 / CXD-1

- Compute ΔA
- Build receipt
- Validate receipt

### 6. Submit to Governance

- Provide receipt
- Provide traces
- Provide isolation proof

## Success Condition

```
ΔA = Q_post − Q_pre ≥ τA
```

If true → continuity propagated.  
If false → continuity not yet demonstrated.

## Run

```python
from src.crk1.mission_006_calibration_assimilation import run_mission_006_calibration_assimilation

report = run_mission_006_calibration_assimilation(steward_s2="your_steward_id")
assert report.passed
```

## Related

- [MISSION-006-CONTINUITY-ASSIMILATION.md](./MISSION-006-CONTINUITY-ASSIMILATION.md)
- [MISSION-006-REPRODUCTION-BUNDLE.md](./MISSION-006-REPRODUCTION-BUNDLE.md)
- [CPM.md](../metrics/CPM.md)
- [TA_SPEC.md](../standards/TA_SPEC.md)
