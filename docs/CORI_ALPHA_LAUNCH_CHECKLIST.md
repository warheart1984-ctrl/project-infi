# CORI Alpha Launch Checklist

Final readiness checklist before the first governed mission runs end-to-end.

## A. Infrastructure

- [ ] Docker Compose up: FastAPI, PostgreSQL, Neo4j (if used by your deployment)
- [ ] Lawful Nova running on `:8080` (`nova-api` or `python -m nova.api`)
- [ ] AAIS running on `:8000` (`aais` launcher / `uvicorn app.main:app`)
- [ ] AAES mounted at `/aaes/execute` on AAIS shell
- [ ] Nexus ops-console running on `:4000`
- [ ] SQLite stores initialized:
  - `data/nova_panel_store.sqlite3` — schema in `fixtures/continuity/panel_store.sql`
  - `data/law-ledger.sqlite3` (or `LAW_LEDGER_PATH`) — schema in `fixtures/continuity/law_ledger.sql`
  - `data/continuity.sqlite3` (or `CONTINUITY_STORE_PATH`) — schema in `fixtures/continuity/continuity.sql`

## B. Identity + Stewardship

- [ ] Identity service operational (`src/kernel/identity_history.py`)
- [ ] Steward identity available to operator CLI / API payload
- [ ] `identity_bridge.get_current_identity()` returns snapshots
- [ ] T5 reference binding resolves via `reference_bridge.current_reference_binding()`

## C. Law Kernel

- [ ] Law ledger cache hydrated (`law_ledger_bridge.list_cached_laws()`)
- [ ] Founding laws seeded only if cache empty (Nova bootstrap)
- [ ] `introduced_by="nova"` tagging verified on Nova-origin laws
- [ ] `LAW_EVAL` emits correct payload via `call_lawful_nova()`

## D. URG

- [ ] `POST /legacy_api/api/ugr/mission/run` reachable
- [ ] `build_darz_receipt_from_urg()` generates DAR-Z bridge receipt
- [ ] Mission → AAES payload validated (`send_to_aaes()`)

## E. AAES

- [ ] `POST /aaes/execute` reachable
- [ ] Execution receipts generated with `execution_id` / `trace_id`
- [ ] Nexus module receives execution events

## F. Nexus OS

- [ ] `record_execution()` writes to Nexus execution ledger
- [ ] Ops-console **Governed AAES Executions** panel shows events
- [ ] `GET /api/nexus/executions` returns recent events

## G. Panels + Continuity

- [ ] `panel_store` write-through on emit (legacy tables + unified `panels`)
- [ ] Evidence factory emits full chain (`docs/CORI_ALPHA_EVIDENCE_FRAMEWORK.md`)
- [ ] Continuity events logged: identity, asset, evidence, validation, execution, panels
- [ ] Identity snapshots updated in `continuity.sqlite3`
- [ ] Asset registry populated (`assets` table)

## H. Runtime Governance Invariants

- [ ] `pytest tests/test_runtime_governance_invariants.py` passes (in-process, CI-safe)
- [ ] `CORI_LIVE_INVARIANTS=1 pytest tests/test_runtime_governance_invariants_live.py` passes (after live missions)
- [ ] No execution without validation (`aaes_exec` → `validation_decided` + `law_eval`)
- [ ] No validation without evidence (`validation_decided` → `evidence_attached`)
- [ ] Governed URG missions reference continuity `law_eval`
- [ ] Nova-introduced laws have ledger hash entries
- [ ] Panels reference execution ids from continuity

## I. Observability Dashboard

- [ ] `GET /dashboard/health` — store paths present
- [ ] `GET /dashboard/missions` returns mission stream (array)
- [ ] `GET /dashboard/trace/{mission_id}` returns full constitutional trace
- [ ] `GET /dashboard/invariants` shows traffic-light status
- [ ] `POST /dashboard/invariants/run` updates `invariant_status` table

## J. End-to-End Test

- [ ] `pytest tests/test_e2e_governed_mission.py` passes
- [ ] CLI works:

  ```bash
  python cli/cori.py mission "test governed mission"
  ```

- [ ] Full trace returned with:
  - `law_eval`
  - `urg_receipt`
  - `aaes_receipt` (`execution_id`)
  - `nexus_event` (`event_type: execution`)

## Recommended order

1. **Run governed missions** — `cori mission "..."` or `POST /governed/mission`
2. **Invariant tests (CI / isolated)** — `pytest tests/test_runtime_governance_invariants.py -q`
3. **Invariant tests (live DBs)** — `CORI_LIVE_INVARIANTS=1 pytest tests/test_runtime_governance_invariants_live.py -q`
4. **Dashboard** — `GET /dashboard/missions`, `/dashboard/trace/{mission_id}`, `POST /dashboard/invariants/run`
5. **Automate in CI** — both invariant test modules on every commit

## Quick verification commands

```bash
# Governed mission (HTTP)
curl -s -X POST http://127.0.0.1:8000/governed/mission \
  -H "Content-Type: application/json" \
  -d '{"text":"Evaluate continuity of asset X","operator_id":"operator-demo"}'

# Nexus executions
curl -s http://127.0.0.1:8000/api/nexus/executions

# CORI dashboard
curl -s http://127.0.0.1:8000/dashboard/missions
curl -s -X POST http://127.0.0.1:8000/dashboard/invariants/run

# Ops-console Nexus executions (shared ledger with AAIS when NEXUS_EXECUTION_LEDGER_PATH is set)
curl -s http://127.0.0.1:4000/api/nexus/executions | jq '.executions'
```

## Environment flags (local / CI without live HTTP)

| Variable | Effect |
|----------|--------|
| `GOVERNED_NOVA_IN_PROCESS=1` | In-process Lawful Nova |
| `GOVERNED_URG_IN_PROCESS=1` | In-process URG mission runtime |
| `GOVERNED_AAES_IN_PROCESS=1` | In-process AAES orchestrator |
| `NOVA_PANEL_STORE_PATH` | Panel SQLite path |
| `LAW_LEDGER_PATH` | Law ledger SQLite path |
| `CONTINUITY_STORE_PATH` | Continuity SQLite path |
| `NEXUS_EXECUTION_LEDGER_PATH` | Nexus execution JSONL ledger |

## OpenAPI

See `docs/openapi_governed_mission.yaml` for the operator-facing contract.

## Future CI coverage (not yet automated)

- **Distributed UGR mesh** (`deploy/ugr/docker-compose.yml`, ports 8090–8099) is not part of the CORI CI spine. Governed missions currently use in-process or AAIS-hosted URG (`/legacy_api/api/ugr/mission/run`), not the mesh services.
