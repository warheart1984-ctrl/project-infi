# MVCD — Falling Object Demo

**Minimal Viable Continuity Demo** — the canonical contradiction → correction scenario.

## Scenario

A steward predicts fall time for a 2m drop:

| Stage | Value |
|-------|-------|
| Expectation | 1.0s |
| Observation | 0.3s |
| Contradiction Δ | 0.7 |
| Surprise | HIGH (confidence-weighted) |

Reality wins. Judgment updates. CRR-1 preserved.

## CLI

```bash
continuity demo falling-object
```

## Python

```python
from continuity_sdk import run_falling_object_scenario

correction, crr1 = run_falling_object_scenario()
```

Or via adapter directly:

```python
from continuity_sdk import LawfulLLMAdapter, FallingObjectModel

adapter = LawfulLLMAdapter(FallingObjectModel(), steward_id="steward_llm")
correction, crr1 = adapter.run_falling_object_scenario()
```

## Pipeline steps

1. ExpectationObject — predict 1.0s @ 0.9 confidence
2. EvidenceObject — observe 0.3s via `physics.fall` channel
3. ContradictionObject — Δ > threshold
4. SurpriseObject — intensity = Δ × confidence
5. CorrectionObject — model shift, confidence update
6. CRR-1 — preservation receipt
7. CLG-1 — lineage ingest

## C-PoLT

The underlying runtime runs seven Continuity Proof-of-Life tests:

```python
from src.crk1.calibration_pipeline import run_continuity_proof_of_life

result, report = run_continuity_proof_of_life()
assert report.overall == "PASS"
```

## Spec

Normative: [`crk1/MVCD-MINIMAL-CONTINUITY-DEMO.md`](../crk1/MVCD-MINIMAL-CONTINUITY-DEMO.md)

## Next

[Interactive Tutorial](../tutorials/interactive-tutorial.md)
