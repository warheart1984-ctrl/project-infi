# Installation

## Requirements

- Python 3.10+
- Git (for editable install from source)

## From source (monorepo)

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
pip install -e ".[dev]"
```

## Verify install

```bash
continuity info
```

Expected output:

```
Continuity SDK v1
Governed • Corrigible • Lineage-Preserving
```

## Python import

```python
from continuity_sdk import (
    LawfulLLMAdapter,
    FallingObjectModel,
    run_falling_object_scenario,
    run_mission_005_calibration_lineage_stress,
)
```

## Run tests

```bash
pytest tests/continuity_sdk/ -q
pytest tests/crk1/ -q
```

## Optional: CRK-1 runtime

The full constitutional runtime (`src/crk1/`) ships in the same repository. Mission certification:

```bash
python tools/run_mission_003_certification.py --json
```

## Next

[First Run](first-run.md)
