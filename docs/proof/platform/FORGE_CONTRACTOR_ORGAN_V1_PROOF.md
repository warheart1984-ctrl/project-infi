# Forge Contractor Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make forge-contractor-organ-organ-gate
python -m pytest tests/test_forge_contractor_organ.py -q
```
