# Aris Integration Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make aris-integration-organ-organ-gate
python -m pytest tests/test_aris_integration_organ.py -q
```
