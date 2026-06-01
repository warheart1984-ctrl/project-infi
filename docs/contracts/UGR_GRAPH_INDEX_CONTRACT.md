# UGR Graph Index Contract (v1)

Authority: `META_ARCHITECT_LAWBOOK.md`, `docs/contracts/PATTERN_LEDGER_SCHEMA_V0_5.md`.

## Scope

Graph index v1 accelerates claim queries over the **canonical JSONL ledger**. JSONL append-only storage remains the source of truth.

## Enable

```bash
export UGR_GRAPH_ENABLED=1
export UGR_GRAPH_INDEX_CONFIG=deploy/ugr/graph-index.json
```

When disabled, `PatternLedgerStore.query_related` falls back to JSONL scan behavior.

## Architecture

| Layer | Path | Role |
|---|---|---|
| Canonical log | `**/claims.jsonl` under `.runtime/collective-pattern-ledger/` | Append-only writes |
| Graph index | `src/ugr/graph_index/` | In-memory adjacency + term index |
| Query API | `PatternLedgerStore.query_related`, mesh `:8097` | Indexed reads |

Index buckets: tenant, subject, predicate, term tokens, `(subject, predicate)` edges.

## Mesh service

| Service | Port | Routes |
|---|---|---|
| graph_index | 8097 | `GET /v1/graph/stats`, `POST /v1/graph/rebuild`, `POST /v1/graph/query`, `POST /v1/graph/related` |

## Monolith API

- `GET /api/ugr/graph/stats`
- `POST /api/ugr/graph/query`
- `POST /api/ugr/graph/rebuild`

## Acceptance

- Indexed `query_related` matches JSONL scan on the same corpus
- Appends update the index incrementally
- `UGR_GRAPH_ENABLED=0` preserves legacy scan path
- Debt **UGR-D2** partially closed — external graph DB still out of scope

## Verification

```bash
make ugr-graph-index-gate
```

Claim status: **asserted** until gate evidence is recorded in a proof bundle.
