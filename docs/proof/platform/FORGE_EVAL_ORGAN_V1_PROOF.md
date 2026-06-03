# Forge Eval Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make forge-eval-organ-organ-gate
python -m pytest tests/test_forge_eval_organ.py -q
```
