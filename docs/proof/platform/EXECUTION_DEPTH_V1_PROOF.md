# Execution Depth V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Patch apply organ reports operator-gated apply | asserted |
| Run ledger organ surfaces durable history posture | asserted |

## Reproduction

```bash
make patch-apply-organ-gate run-ledger-organ-gate
python -m pytest tests/test_patch_apply_organ.py tests/test_run_ledger_organ.py -q
```
