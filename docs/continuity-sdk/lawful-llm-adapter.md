# LawfulLLMAdapter

Wrap any model in constitutional governance.

## Purpose

`LawfulLLMAdapter` ensures every model interaction passes through:

- **CRK-1** governance gate (GRR header on decisions)
- **CK-1 / CE-1** calibration pipeline (F1–F5)
- **CRR-1** preservation + **CLG-1** lineage ingest

Every model becomes a lawful steward.

## Usage

```python
from continuity_sdk import LawfulLLMAdapter, FallingObjectModel

adapter = LawfulLLMAdapter(
    FallingObjectModel(),
    steward_id="steward_llm",
    channel_id="physics.fall",
    decision_cluster_id="phenomenon:falling_object_2m",
)

# Emit expectation
exp = adapter.predict("Predict fall time for 2m drop.")

# Ingest reality
evidence = adapter.observe({"value": 0.3, "strength": 1.0})

# Correct and preserve
correction, crr1 = adapter.correct(exp, evidence)
```

## API surface

| Method | Returns | Role |
|--------|---------|------|
| `ask(prompt)` | `(raw, GRR header)` | Governed decision |
| `predict(prompt)` | `ExpectationObject` | What we expect |
| `observe(obs)` | `EvidenceObject` | What reality produced |
| `correct(exp, evd)` | `(LawfulCorrection, CRR-1 dict)` | Full calibration cycle |

## Custom models

Your model must be callable. Return a dict for rich expectations:

```python
class MyModel:
    def __call__(self, prompt: str) -> dict:
        return {
            "outcome": 42.0,
            "confidence": 0.85,
            "assumptions": ["linear_drag"],
        }
```

Optional hook after correction:

```python
def on_correction(self, correction: CorrectionObject) -> None:
    ...
```

## Implementation

Core: `src/crk1/lawful_llm_adapter.py`  
SDK facade: `src/continuity_sdk/lawful_llm_adapter.py`

## Related

- [MVCD Demo](mvcd-demo.md)
- [Building a Lawful Agent](../tutorials/building-a-lawful-agent.md)
- [CE-1 Architecture](../continuity-os/architecture/ce1-calibration.md)
