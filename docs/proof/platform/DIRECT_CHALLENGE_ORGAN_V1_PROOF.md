# Direct Challenge Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make direct-challenge-organ-gate
python -m pytest tests/test_direct_challenge_organ.py -q
```
