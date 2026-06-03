# Deliberation Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make deliberation-organ-gate
python -m pytest tests/test_deliberation_organ.py -q
```
