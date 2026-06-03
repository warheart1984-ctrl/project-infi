# Module Governance Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Module governance organ attests major_violation_disable_module | proven |
| Fail-closed posture aligned with live module_governance controller | asserted |

## Reproduction

```bash
make module-governance-organ-gate
python -m pytest tests/test_module_governance_organ.py -q
```
