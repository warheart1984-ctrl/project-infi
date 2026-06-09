# Organ Mesh V1 Proof

Status: **Release 35 / Anatomical Stage 4**

## Scope

Governed sequential multi-organ mesh runs with mediated handoffs, Jarvis authorization, ledger receipts, and brain accept → approval enqueue (no auto-execute).

## Contract

- [ORGAN_COORDINATION_CONTRACT.md](../../contracts/ORGAN_COORDINATION_CONTRACT.md)
- Schemas: `organ_handoff.v1`, `organ_mesh_run.v1`

## Modules

| Module | Role |
|--------|------|
| `src/organ_coordination_runtime.py` | Plan (OCC-0) and execute sequential handoffs |
| `src/jarvis_organ_mesh_authority.py` | Jarvis gate before execution |
| `src/organ_mesh_approval_bridge.py` | Brain accept → workflow approval enqueue |
| `src/workflow_family_registry.py` | Handoff graph + `validate_handoff_graph()` |

## APIs

| Route | Behavior |
|-------|----------|
| `GET /api/operator/organs/mesh` | Handoff graph + readiness overlay |
| `POST /api/operator/organs/mesh/plan` | OCC-0 dry plan |
| `POST /api/operator/organs/mesh/runs` | Governed run (403 without Jarvis auth) |
| `GET /api/operator/organs/mesh/runs/<run_id>` | Run timeline |

## Seed handoff graph

- `knowledge_work` → `creative_workflows` (`research_brief` → `creative_asset_package`)
- `knowledge_work` → `business_workflows` (`compliance_memo` → `contract_redline`)
- `data_workflows` → `knowledge_work` (`data_cleanup` → `research_brief`)
- `operational_workflows` → `business_workflows` (`incident_triage` → `support_resolution`)

## Verification

```bash
make organ-mesh-gate
python -m pytest tests/test_organ_coordination_plan.py tests/test_organ_coordination_execute.py -q
```

## Success criteria

- Two-organ mesh dry-run completes with handoff envelope + ledger receipt per step
- Mesh run without Jarvis authorization returns 403
- Brain accept enqueues mesh approval; does not auto-execute
- Somatic panel exposes `active_mesh_runs` and `blocked_handoffs`

## Limitations (Release 36+)

- DAG / parallel organ branches deferred
- Cross-machine organ mesh out of scope
