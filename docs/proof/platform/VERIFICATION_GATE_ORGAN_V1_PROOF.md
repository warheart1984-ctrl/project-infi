# Verification Gate Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make verification-gate-organ-gate
python -m pytest tests/test_verification_gate_organ.py -q
```
