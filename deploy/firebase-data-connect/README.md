# Firebase Data Connect — Memory Board Vector Projection

Optional **Firebase-native** vector backend for governed Jarvis Memory Board retrieval.
Chroma remains the default local backend (`AAIS_VECTOR_BACKEND=chroma`).

Firebase Data Connect (PostgreSQL + pgvector + GraphQL) matches the optional cloud
projection pattern used for ScyllaDB Cloud Vector Search.

## Why this fits AAIS

| AAIS law | How this backend respects it |
|---|---|
| Query projection only | Schema stores recall chunks; JSONL operator receipts stay write authority |
| Slot + tenant partitioning | `tenant_id`, `memory_slot`, `session_id`, `trust_class` mirror `src/memory_vector_store.py` |
| Testable | Unit tests mock REST; emulator/cloud via `python -m src.firebase_connection_test` |
| No hidden authority | Operations are `NO_ACCESS` — callable from service account / emulator only |

## Prerequisites

1. Firebase project with **Data Connect** and **Cloud SQL for PostgreSQL**
2. Node.js + `npx` on PATH (or global `firebase-tools`)
3. Python: `pip install google-auth sentence-transformers` (see `requirements-advanced.txt`)
4. Embedding model unchanged: `all-MiniLM-L6-v2` → **384 dimensions** (custom vectors, not Vertex `_embed`)

## Layout

```
deploy/firebase-data-connect/
├── firebase.json
├── README.md
├── .env.example
└── dataconnect/
    ├── dataconnect.yaml          # set cloudSql.instanceId before cloud deploy
    ├── schema/schema.gql
    └── connector/
        ├── connector.yaml
        ├── mutations.gql
        └── queries.gql
```

## Setup

From `deploy/firebase-data-connect/`:

```bash
npx -y firebase-tools@latest login
npx -y firebase-tools@latest use --add <PROJECT_ID>
# Edit dataconnect/dataconnect.yaml → set cloudSql.instanceId
npx -y firebase-tools@latest emulators:start --only dataconnect
npx -y firebase-tools@latest deploy --only dataconnect
```

Emulator env (example):

```bash
export FIREBASE_PROJECT_ID=<your-project-or-demo-id>
export DATA_CONNECT_EMULATOR_HOST=127.0.0.1:9399
python -m src.firebase_connection_test
```

## Runtime wiring

| Variable | Default | Effect |
|---|---|---|
| `AAIS_VECTOR_BACKEND` | `chroma` | Set `firebase` to use Data Connect projection |
| `FIREBASE_PROJECT_ID` | unset | Required for `firebase` backend |
| `FIREBASE_DATA_CONNECT_LOCATION` | `us-central1` | Data Connect region |
| `FIREBASE_DATA_CONNECT_SERVICE` | `jarvis-memory` | Service id |
| `FIREBASE_DATA_CONNECT_CONNECTOR` | `jarvis-memory-connector` | Connector id |
| `GOOGLE_APPLICATION_CREDENTIALS` | unset | Service account JSON (production) |
| `DATA_CONNECT_EMULATOR_HOST` | unset | Local emulator host:port |
| `AAIS_VECTOR_TENANT_ID` | `default` | Same tenant partition as Chroma/Scylla |

Copy [`deploy/firebase-data-connect/.env.example`](.env.example) into your environment.

Implementation:

- REST client: [`src/firebase_dataconnect_client.py`](../../src/firebase_dataconnect_client.py)
- Adapter: `FirebaseDataConnectVectorBackend` in [`src/memory_vector_store.py`](../../src/memory_vector_store.py)
- Smoke test: [`src/firebase_connection_test.py`](../../src/firebase_connection_test.py)

## Admission

Documented in
[`docs/contracts/MEMORY_VECTOR_BACKEND_FIREBASE_ADMISSION.md`](../../docs/contracts/MEMORY_VECTOR_BACKEND_FIREBASE_ADMISSION.md).

Parallel reference: [`deploy/scylladb/README.md`](../scylladb/README.md),
[`docs/contracts/MEMORY_VECTOR_BACKEND_ADMISSION.md`](../../docs/contracts/MEMORY_VECTOR_BACKEND_ADMISSION.md).

## Firebase MCP (optional)

The Firebase Cursor plugin exposes an MCP server. Enable it in Cursor → MCP settings
using the plugin's `.mcp.json` when `npx` / `firebase-tools` is on PATH.
