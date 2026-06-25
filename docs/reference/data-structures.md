# Data Structures

Calibration pipeline objects (CE-1 layer).

## Pipeline order

```
ExpectationObject
    → EvidenceObject
    → ContradictionObject
    → SurpriseObject
    → CorrectionDeltaObject / CorrectionObject
    → CalibrationEvent
    → CRR-1 (wire receipt)
```

## ExpectationObject

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | EXP-* |
| `expected_outcome` | float \| string | Prediction |
| `expected_confidence` | 0–1 | Prior confidence |
| `assumptions` | string[] | Explicit assumptions |
| `model_ref` | string | Model identifier |

## EvidenceObject

| Field | Type | Description |
|-------|------|-------------|
| `evidence_ref` | string | Evidence identifier |
| `observed_outcome` | float \| string | Reality value |
| `channel_id` | string | Reality channel |
| `evidence_strength` | 0–1 | Signal quality |

## ContradictionObject

| Field | Type | Description |
|-------|------|-------------|
| `contradiction_delta` | float | \|expected − observed\| |
| `threshold_exceeded` | bool | Triggers CE-1 |
| `prediction_error_vector` | float[] | Signed error |

## SurpriseObject

| Field | Type | Description |
|-------|------|-------------|
| `surprise_intensity` | float | f(Δ, confidence) |
| `prior_confidence` | 0–1 | From expectation |

## CalibrationEvent

| Field | Type | Description |
|-------|------|-------------|
| `crr_id` | string | Linked CRR-1 |
| `steward_id` | string | Acting steward |
| `calibration_delta` | float | Preserved shift |

## Module

`src/crk1/calibration_objects.py`

## Invariants

C0–C5 enforced at construction. See [CE-1 Architecture](../continuity-os/architecture/ce1-calibration.md).
