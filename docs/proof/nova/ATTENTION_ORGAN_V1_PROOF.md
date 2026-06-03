# Attention Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make attention-organ-gate
python -m pytest tests/test_attention_organ.py -q
```
