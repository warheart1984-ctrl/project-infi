# Operator Decision Ledger Governed Proof

Status: **governed proof**

## Claims

| Claim | Label |
|-------|-------|
| Append-only JSONL with hash chain per scope | proven |
| Indexed query, diff, and federation graph APIs | proven |
| Temporal replay ingest joins ledger events | proven |
| Checkpoint policy blocks irreversible drift | proven |

## Reproduction

```bash
make operator-decision-ledger-gate
make operator-decision-ledger-v2-graph-gate
python -m pytest tests/test_operator_decision_ledger*.py tests/test_ugr_federation_v19_acceptance.py -q
```

Lab scenarios: [OPERATOR_DECISION_LEDGER_LAB_GUIDE.md](./OPERATOR_DECISION_LEDGER_LAB_GUIDE.md)
