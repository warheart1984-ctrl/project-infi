# Mission #005

**Calibration Lineage Stress Test**

## Objective

Prove multi-steward calibration lineage under shared CLG-1.

## Scenario

Three stewards predict different fall times; reality observes 0.3s; each produces CRR-1; lineage reconstructs.

## Run

```bash
continuity mission 005
pytest tests/continuity_sdk/test_continuity_sdk.py::test_mission_005_demo -q
```

## Pass criteria

- 3 CRR-1 receipts validated
- 3 CalibrationEvent nodes
- Per-steward calibration profiles non-empty
- Lineage reconstruction matches calibration deltas

## Docs

- [SDK Mission #005](../../continuity-sdk/mission-005.md)
- [MISSION-005-CALIBRATION-LINEAGE-STRESS](../crk1/mission-005/MISSION-005-CALIBRATION-LINEAGE-STRESS.md)
- [MISSION-005-RECONSTRUCTION](../crk1/mission-005/MISSION-005-RECONSTRUCTION-REALITY-CONTACT.md)
