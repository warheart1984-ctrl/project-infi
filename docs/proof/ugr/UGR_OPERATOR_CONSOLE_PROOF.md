# UGR Operator Console Proof

Claim status: **asserted** (local unit tests + manifest gate on Windows)

## Verification

```bash
make ugr-operator-console-gate
curl http://127.0.0.1:5000/api/operator/console
curl http://127.0.0.1:5000/api/operator/console/mesh-health
curl "http://127.0.0.1:5000/api/operator/console/traces?limit=20"
curl http://127.0.0.1:5000/api/operator/console/forge-platform
```

## Console v1.1 surfaces

- Live mesh health poll: `GET /api/operator/console/mesh-health`
- Deliberation trace viewer: `GET /api/operator/console/traces`
- Forge platform dashboard JSON: `GET /api/operator/console/forge-platform`

## Artifacts

- `src/ugr/operator_console/snapshot.py` (console_version 1.1)
- `src/ugr/operator_console/mesh_health.py`
- `src/ugr/operator_console/trace_viewer.py`
- `src/ugr/operator_console/forge_platform.py`
- `GET /api/operator/console`
- `frontend/src/pages/OperatorConsole.jsx`
- `frontend/src/components/operator/UGRCloudForgeConsoleCard.jsx`
