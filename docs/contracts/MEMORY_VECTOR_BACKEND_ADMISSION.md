# Memory Vector Backend Admission

Authority: [`EXTERNAL_SUGGESTION_ADMISSION_RULE.md`](./EXTERNAL_SUGGESTION_ADMISSION_RULE.md)

Optional cloud backends also documented in
[`MEMORY_VECTOR_BACKEND_FIREBASE_ADMISSION.md`](./MEMORY_VECTOR_BACKEND_FIREBASE_ADMISSION.md).

## Admitted form

ScyllaDB Cloud Vector Search may serve as an **optional query projection** for
Jarvis Memory Board semantic retrieval. It is not constitutional truth and does
not replace:

- JSONL operator decision ledgers (accountability write authority)
- SQLite UGR graph projection (`UGR_GRAPH_QUERY_BACKEND=sqlite`)
- Memory Board controller install/swap law (`src/jarvis_memory_board.py`)

## Law filter outcome

| Check | Result |
|---|---|
| Preserves doctrine | Yes — slot purpose, trust class, and controller approval remain in board law |
| Respects module purpose | Yes — vector store is a retrieval projection behind `src/memory_vector_store.py` |
| Testable | Yes — `tests/test_memory_vector_store.py` |
| Documentable | Yes — this file + `deploy/scylladb/README.md` |
| New seams | No — dual backend via `AAIS_VECTOR_BACKEND`; default remains Chroma |

## Runtime contract

| Variable | Default | Effect |
|---|---|---|
| `AAIS_VECTOR_BACKEND` | `chroma` | `chroma` = local persistent Chroma; `scylladb` = Cloud projection |
| `AAIS_VECTOR_TENANT_ID` | `default` | Partition tenant for multi-tenant recall |
| `SCYLLA_*` | unset | Required only when backend is `scylladb` |

Implementation surfaces:

- Adapter: [`src/memory_vector_store.py`](../../src/memory_vector_store.py)
- Board routing: `store_board_memory` / `retrieve_board_memory` in [`src/jarvis_memory_board.py`](../../src/jarvis_memory_board.py)
- Schema: [`deploy/scylladb/schema.cql`](../../deploy/scylladb/schema.cql)

## Non-admitted uses

- Treating ScyllaDB as the sole write authority for operator decisions
- Bypassing Memory Board controller approval for installs or swaps
- Replacing UGR JSONL canonical ledger with CQL tables
