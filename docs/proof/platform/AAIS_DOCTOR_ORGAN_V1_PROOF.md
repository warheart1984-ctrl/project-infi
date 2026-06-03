# Aais Doctor Organ V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make aais-doctor-organ-organ-gate
python -m pytest tests/test_aais_doctor_organ.py -q
```
