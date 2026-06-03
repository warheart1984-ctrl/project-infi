# Nova Landing Surface Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make nova-landing-surface-organ-organ-gate
python -m pytest tests/test_nova_landing_surface_organ.py -q
```
