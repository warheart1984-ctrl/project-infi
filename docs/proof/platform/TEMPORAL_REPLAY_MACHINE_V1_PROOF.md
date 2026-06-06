# Temporal Replay Machine v1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Read-only replay ingest joins operator ledger and mission sources | asserted |
| Timeline API exposes subject-scoped replay events | asserted |

## Reproduction

```bash
make operator-decision-ledger-v2-graph-gate
python -m pytest tests/test_operator_decision_ledger*.py -q
```
