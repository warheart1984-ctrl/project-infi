# Cortex Arcs Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make cortex-arcs-organ-gate
python -m pytest tests/test_cortex_arcs_organ.py -q
```
