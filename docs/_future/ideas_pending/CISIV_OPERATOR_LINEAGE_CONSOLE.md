# CISIV Operator Lineage Console

CISIV stage: **implementation** (MVP live — see [../../runtime/UL_LINEAGE_CONSOLE.md](../../runtime/UL_LINEAGE_CONSOLE.md))

Status: partial live — read-only lineage graph, API, operator UI. Proof: [../../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md](../../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md)

## 1. Purpose

Provide a **unified governance visibility layer** so operators can trace a
mission's full lifecycle across chat turns, memory promotions, capability bridge
calls, and forge handoffs — not only per-turn `cisiv_stage` on chat replies.

AAIS-UL and CISIV are proven on chat and forge paths
([UL_CISIV_PHASES_1_5_PROOF](../../proof/aais-ul/UL_CISIV_PHASES_1_5_PROOF.md)),
but Memory Board, Mission Board, and Capability Service Bridge remain partially
governed per [AAIS_SUBSYSTEM_SPEC.md](../../runtime/AAIS_SUBSYSTEM_SPEC.md).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

The Lineage Console is **read-only in v1**. It observes runtime envelopes; it
does not invent goals, mutate memory, or bypass law admission.

## 3. Non-Goals

- No new authority plane above Jarvis or Mission Board
- No write path from the UI in v1 (inspect only)
- No replacement for raw trace logs in `docs/contracts/AAIS_TRACING_PROTOCOL.md`
- No Super Nova or biometric input coupling

## 4. UL Lineage Graph

Schema: [schemas/ul_lineage_graph.v1.json](./schemas/ul_lineage_graph.v1.json)

Append-only DAG per mission or session:

| Node type | Source module |
|-----------|---------------|
| `chat_turn` | `src/chat_turn_governance.py` |
| `memory_promotion` | `src/jarvis_memory_board.py` |
| `capability_call` | `src/capability_service_bridge.py` |
| `forge_handoff` | `src/forge_repo_governance.py` |

Each node carries:

- `node_id`, `node_type`, `timestamp_utc`
- `cisiv_stage` at emission time
- `law_enforcement` snapshot (subset)
- `claim_label` where applicable

Edges link causal or temporal ordering with optional `drift_checked: true`.

## 5. Extended Drift / Smoke

Mirror existing tooling:

- `python -m tools.ul.drift`
- `python -m tools.ul.smoke`

Proposed extensions (structure stage):

- `python -m tools.ul.drift --lane memory_board`
- `python -m tools.ul.drift --lane capability_bridge`
- `python -m tools.ul.smoke --lineage-graph <path>`

Drift failure on any node MUST surface in the console as a visible regression
marker without blocking live chat (observe-only in v1).

## 6. Operator UI (Future)

Frontend panel in [../../../frontend/](../../../frontend/) — Jarvis console
sidebar:

- Timeline of nodes by `timestamp_utc`
- CISIV stage transitions per node
- Claim labels and law enforcement highlights
- Drift/smoke status badges

Proposed API route (implementation stage):

```text
GET /legacy_api/api/lineage/{mission_id}
```

## 7. Failsafe

- Missing mission or session → empty graph with explicit `claim_label: asserted`
- Partial lane coverage → graph renders available nodes; gaps labeled in UI
- Stale graph vs live state → `updated_at_utc` on graph root; operator refresh

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Lineage graph schema covers four node types | `asserted` | Schema + this document |
| Multi-hop fixture detects memory bypass regression | `none_yet` | Requires implementation |
| Frontend panel renders read-only timeline | `none_yet` | Requires implementation |
| Extended drift/smoke passes on fixture graph | `none_yet` | Requires structure stage |

Target proof packet: `docs/proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md` (not
yet created).

Doctrine addendum (structure stage): extend
[AAIS_UL_DOCTRINE.md](../../contracts/AAIS_UL_DOCTRINE.md) with lineage graph
rules.

## 9. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema |
| Identity | Node IDs tied to session + mission board keys |
| Structure | `src/ul_lineage.py` emitter hooks in memory board, capability bridge, chat governance |
| Implementation | API route + React panel |
| Verification | Drift/smoke on multi-hop fixture; stage regression detection proof |

## 10. Related

- [../../contracts/AAIS_UL_DOCTRINE.md](../../contracts/AAIS_UL_DOCTRINE.md)
- [../../runtime/AAIS_SUBSYSTEM_SPEC.md](../../runtime/AAIS_SUBSYSTEM_SPEC.md)
- [../../proof/aais-ul/UL_CISIV_PHASES_1_5_PROOF.md](../../proof/aais-ul/UL_CISIV_PHASES_1_5_PROOF.md)
- [../../../src/mission_board.py](../../../src/mission_board.py)

## 11. Activation Order Notes And Minimal Invariants

**Recommended activation order (batch):** 1 of 3 — activate first (most foundational)

**Depends on:** Mission Board, chat turn governance, CISIV/UL substrate (UL CISIV Phases 1–5 proven)

**Minimal invariants:**

- Read-only in v1 — graph observes runtime envelopes; no write path from UI
- Append-only DAG per mission — nodes never deleted or mutated in place
- Each node carries `cisiv_stage` at emission time and `claim_label` where applicable
- Missing mission → empty graph with explicit `claim_label: asserted`
- Drift failure surfaces as visible regression marker without blocking live chat
