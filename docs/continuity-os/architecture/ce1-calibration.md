# CE-1 — Correction Engine

The mechanism by which K-∞ is realized.

## Layer position

```
Reasoning Layer  → produces expectations
Calibration Layer → updates judgment  ← CE-1
Stewardship Layer → transmits calibration
```

## Constitutional functions

| Function | Description |
|----------|-------------|
| **F1** | Detect contradiction (expectation vs evidence) |
| **F2** | Quantify surprise (error × confidence) |
| **F3** | Apply correction (assumptions, model, confidence) |
| **F4** | Compute calibration delta |
| **F5** | Preserve calibration (CRR-1 + CLG-1) |

## Pipeline objects

1. ExpectationObject
2. EvidenceObject
3. ContradictionObject
4. SurpriseObject
5. CorrectionObject
6. CalibrationEvent / CRR-1

## Layer invariants (C0–C5)

| ID | Rule |
|----|------|
| C0 | No surprise without expectation |
| C1 | No correction without contradiction |
| C2 | No calibration without correction |
| C3 | Every correction must be preserved |
| C4 | Calibration must be reconstructible |
| C5 | Calibration must be transmissible |

## Implementation

- Module: `src/crk1/correction_engine_ce1.py`
- Class: `CorrectionEngineCE1`

## Spec

[`CALIBRATION_LAYER_SPECIFICATION`](../crk1/continuity-os/CALIBRATION_LAYER_SPECIFICATION.md)
