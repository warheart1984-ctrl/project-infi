# Memory Runtime Organ

CISIV stage: **concept**

Status: pending — Alt-5 summon wave 2 `alt5-summon-wave-2-2026-06`.

## 1. Purpose

Formalize the **Memory Runtime** (`cognitive.memory`) from
[NOVA_CORTEX.md](../../runtime/NOVA_CORTEX.md) as a governed Alt-5 organ distinct
from the Jarvis Memory Board governance fabric: bounded episodic/semantic recall
law exposed as a read-only organ snapshot.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Subordinate to Jarvis routing and
[JARVIS_MEMORY_BOARD_DOCTRINE.md](../../contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md)
(slot governance is separate).

## 3. Non-Goals

- No slot install or controller approval in this organ (see `jarvis_memory_board`)
- No unbounded RAG or document intelligence in v1
- No override of reflection or deliberation lobes

## 4. Organ Contract

Schema: [schemas/memory_runtime_organ.v1.json](./schemas/memory_runtime_organ.v1.json)

| Field | Role |
|-------|------|
| `runtime_id` | `cognitive.memory` |
| `stages` | Memory compression stages from live spec |
| `summary` | Bounded hippocampus-style recall |

## 5. Runtime (Proposed)

- `GET /api/jarvis/memory-runtime/status` — read-only spec snapshot
- `src/memory_runtime_organ.py` — wraps `memory_runtime_spec()`

## 6. Failsafe

Organ exports spec only; live memory mutations remain inside cog runtime sessions.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns memory snapshot | `none_yet` | Requires MVP |
| Distinct from Jarvis Memory Board gene | `none_yet` | Requires verification |

Target proof packet: `docs/proof/cognitive_runtime/MEMORY_RUNTIME_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/memory_runtime_organ.py` stub |
| Implementation | API route + gate |
| Verification | V1 proof + `make memory-runtime-gate` |

## 9. Related

- [NOVA_CORTEX.md](../../runtime/NOVA_CORTEX.md)
- [JARVIS_MEMORY_BOARD.md](./JARVIS_MEMORY_BOARD.md)
- [REFLECTION_RUNTIME_ORGAN.md](./REFLECTION_RUNTIME_ORGAN.md)

## 10. Activation Order

**Batch:** `alt5-summon-wave-2-2026-06` — order **2** (after Reflection Runtime Organ)

**Depends on:** `reflection_runtime_organ`, Nova cortex registration

**Minimal invariants:**

- Read-only v1 — organ does not install memory board slots
- runtime_id remains `cognitive.memory`
- Memory law invariants from live spec referenced in snapshot
