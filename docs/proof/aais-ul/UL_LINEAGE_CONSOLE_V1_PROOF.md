# UL Lineage Console v1 Proof Packet

Claim: CISIV Operator Lineage Console records governed runtime events across chat, memory, capability, and forge lanes into an inspectable UL lineage graph with read-only API and operator UI.

Claim status: **asserted** on one machine (single-machine MVP). Multi-hop fixture validation: **proven**.

## 1) Incident / Issue ID

- ID: `UL-LINEAGE-CONSOLE-V1`
- Title: CISIV Operator Lineage Console MVP
- Scope: `src/ul_lineage.py`, emitter hooks, API route, Jarvis console panel, drift/smoke extensions
- Severity: governance / operator visibility

## 2) Hypothesis And Root Cause

- Initial hypothesis: CISIV/UL coverage stops at individual chat turns; mission lifecycle is not traceable.
- Confirmed root cause: memory board, capability bridge, and forge paths lacked lineage emitters and operator-facing graph.
- Trigger: mission-bound session with chat, memory promotion, capability call, or forge handoff.

## 3) Reproduction Steps

1. Create a mission on the Mission Board.
2. Send chat turns / run capability actions with mission context.
3. `GET /api/jarvis/lineage/{mission_id}` or open Operator → CISIV Lineage panel.
4. Run lineage gate.

Expected: graph nodes append with CISIV stages; empty graph when no mission bound.

## 4) Fix Details

| Deliverable | Module |
|---|---|
| Lineage graph store | `src/ul_lineage.py` |
| Chat hook | `src/chat_turn_governance.py` |
| Capability hook | `src/capability_service_bridge.py` |
| Memory hook | `src/jarvis_operator.py` |
| Forge hook | `src/forge_repo_governance.py` |
| API | `GET /api/jarvis/lineage/<mission_id>` in `src/api.py` |
| UI | `LineageConsoleCard` in `frontend/src/pages/JarvisConsole.jsx` |
| Smoke/drift | `tools/ul/smoke.py --lineage-graph`, `tools/ul/drift --lane lineage` |

Deferred: full memory-path coverage, cross-machine replay.

## 5) Verification Evidence

### One-click override command

```bash
make lineage-gate
python -m pytest tests/test_ul_lineage.py -q
python -m tools.ul.smoke --lineage-graph tools/ul/fixtures/lineage_multi_hop.json --no-pytest
python -m tools.ul.drift --lane lineage
```

### Claim posture

| Claim | Label |
|---|---|
| Multi-hop fixture validates 4 node types | proven |
| End-to-end operator UI on all platforms | asserted |
| All memory paths board-governed | none_yet |

## 6) Sign-Off

- claim_label: asserted
- why_short: Single-machine MVP with proven multi-hop fixture validation; UI verified locally.
- proof_links:
  - docs/proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md
  - tests/test_ul_lineage.py
  - tools/ul/fixtures/lineage_multi_hop.json
- override_command: make lineage-gate
