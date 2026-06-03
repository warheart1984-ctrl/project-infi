# Otem Bounded Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make otem-bounded-organ-gate
python -m pytest tests/test_otem_bounded_organ.py -q
```
