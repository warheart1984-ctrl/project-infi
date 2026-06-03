# Operator Workbench Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make operator-workbench-organ-organ-gate
python -m pytest tests/test_operator_workbench_organ.py -q
```
