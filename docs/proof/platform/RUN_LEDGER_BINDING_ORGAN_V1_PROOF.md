# Run Ledger Binding Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make run-ledger-binding-organ-organ-gate
python -m pytest tests/test_run_ledger_binding_organ.py -q
```
