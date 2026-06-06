# Operator Decision Ledger v1 Proof

Status: **mvp proof**

## Claim

Append-only operator decision ledger with hash chain, digest API, temporal replay ingest, and checkpoint policy hooks.

## Reproduction

```bash
make operator-decision-ledger-gate
make operator-decision-ledger-v2-graph-gate
python -m pytest tests/test_operator_decision_ledger*.py -q
```
