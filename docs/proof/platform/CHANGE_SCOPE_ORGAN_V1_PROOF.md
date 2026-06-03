# Change Scope Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make change-scope-organ-gate
python -m pytest tests/test_change_scope_organ.py -q
```
