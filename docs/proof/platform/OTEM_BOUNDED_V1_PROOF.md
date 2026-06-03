# OTEM Bounded V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| OTEM ceiling at default capability level 10 is `v10_governed` | asserted |
| Organ reports proposal-only chat posture | asserted |
| Execution ingress via workflow approvals at level 10 | asserted |

## Reproduction

```bash
make otem-bounded-organ-gate
python -m pytest tests/test_otem_bounded_organ.py tests/test_otem_capability.py -q
```
