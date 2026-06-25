# Constitutional runtime versions

Nova and `src/` each ship a constitutional runtime path. They share substrate ledgers in `src/continuity/` but expose different operator surfaces.

## v0.1 — Flask substrate runtime (`src/`)

- **Entry:** `src/api.py` Flask app (`from src.api import app`)
- **Cockpit:** `src/constitutional_cockpit_routes.build_cockpit_summary()` — law/evidence/comprehension spine + CRK-T2 boundary loop + CRK-T5 reference metrics
- **Law ledger:** SQLite `src/continuity/law_ledger.py` (`LawLedgerStore`)
- **Epochs:** `src/continuity/epoch_engine.run_epoch_cycle()`
- **Boundary:** `src/kernel/boundary_service.get_boundary_loop().snapshot()`
- **Identity / reference:** `src/kernel/identity_history.py`, `src/kernel/reference_service.py`

Use v0.1 when running the full Jarvis operator stack, constitutional cockpit API tests, and epoch simulation.

## v0.2 — Nova lawful cortex (`nova/`)

- **Entry:** `nova/api.py` (FastAPI `/v1/chat`) and `nova/lawful_llm.py`
- **Law kernel:** in-memory `nova/law_kernel/` with PIT transforms, capability ladders, T5 binding (reads src reference metrics when available)
- **Cockpit v2:** `nova/crk/cockpit/summary_builder.py` — panel aggregation for HUD; boundary now bridged to src CRK-T2 via `nova/bridges/boundary_bridge.py`
- **Governance:** steward proposals/ratifications (`nova/governance/`)
- **Continuity:** DriftGuard + RIL export/replay (`nova/continuity/`) with deep replay in `nova/continuity/replay.py`
- **Cortex routing:** `nova/cortex/` lawful intent router; formal cog_runtime available through `nova/bridges/cortex_bridge.py`

Use v0.2 for lawful LLM turns, continuity seal CI, omega harness, and cockpit v2/HUD aggregation.

## Bridge layer (`nova/bridges/`)

| Bridge | src backing | Nova consumer |
|--------|-------------|---------------|
| `law_ledger_bridge` | `LawLedgerStore` SQLite | Law kernel cache / persistence |
| `boundary_bridge` | `get_boundary_loop().snapshot()` | Cockpit v2 `boundary_detection` |
| `identity_bridge` | `IdentityHistory.current()` | HUD identity plane |
| `reference_bridge` | `get_reference_evaluator()` | T5 binding without silent default |
| `continuity_bridge` | epochs + RIL export/replay | DriftGuard deep replay |
| `cockpit_bridge` | `build_cockpit_summary()` v1 | Transitional v2 normalization |
| `cortex_bridge` | `cog_runtime` planning/execution | Formal cortex spec path |

## Recommended product entry

Keep **Flask `src/api` as primary** for operator chat and substrate control. Mount or proxy Nova lawful paths (`/v1/chat`, `/api/cockpit/summary` v2) where HUD and lawful LLM are required. Bridges avoid duplicating SQLite and kernel state.

## Migration notes

1. Wire panel persistence through `law_ledger_bridge` and steward SQLite (future).
2. Phase out `cockpit_bridge` once HUD fully replaces v1 summary shape.
3. Unify epoch IDs: src uses integer epochs; Nova HUD uses `EPOCH:{n}:T0` strings — map in `continuity_bridge.list_epochs()`.
