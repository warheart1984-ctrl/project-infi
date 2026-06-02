# UL Lineage Console

Status: **partial live** — MVP implementation with read-only API and operator UI.

CISIV stage: **implementation** (verification proof: `docs/proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md`)

## Purpose

Unified governance visibility for mission lifecycles: chat turns, memory promotions, capability bridge calls, and forge handoffs in one UL lineage graph.

## Runtime

| Surface | Location |
|---------|----------|
| Graph store | `src/ul_lineage.py` |
| Persistence | `.runtime/lineage/<mission_id>/ul_lineage_graph.v1.json` |
| API | `GET /api/jarvis/lineage/<mission_id>` |
| UI | `LineageConsoleCard` in `frontend/src/pages/JarvisConsole.jsx` |
| Schema | `schemas/ul_lineage_graph.v1.json` |
| Gate | `make lineage-gate` |

## Emitter hooks

- `src/chat_turn_governance.py` — `chat_turn`
- `src/capability_service_bridge.py` — `capability_call`
- `src/jarvis_operator.py` — `memory_promotion`
- `src/forge_repo_governance.py` — `forge_handoff`

## Verification

```bash
make lineage-gate
python -m tools.ul.smoke --lineage-graph tools/ul/fixtures/lineage_multi_hop.json --no-pytest
```

## Related

- Concept origin: [../_future/ideas_pending/CISIV_OPERATOR_LINEAGE_CONSOLE.md](../_future/ideas_pending/CISIV_OPERATOR_LINEAGE_CONSOLE.md)
- Proof: [../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md](../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md)
