# First Run

Run your first constitutional correction in under five minutes.

## CLI

```bash
continuity demo falling-object
```

Expected:

```
Running MVCD...
Expectation: 1.0s
Observation: 0.3s
Contradiction detected.
Correction applied.
Calibration delta: 0.7
```

## Python

```python
from continuity_sdk import run_falling_object_scenario

correction, crr1 = run_falling_object_scenario()
print("Calibration delta:", crr1["calibration_delta"])
print("CRR-1 id:", crr1["crr_id"])
```

## What just happened

1. **Expectation** — model predicted 1.0s fall time (2m drop)
2. **Evidence** — reality observed 0.3s
3. **Contradiction** — Δ = 0.7, threshold exceeded
4. **Surprise** — high (confidence-weighted)
5. **Correction** — judgment updated via CE-1
6. **Preservation** — CRR-1 receipt emitted, CLG-1 updated

## Steward console (optional)

```bash
continuity console
```

Renders the VR-style holographic dashboard.

## Multi-steward stress test

```bash
continuity mission 005
```

Three stewards, three corrections, one shared lineage graph.

## Next

- [Interactive Tutorial](../tutorials/interactive-tutorial.md)
- [MVCD Demo](../continuity-sdk/mvcd-demo.md)
- [Steward Certification](../continuity-os/stewardship/steward-certification.md)
