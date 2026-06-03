# Patch Apply Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make patch-apply-organ-gate
python -m pytest tests/test_patch_apply_organ.py -q
```
