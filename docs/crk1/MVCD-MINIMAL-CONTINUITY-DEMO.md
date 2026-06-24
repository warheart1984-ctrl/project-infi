# MVCD — Minimal Viable Continuity Demonstration

The smallest observable unit of continuity: **reality wins → judgment loses → correction is preserved**.

## Requirements

| ID | Requirement |
|----|-------------|
| R1 | Expectation with outcome, confidence, assumptions |
| R2 | Independent, consequence-bearing, verifiable evidence |
| R3 | Contradiction Δ = \|expected − observed\| > θ |
| R4 | Surprise S = f(Δ, confidence) |
| R5 | Correction of assumptions, confidence, judgment state |
| R6 | CRR-1 captures full calibration lineage |
| R7 | Future steward can reconstruct via `CalibrationCorrectionReceipt.reconstruct()` |

## Implementation

```python
from src.crk1.calibration_pipeline import run_continuity_proof_of_life

result, report = run_continuity_proof_of_life()
assert report.overall == "PASS"
```

## C-PoLT

Seven tests in `run_continuity_proof_of_life()` — see `tests/crk1/test_continuity_mvcd.py`.

## Related

- `CorrectionObject` — `src/crk1/correction_object.py`
- `CONTINUITY_CODEX.md` — K‑∞ through KΩ
- SCT / RAI / CFE — steward and system-level continuity metrics
