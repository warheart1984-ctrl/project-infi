# Workflow Shell Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make workflow-shell-organ-organ-gate
python -m pytest tests/test_workflow_shell_organ.py -q
```
