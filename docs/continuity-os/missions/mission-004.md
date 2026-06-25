# Mission #004

**Calibration Preservation & Kernel Challenge**

## Objective

Preserve corrigibility as first-class artifacts and keep the kernel challengeable.

## Deliverables

| Component | Artifact |
|-----------|----------|
| Calibration objects | ExpectationObject → CalibrationEvent |
| CE-1 | CorrectionEngineCE1 (F1–F5) |
| CRR-1 | Calibration Reconstruction Receipt |
| CLG-1 | Calibration Lineage Graph |
| Kernel challenge | KCR, IDC |

## Run

```bash
pytest tests/crk1/test_mission_004_calibration.py -q
```

## Docs

- [MISSION-004-CALIBRATION-PRESERVATION](../crk1/mission-004/MISSION-004-CALIBRATION-PRESERVATION.md)
- [MISSION-004-KERNEL-CHALLENGE](../crk1/mission-004/MISSION-004-KERNEL-CHALLENGE.md)
- [CE-1 Architecture](../architecture/ce1-calibration.md)
