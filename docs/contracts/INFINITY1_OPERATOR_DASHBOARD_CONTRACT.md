# Infinity-1 Operator Dashboard Contract

Authority: [UGR_OPERATOR_CONSOLE_CONTRACT.md](./UGR_OPERATOR_CONSOLE_CONTRACT.md), [SEAM_LAW.md](./SEAM_LAW.md)

## Scope

Unified operator landing at `/operator` — seam health, workflow stack, accountability readouts, plus embedded UGR advisory panels.

- Backend: `src/operator_infinity1_dashboard.py`
- Console embed: `infinity1` key on `GET /api/operator/console` (console v1.2)
- Poll: `GET /api/operator/dashboard/seam-health`
- UI: `frontend/src/pages/OperatorConsole.jsx` + `frontend/src/components/operator/*`

## Version

- Dashboard snapshot version: **1.1**
- Console wrapper version: **1.2**

## Invariants

1. `runtime_effect: readout_only` — dashboard never mutates runtime
2. Seam stress data prefers `ci-artifacts/seam_discovery_report.json` when live probe unavailable
3. Brain readouts remain `proposal_only` — no execute authority
4. Ledger digest is read-only aggregate from operator decision ledger store
5. Workflow stack gate list is static documentation — no shell-out in request path

## Snapshot keys (`infinity1`)

| Key | Source |
|-----|--------|
| `health` | Live `/health` probe or seam artifact fallback |
| `seam_stress` | `ci-artifacts/seam_discovery_report.json` summary |
| `live_stress` | `ci-artifacts/live_stress_report.json` summary |
| `ledger_digest` | `operator_decision_ledger_store.build_digest_summary("global")` |
| `brain` | `brain_session_store.list_sessions()` aggregates |
| `plugins` | `plug_adapter_runtime.registry_snapshot()` counts |
| `workflow_stack` | Static gate manifest + claim from seam closure |
| `quick_links` | Operator surface deep links |
| `monitoring` | Sentinel + Cloud Forge rail + mesh poll alerts |

## Surfaces

| Surface | Path |
|---------|------|
| Full dashboard | `/operator` |
| Console snapshot | `GET /api/operator/console` → `infinity1` |
| Seam health poll | `GET /api/operator/dashboard/seam-health` |
| Monitoring poll | `GET /api/operator/dashboard/monitoring` |

## Verification

```bash
pytest tests/test_operator_infinity1_dashboard.py tests/test_ugr_operator_console.py -q
python tools/stress/seam_discovery_stress.py --offline
```

Evidence: [INFINITY1_OPERATOR_DASHBOARD_V1_PROOF.md](../proof/platform/INFINITY1_OPERATOR_DASHBOARD_V1_PROOF.md)
