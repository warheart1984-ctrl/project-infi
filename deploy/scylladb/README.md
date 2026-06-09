# ScyllaDB Memory Board Vector Projection

Optional cloud vector backend for governed Jarvis Memory Board retrieval.
Chroma remains the default local backend (`AAIS_VECTOR_BACKEND=chroma`).

## Prerequisites

1. [ScyllaDB Cloud](https://cloud.scylladb.com/) cluster with **Vector Search** enabled
2. Client IP allowlisted in the cluster Connect tab
3. Python driver: `pip install scylla-driver` (see `requirements-advanced.txt`)

## Setup

1. Copy [`deploy/scylladb/.env.example`](.env.example) values into your environment
2. Apply schema: `cqlsh` or Cloud Console CQL editor → run [`schema.cql`](schema.cql)
3. Set `AAIS_VECTOR_BACKEND=scylladb`
4. Verify connection:

```bash
python -m src.scylla_connection_test
```

Expected output includes a `release_version` from `system.local`.

## DC-aware driver requirement

Vector Search requires DC-aware load balancing. The datacenter name must match
the Cloud Console value exactly (e.g. `AWS_US_EAST_1`, not `us-east-1`).

## Admission

This backend is an optional query projection documented in
[`docs/contracts/MEMORY_VECTOR_BACKEND_ADMISSION.md`](../../docs/contracts/MEMORY_VECTOR_BACKEND_ADMISSION.md).
JSONL operator receipts remain the accountability write authority.
