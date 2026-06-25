# Continuity SDK Introduction

The Continuity SDK is the **minimal steward interface** for Continuity OS.

It exposes three primitives:

1. **LawfulLLMAdapter** — constitutional wrapper for any model
2. **Falling Object (MVCD)** — canonical contradiction → correction demo
3. **Mission #005** — multi-steward calibration lineage stress test

## Tagline

**Governed. Corrigible. Lineage-Preserving.**

## What the SDK guarantees

| Guarantee | Mechanism |
|-----------|-----------|
| Governed decisions | GRR-1 headers on steward actions |
| Calibration & correction | CE-1 pipeline (F1–F5) |
| Preserved lineage | CRR-1 → CLG-1 ingest |

## Install

```bash
pip install -e .
continuity info
```

## Quick example

```python
from continuity_sdk import LawfulLLMAdapter, FallingObjectModel

adapter = LawfulLLMAdapter(FallingObjectModel(), steward_id="my_steward")
exp = adapter.predict("Predict fall time for 2m drop.")
evidence = adapter.observe({"value": 0.3, "strength": 1.0})
correction, crr1 = adapter.correct(exp, evidence)
```

## CLI

| Command | Action |
|---------|--------|
| `continuity info` | Version and tagline |
| `continuity demo falling-object` | MVCD demo |
| `continuity mission 005` | Lineage stress test |
| `continuity console` | VR steward dashboard |
| `continuity certify` | Steward certification quiz |

## Further reading

- [LawfulLLMAdapter](lawful-llm-adapter.md)
- [MVCD Demo](mvcd-demo.md)
- [API Reference](api-reference.md)
- [Landing page](index.html)
