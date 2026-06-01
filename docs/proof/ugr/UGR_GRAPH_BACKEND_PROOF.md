# UGR Graph Backend Proof

Claim status: **asserted** (local verification)

## Selected DB

**SQLite** — embedded projection at `collective-pattern-ledger/graph-projection/ugr_graph.sqlite3`

## Verification

```bash
make ugr-graph-backend-gate
```

## Artifacts

- `deploy/ugr/graph-backend.json`
- `src/ugr/graph_backends/sqlite_backend.py`
- `tests/test_ugr_graph_backend.py`
