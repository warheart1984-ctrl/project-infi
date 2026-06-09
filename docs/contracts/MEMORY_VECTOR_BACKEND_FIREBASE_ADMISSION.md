# Memory Vector Backend Admission — Firebase Data Connect

Authority: [`EXTERNAL_SUGGESTION_ADMISSION_RULE.md`](./EXTERNAL_SUGGESTION_ADMISSION_RULE.md)

Sibling optional backend: [`MEMORY_VECTOR_BACKEND_ADMISSION.md`](./MEMORY_VECTOR_BACKEND_ADMISSION.md) (ScyllaDB).

## Admitted form

Firebase Data Connect (PostgreSQL + pgvector + GraphQL) may serve as an **optional
query projection** for Jarvis Memory Board semantic retrieval. It is not constitutional
truth and does not replace:

- JSONL operator decision ledgers (accountability write authority)
- SQLite UGR graph projection (`UGR_GRAPH_QUERY_BACKEND=sqlite`)
- Memory Board controller install/swap law (`src/jarvis_memory_board.py`)

## Law filter outcome

| Check | Result |
|---|---|
| Preserves doctrine | Yes — slot purpose, trust class, and controller approval remain in board law |
| Respects module purpose | Yes — vector store is a retrieval projection behind `src/memory_vector_store.py` |
| Testable | Yes — `tests/test_memory_vector_store.py` (mocked REST); `python -m src.firebase_connection_test` against emulator or cloud |
| Documentable | Yes — this file + `deploy/firebase-data-connect/README.md` |
| New seams | No — triple backend via `AAIS_VECTOR_BACKEND`; default remains Chroma |

## Runtime contract

| Variable | Default | Effect |
|---|---|---|
| `AAIS_VECTOR_BACKEND` | `chroma` | `chroma` = local Chroma; `scylladb` = Scylla projection; `firebase` = Data Connect projection |
| `AAIS_VECTOR_TENANT_ID` | `default` | Partition tenant for multi-tenant recall |
| `FIREBASE_PROJECT_ID` | unset | Required when backend is `firebase` |
| `FIREBASE_DATA_CONNECT_LOCATION` | `us-central1` | Data Connect region |
| `FIREBASE_DATA_CONNECT_SERVICE` | `jarvis-memory` | Service id in `dataconnect.yaml` |
| `FIREBASE_DATA_CONNECT_CONNECTOR` | `jarvis-memory-connector` | Connector for predefined GraphQL ops |
| `GOOGLE_APPLICATION_CREDENTIALS` | unset | Service account for production REST calls |
| `DATA_CONNECT_EMULATOR_HOST` | unset | e.g. `127.0.0.1:9399` for local emulator (no OAuth) |

Implementation surfaces:

- REST client: [`src/firebase_dataconnect_client.py`](../../src/firebase_dataconnect_client.py)
- Adapter: [`src/memory_vector_store.py`](../../src/memory_vector_store.py) (`FirebaseDataConnectVectorBackend`)
- Smoke test: [`src/firebase_connection_test.py`](../../src/firebase_connection_test.py)
- Schema and ops: [`deploy/firebase-data-connect/dataconnect/`](../../deploy/firebase-data-connect/dataconnect/)

Predefined connector operations (all `@auth(level: NO_ACCESS)` — backend/service account only):

- `StoreMemoryChunk` — insert with custom 384-dim embedding
- `DeleteMemoryChunksBySlot` — clear docs partition
- `RetrieveMemorySimilarity` — tenant + slot + session ANN
- `RetrieveMemorySimilarityVerified` — adds trust_class filter
- `RetrieveMemorySimilarityDocs` — docs slot without session filter

## Non-admitted uses

- Treating Data Connect / Cloud SQL as the sole write authority for operator decisions
- Bypassing Memory Board controller approval for installs or swaps
- Replacing UGR JSONL canonical ledger with GraphQL mutations
- Client-side connector access without service-account isolation

## Verification checklist

1. From `deploy/firebase-data-connect/`: `firebase emulators:start --only dataconnect` (or deploy to cloud)
2. Export env from [`deploy/firebase-data-connect/.env.example`](../../deploy/firebase-data-connect/.env.example)
3. `python -m src.firebase_connection_test`
4. `AAIS_VECTOR_BACKEND=firebase` with board store/retrieve smoke on a non-production tenant
