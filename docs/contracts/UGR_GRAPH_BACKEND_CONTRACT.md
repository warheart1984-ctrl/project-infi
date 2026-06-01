# UGR Graph Backend Contract (UGR-D2 remainder)

Authority: `docs/programs/UGR_CLOUD_PROGRAM.md`

## Selected external graph DB

**SQLite** (`query_backend: sqlite`) — embedded projection at:

`.runtime/collective-pattern-ledger/graph-projection/ugr_graph.sqlite3`

### Rationale

| Option | Status |
|---|---|
| JSONL + in-memory | Default canonical + index (unchanged) |
| **SQLite** | **Selected v1 external query backend** — zero-ops, CI-friendly, rebuildable |
| Neo4j | Documented future option for multi-region traversals; not wired |

JSONL remains the **sole write authority**. SQLite is a derived read projection synced on rebuild/`on_append`.

## Enablement

| Variable | Value | Effect |
|---|---|---|
| `UGR_GRAPH_QUERY_BACKEND` | `sqlite` | Route graph queries through SQLite projection |
| `UGR_GRAPH_BACKEND_CONFIG` | path | Override `deploy/ugr/graph-backend.json` |
| `UGR_GRAPH_ENABLED` | `1` | Required for graph index store wiring |

## Verification

```bash
make ugr-graph-backend-gate
```

Evidence: `docs/proof/ugr/UGR_GRAPH_BACKEND_PROOF.md`
