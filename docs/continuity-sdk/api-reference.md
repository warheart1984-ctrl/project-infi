# Continuity SDK — API Reference

## Package: `continuity_sdk`

### Classes

#### `LawfulLLMAdapter`

```python
LawfulLLMAdapter(
    model,
    steward_id: str = "llm_steward",
    *,
    engine=None,
    clg=None,
    continuity_graph=None,
    channel_id: str = "reality.default",
    decision_cluster_id: str | None = None,
)
```

| Method | Description |
|--------|-------------|
| `ask(prompt)` | Governed decision + GRR header |
| `predict(prompt)` | `ExpectationObject` |
| `observe(observation)` | `EvidenceObject` |
| `correct(expectation, evidence)` | `(LawfulCorrection, crr1_dict)` |
| `run_falling_object_scenario()` | MVCD end-to-end |

#### `FallingObjectModel`

Canonical demo model — predicts 1.0s for fall prompts.

### Functions

#### `run_falling_object_scenario()`

Returns `(LawfulCorrection, dict)` — MVCD pipeline output with CRR-1 fields.

#### `run_mission_005_calibration_lineage_stress()`

Returns `Mission005CalibrationLineageReport` with `.passed`, `.crr_ids`, `.lineage`.

#### `render_steward_console(**kwargs)`

Returns ASCII VR-style steward console string.

### Steward certification

```python
from continuity_sdk.steward_certification import (
    STEWARD_CERTIFICATION_QUESTIONS,
    grade_steward_certification,
)

result = grade_steward_certification(["B", "B", "B", "B", "B", "B", "B", "C", "B", "C"])
# result.passed, result.score, result.title
```

## CLI: `continuity`

```
continuity info
continuity demo falling-object
continuity mission 005
continuity console
continuity certify [--answers B,B,B,...]
```

## CRR-1 dict keys (wire)

| Key | Description |
|-----|-------------|
| `crr_id` | Receipt identifier |
| `expected_outcome` | Prior prediction |
| `observed_outcome` | Reality value |
| `contradiction_delta` | Magnitude of error |
| `calibration_delta` | Judgment shift preserved |
| `steward_id` | Acting steward |

## Schemas

| Schema | Path |
|--------|------|
| GRR-1 | `fixtures/crk1/governance_reconstruction_receipt.schema.json` |
| CRR-1 | `fixtures/crk1/calibration_reconstruction_receipt.schema.json` |

## See also

[Data Structures](../reference/data-structures.md) · [Receipts](../reference/receipts.md)
