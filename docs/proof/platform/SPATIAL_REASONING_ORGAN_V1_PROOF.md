# Spatial Reasoning Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make spatial-reasoning-organ-gate
python -m pytest tests/test_spatial_reasoning_organ.py -q
```
