# Reasoning Contract Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make reasoning-contract-organ-organ-gate
python -m pytest tests/test_reasoning_contract_organ.py -q
```
