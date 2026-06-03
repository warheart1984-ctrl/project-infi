# Invariant Engine Organ — V1 Proof

CISIV stage: **verification**

## Claims

| Claim | Label |
|-------|-------|
| Status API returns engine snapshot | `asserted` |
| Nova runtime consumer on companion path | `asserted` |

## Verification

```bash
python -m pytest tests/test_invariant_engine_organ.py -q
make invariant-engine-organ-gate
```
