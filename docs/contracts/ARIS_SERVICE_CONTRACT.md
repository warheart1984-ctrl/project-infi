# ARIS Service Contract

Status: **active contract**

## Modes

| Mode | Behavior |
|------|----------|
| `embedded` | Default — `aris_integration` via cognitive bridge |
| `standalone` | FastAPI sidecar at `ARIS_SERVICE_URL` (default `http://127.0.0.1:8791`) |
| `dual` | Standalone first with embedded fallback |

## Standalone Service

- `GET /health` — liveness
- `POST /v1/admit` — admission envelope compatible with bridge packets

## Authority

Embedded profile remains the AAIS authority spine. Standalone service is an admission/truth worker, not a parallel executor.
