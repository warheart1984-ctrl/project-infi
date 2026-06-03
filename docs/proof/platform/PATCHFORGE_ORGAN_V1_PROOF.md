# Patchforge Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make patchforge-organ-gate
python -m pytest tests/test_patchforge_organ.py -q
```
