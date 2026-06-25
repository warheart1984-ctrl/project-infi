# Redundancy Contract (RLS-01)

Every subsystem admitted in rebuild stage 1 documents three paths:

| Field | Meaning |
|-------|---------|
| `primary_path` | Preferred production route |
| `fallback_path` | Degraded but functional route |
| `safe_mode_path` | Fail-closed or minimal surface |

## Subsystems (stage 1)

### Default chat

| Path | Route |
|------|-------|
| primary_path | `nova_chat_adapter.generate_turn` → `LawfulLLM.ask` |
| fallback_path | `LEGACY_CHAT_GENERATION=1` → `_generate_chat_response` |
| safe_mode_path | `GovernanceViolationError` → HTTP 403 with RSL payload |

### Organ status HTTP

| Path | Route |
|------|-------|
| primary_path | `jarvis_organ_status_registry` static handlers |
| fallback_path | (none in stage 1) |
| safe_mode_path | HTTP 500 with `organ_status_unavailable` |

### Story Forge / Movie Renderer

| Path | Route |
|------|-------|
| primary_path | `story_forge/redundant_pipeline.py` (stub exporters) |
| fallback_path | Lane organ status endpoints (legacy, until pruned) |
| safe_mode_path | No-op export + logged `safe_mode` flag |

### OTEM execution substrate

| Path | Route |
|------|-------|
| primary_path | `operator_task_execution_mode.detect_otem` (scaffold) |
| fallback_path | `heuristic_plan` |
| safe_mode_path | `safe_operator_restoration_mode` |

## Chat path exclusion

OTEM ceiling, slingshot, mechanic, and composed-turn blocks are **not** on the default chat path in stage 1. They remain behind `JARVIS_ACTION_TURN=1` / `JARVIS_LEGACY_BRIDGE=1` for action surfaces only.
