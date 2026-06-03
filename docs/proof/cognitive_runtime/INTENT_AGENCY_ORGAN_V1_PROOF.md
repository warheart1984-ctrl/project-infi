# Intent Agency Organ — V1 Proof

CISIV stage: **verification**

## Claims

| Claim | Label |
|-------|-------|
| Status API returns agency snapshot | `asserted` |
| Session-reset fixture survival | `asserted` |

## Verification

```bash
python -m pytest tests/test_intent_agency_organ.py -q
make intent-agency-gate
```
