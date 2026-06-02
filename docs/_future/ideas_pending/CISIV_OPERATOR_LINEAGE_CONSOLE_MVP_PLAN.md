# CISIV Operator Lineage Console — MVP Plan

CISIV stage: concept → implementation target

Status: **implemented (partial live)** — see [../../runtime/UL_LINEAGE_CONSOLE.md](../../runtime/UL_LINEAGE_CONSOLE.md)

Concept origin: [./CISIV_OPERATOR_LINEAGE_CONSOLE.md](./CISIV_OPERATOR_LINEAGE_CONSOLE.md)

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| Graph store | `src/ul_lineage.py` | Append-only DAG per mission |
| Persistence | `.runtime/lineage/<mission_id>/ul_lineage_graph.v1.json` | Schema-validated writes |
| API | `GET /api/jarvis/lineage/<mission_id>` | Read-only |
| UI | `LineageConsoleCard` in `frontend/src/pages/JarvisConsole.jsx` | Operator sidebar panel |
| Schema | `schemas/ul_lineage_graph.v1.json` | Four node types |
| Smoke/drift | `tools/ul/smoke.py`, `tools/ul/drift.py` | `--lineage-graph`, `--lane lineage` |

## 2. Code Artifacts

- `src/ul_lineage.py` — graph store and persistence
- `src/chat_turn_governance.py` — `chat_turn` emitter hook
- `src/capability_service_bridge.py` — `capability_call` emitter hook
- `src/jarvis_operator.py` — `memory_promotion` emitter hook
- `src/forge_repo_governance.py` — `forge_handoff` emitter hook
- `src/api.py` — lineage API route
- `frontend/src/pages/JarvisConsole.jsx` — `LineageConsoleCard`
- `.github/scripts/check-lineage-governance.py` — governance gate

## 3. Tests

- `tests/test_ul_lineage.py` — graph append, schema validation, node types, empty graph handling

## 4. Fixtures

- `tools/ul/fixtures/lineage_multi_hop.json` — multi-hop scenario covering chat, memory, capability, and forge nodes

## 5. Gates

| Gate | Script | Sequence |
|------|--------|----------|
| `make lineage-gate` | `.github/scripts/check-lineage-governance.py` | pytest → lineage smoke → drift lane check |

## 6. Proof Bundle

Target: [../../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md](../../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md)

| Claim | Label | Evidence |
|-------|-------|----------|
| Multi-hop fixture validates 4 node types | `proven` | `tools/ul/fixtures/lineage_multi_hop.json` |
| End-to-end operator UI on all platforms | `asserted` | Local UI verification |
| All memory paths board-governed | `none_yet` | Deferred full memory-path coverage |

## 7. Reproduction Commands

```bash
make lineage-gate
python -m pytest tests/test_ul_lineage.py -q
python -m tools.ul.smoke --lineage-graph tools/ul/fixtures/lineage_multi_hop.json --no-pytest
python -m tools.ul.drift --lane lineage
```

## 8. Activation Dependencies

**Existing subsystems required:** Mission Board, chat turn governance, CISIV/UL substrate (proven in UL CISIV Phases 1–5)

**Order among batch:** 1 of 3 (most foundational — governance visibility layer)

**Rationale:** Lineage Console observes runtime envelopes across lanes; no dependency on Triangulation or NTP. Should activate first in a batch because it provides operator visibility for subsequent subsystem debugging.
