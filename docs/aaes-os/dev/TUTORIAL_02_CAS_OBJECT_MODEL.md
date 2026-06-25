# Tutorial 2 — Understanding CAS 1.0

## Object model

CAS 1.0 defines governed cognition objects:

| Object | Role |
|--------|------|
| Identity | Who or what acts |
| Decision | A governed choice |
| Outcome | Result of a decision |
| Evidence | Supporting material |
| Interpretation | Structured reading of evidence |
| Receipt | Content-addressed proof of action |
| DriftObservation | Recorded continuity deviation |
| KernelChallenge | Formal dispute of behavior |

## Allowed transitions

All transitions are deterministic and constitutionally validated. No hidden state.

## First CAS request

Explore the reference implementation under `src/cas/` and CRK-1 integration in `src/crk1/`.

```bash
pytest tests/crk1/test_cas*.py -q
```

## Read next

- [Constitution](../governance/CONSTITUTION.md)
- [Invariants](../governance/INVARIANTS.md)
