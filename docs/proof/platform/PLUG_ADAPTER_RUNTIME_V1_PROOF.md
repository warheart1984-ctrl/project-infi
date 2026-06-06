# Plug Adapter Runtime v1 Proof

Status: **prototype proof**

CISIV stage: **implementation**

## Claim

AAIS discovers MCP tools, Cursor skills, and native capability routes; catalogs them under
`plug_adapter.v1` contracts; exposes operator control at `/operator/plugins`; and routes
enabled plugs through governed execution with UL wrapping and operator decision ledger receipts.

## Evidence

| Check | Command | Expected |
|-------|---------|----------|
| Spec gate | `make plug-adapter-spec-gate` | PASS |
| Runtime gate | `make plug-adapter-gate` | PASS (9 tests) |
| Discovery | `pytest tests/test_plug_discovery.py -q` | PASS |
| Registry | `pytest tests/test_plug_adapter_runtime.py -q` | PASS |
| MCP bridge | `pytest tests/test_mcp_bridge.py -q` | PASS |
| Jarvis attach | `pytest tests/test_plug_bridge_jarvis.py -q` | PASS |

## Surfaces verified

- `GET /api/operator/plugins`
- `POST /api/operator/plugins/rescan`
- `PATCH /api/operator/plugins/<plug_id>`
- `POST /api/operator/plugins/<plug_id>/execute`
- `GET /api/jarvis/plug-bridge/status`
- `/operator/plugins` UI route

## Non-goals (v1)

- Live MCP server launch for all Cursor plugins (requires `governance/mcp_server_manifest.v1.json` operator config)
- Auto-execution of Cursor skill bodies

## Related

- [PLUGIN_GOVERNANCE_CONTRACT.md](../../contracts/PLUGIN_GOVERNANCE_CONTRACT.md)
- [PLUG_ADAPTER_RUNTIME.md](../../_future/ideas_pending/PLUG_ADAPTER_RUNTIME.md)
