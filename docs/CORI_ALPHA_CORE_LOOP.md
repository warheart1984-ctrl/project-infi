# CORI Alpha — `/v1/runtime/core-loop`

Canonical Alpha orchestration contract: **0001 → 1000 → 1001** governed loop.

## Endpoint

```
POST /v1/runtime/core-loop
```

## Request

```json
{
  "email": "steward@example.com",
  "display_name": "Test Steward",
  "asset": {
    "type": "document",
    "name": "Test Asset",
    "metadata": {"category": "example"}
  },
  "evidence": {
    "kind": "upload",
    "uri": "s3://bucket/object",
    "hash": "deadbeef"
  }
}
```

## Response

```json
{
  "subject_id": "uuid",
  "asset_id": "uuid",
  "evidence_id": "uuid",
  "validation_id": "uuid",
  "decision": "approved",
  "audit_id": "uuid"
}
```

`decision` is one of `approved`, `rejected`, or `pending`.

## Execution sequence

1. **Identity** — register or resolve `subject_id` by email
2. **Asset** — create asset owned by subject
3. **Evidence** — attach evidence referencing asset
4. **Validation** — immediate Alpha decision (`alpha.core-loop.v1`)
5. **Audit** — append audit record with SHA-256 `loop_hash`
6. **Response** — return `CoreLoopResponse`

## Implementation

| Layer | Path |
|-------|------|
| API router | `src/runtime/api.py` |
| Orchestrator | `src/runtime/core_loop.py` |
| Pydantic contracts | `src/runtime/schemas.py` |
| SQLAlchemy models | `src/runtime/models.py` |
| Database | `src/runtime/database.py` |
| Services | `src/runtime/services/` |

Default database: `data/runtime_core.db` (`RUNTIME_DATABASE_URL` override).

## Tests

```bash
pytest tests/test_runtime_core_loop.py -q
```

## curl

```bash
curl -s -X POST http://127.0.0.1:8000/v1/runtime/core-loop \
  -H "Content-Type: application/json" \
  -d '{"email":"steward@example.com","display_name":"Steward","asset":{"type":"document","name":"Doc","metadata":{}},"evidence":{"kind":"upload","uri":"s3://bucket/obj","hash":"deadbeef"}}'
```
