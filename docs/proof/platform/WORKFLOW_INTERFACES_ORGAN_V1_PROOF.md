# Workflow Interfaces Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Subsystem surface is read-only | asserted |

## Reproduction

```bash
make workflow-interfaces-organ-organ-gate
python -m pytest tests/test_workflow_interfaces_organ.py -q
```
