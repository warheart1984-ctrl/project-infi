# UGR Operator Console Contract

Authority: `docs/TRUST_BUNDLE_SPEC.md`, `docs/programs/UGR_CLOUD_PROGRAM.md`

## Scope

Jarvis-style **advisory** operator console for UGR + Cloud Forge:

- Backend snapshot: `src/ugr/operator_console/`
- API: `GET /api/operator/console`
- Workbench: `operator_console` key on `GET /api/jarvis/workbench`
- UI: `/operator` page + Jarvis side panel card

## Version

- Console snapshot version: **1.1**
- Adds live mesh health polling, deliberation trace viewer, Forge platform dashboard JSON

## Invariants

1. `runtime_effect: readout_only` — console never mutates runtime
2. `claim_status` reflects trust bundle + debt evidence (`asserted` vs `proven`)
3. Debt register surfaces UGR-D* and CF-D5 items
4. Cloud Forge readout uses `build_cloud_forge_readout` when available
5. Mesh health polls are advisory HTTP GETs only; no mesh mutation

## Surfaces

| Surface | Path |
|---|---|
| Full page | `/operator` |
| Jarvis side panel | Operator tab → UGR + Cloud Forge card |
| Full snapshot | `GET /api/operator/console` |
| Mesh health poll | `GET /api/operator/console/mesh-health` |
| Trace viewer | `GET /api/operator/console/traces?limit=20&trace_id=<optional>` |
| Forge platform | `GET /api/operator/console/forge-platform?live=0` |

## Snapshot keys (v1.1)

| Key | Source |
|---|---|
| `mesh_health` | `poll_mesh_health()` |
| `deliberation_traces` | `load_deliberation_traces()` from `{runtime}/ugr/traces.jsonl` |
| `forge_platform` | `load_forge_platform_dashboard()` via `forge-platform-dashboard.py --json` |

## Verification

```bash
make ugr-operator-console-gate
```

Evidence: `docs/proof/ugr/UGR_OPERATOR_CONSOLE_PROOF.md`
