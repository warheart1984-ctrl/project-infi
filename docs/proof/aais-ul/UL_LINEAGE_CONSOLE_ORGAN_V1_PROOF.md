# Ul Lineage Console Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make ul-lineage-console-organ-gate
python -m pytest tests/test_ul_lineage_console_organ.py -q
```
