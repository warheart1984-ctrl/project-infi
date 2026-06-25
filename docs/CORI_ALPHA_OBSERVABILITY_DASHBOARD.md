# CORI Alpha Observability Dashboard

One dashboard surface that shows CORI as a governed organism—not just CPU and HTTP 200s.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  AAIS FastAPI (:8000)                                   │
│  /dashboard/*  ← src/cori/dashboard_api.py              │
└────────────┬────────────────────────────────────────────┘
             │ reads
   ┌─────────┼─────────┬──────────────────┐
   ▼         ▼         ▼                  ▼
continuity  panel    law_ledger    nexus_executions
.sqlite3    _store    .sqlite3      .jsonl
```

Mounted in `app/main.py` via `cori_dashboard_router`.

## API endpoints

| Route | Purpose |
|-------|---------|
| `GET /dashboard/missions` | Governed mission stream |
| `GET /dashboard/trace/{mission_id}` | Constitutional trace inspector |
| `GET /dashboard/law_kernel` | Law kernel health |
| `GET /dashboard/evidence_density` | Per-asset evidence coverage |
| `GET /dashboard/invariants` | Traffic-light invariant status |
| `POST /dashboard/invariants/run` | Re-run invariant suite and persist |

### Governed mission stream

Columns: `time`, `steward`, `mission_id`, `law_eval_id`, `aaes_exec_id`, `nexus_event_id`, `status`

```bash
curl -s http://127.0.0.1:8000/dashboard/missions | jq
```

### Constitutional trace inspector

Select a mission → returns identity snapshots, law_eval, URG, validation, AAES, Nexus, evidence chain, and matching panels.

```bash
curl -s http://127.0.0.1:8000/dashboard/trace/<mission_id> | jq
```

### Law kernel health

- Laws grouped by `introduced_by`
- Recent `law_eval` count from continuity
- Fitness summary from `law_fitness_history`

```bash
curl -s http://127.0.0.1:8000/dashboard/law_kernel | jq
```

### Evidence density & coverage

Per asset: evidence count, last validation, last execution.

```bash
curl -s http://127.0.0.1:8000/dashboard/evidence_density | jq
```

### Invariant status

Traffic-light indicators backed by `invariant_status` table in `continuity.sqlite3`.

```bash
curl -s http://127.0.0.1:8000/dashboard/invariants | jq
curl -s -X POST http://127.0.0.1:8000/dashboard/invariants/run | jq
```

## Frontend sketch

Recommended static or lightweight SPA routes:

| Path | View |
|------|------|
| `/dashboard/missions` | Sortable mission stream table |
| `/dashboard/trace/{mission_id}` | Multi-panel trace inspector |
| `/dashboard/law_kernel` | Law count + fitness sparklines |
| `/dashboard/invariants` | Green/red cards per invariant |

**Option A — extend ops-console** (`aaes-os/services/ops-console`): add tabs that poll `/dashboard/*` alongside existing `/telemetry`.

**Option B — HTMX shell**: server-rendered tables from the same FastAPI routes with `Accept: text/html` templates (future).

**Option C — Constitutional Cockpit** (`frontend/src/pages/ConstitutionalCockpit.jsx`): add a "CORI Alpha" section linking mission stream + invariants.

## Data sources

| View | Primary source |
|------|----------------|
| Mission stream | `continuity_events` (`urg_mission`, `aaes_exec`, `nexus_event`) |
| Trace inspector | `continuity.sqlite3` + `panel_store.sqlite3` |
| Law kernel | `law_ledger.sqlite3` + continuity `law_eval` events |
| Evidence density | `assets` table + `continuity_events` filtered by `asset_id` |
| Invariants | `invariant_status` updated by `GovernanceInvariantChecker` |

## Invariant integration

Invariant definitions live in `src/cori/governance_invariants.py`. Tests in `tests/test_runtime_governance_invariants.py` should run in CI; optionally call `POST /dashboard/invariants/run` after deploy smoke tests to refresh the dashboard.

## Related

- Evidence framework: `docs/CORI_ALPHA_EVIDENCE_FRAMEWORK.md`
- Launch checklist: `docs/CORI_ALPHA_LAUNCH_CHECKLIST.md`
