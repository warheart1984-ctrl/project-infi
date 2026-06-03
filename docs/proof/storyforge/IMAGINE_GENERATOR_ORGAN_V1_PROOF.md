# Imagine Generator Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make imagine-generator-organ-gate
python -m pytest tests/test_imagine_generator_organ.py -q
```
