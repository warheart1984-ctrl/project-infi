# Scorpion Bridge Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make scorpion-bridge-organ-gate
python -m pytest tests/test_scorpion_bridge_organ.py -q
```
