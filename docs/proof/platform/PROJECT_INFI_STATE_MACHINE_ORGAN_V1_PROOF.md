# Project Infi State Machine Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make project-infi-state-machine-organ-organ-gate
python -m pytest tests/test_project_infi_state_machine_organ.py -q
```
