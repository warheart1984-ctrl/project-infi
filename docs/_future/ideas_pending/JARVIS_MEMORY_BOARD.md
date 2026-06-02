# Jarvis Memory Board

CISIV stage: **concept**

Status: pending — not yet integrated into active AAIS doc tree as a first-class subsystem family.

## 1. Purpose

Formalize the **seeded memory-governance fabric** in
[`src/jarvis_memory_board.py`](../../../src/jarvis_memory_board.py) as a governed
subsystem family: fixed-purpose slots, controller-approved installs, lawful
migration, and board snapshots consumable by lineage and operator surfaces.

Live reference behavior exists (`GET /api/jarvis/memory/board`); this admission
aligns doctrine, schema, genome, and proof posture for Alt-4 promotion.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation > Pipeline > Tool

Canonical doctrine: [JARVIS_MEMORY_BOARD_DOCTRINE.md](../../contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md).
The memory controller is the sole approval path for slot install or swap.

## 3. Non-Goals

- No flat undifferentiated memory bank
- No direct slot install without `controller_approved`
- No trust-class downgrade during migration
- No replacement for conversation RAG or document intelligence subsystems

## 4. Board Contract

Schema: [schemas/jarvis_memory_board.v1.json](./schemas/jarvis_memory_board.v1.json)

| Component | Role |
|-----------|------|
| `MemorySlot` | Fixed `accepted_class`; one active module |
| `MemoryModule` | Installable card with `supported_slot` binding |
| `MemoryController` | Approve install, swap, migration |
| `MigrationRecord` | Lawful moves preserving trust class |
| `build_memory_board_snapshot` | Operator/API snapshot builder |

Default slot families (implementation reference): foundation, operational, session,
archive, signal, preference — see doctrine for canonical card ids.

## 5. Snapshot And API Integration

| Surface | Path |
|---------|------|
| Live snapshot | `build_memory_board_snapshot(controller)` |
| Operator API | `GET /api/jarvis/memory/board` |
| Lineage node type | `memory_promotion` → [CISIV_OPERATOR_LINEAGE_CONSOLE.md](./CISIV_OPERATOR_LINEAGE_CONSOLE.md) |
| Regression tests | `tests/test_jarvis_memory_board.py` |

## 6. Migration And Failsafe Rules

- Slot purpose is immutable — upgrades swap modules, not slot class
- Occupied slot rejects direct install; controller swap required
- Inactive or reserved slots reject install with `MemoryBoardViolation`
- Migration without `trust_class_preserved` is rejected at controller boundary

## 7. Failsafe

- Controller rejection surfaces explicit violation text; no partial silent install
- Empty board snapshot still returns schema-valid envelope with `claim_label: asserted`
- Retired modules remain in slot history for audit; never deleted in place

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers slots, controller state, and migration records | `asserted` | Schema + doctrine + this document |
| API board snapshot matches controller state | `none_yet` | Requires verification gate |
| All memory promotion paths emit lineage nodes | `none_yet` | Requires implementation |
| Dedicated governance gate passes in CI | `none_yet` | Requires implementation |

Target proof packet: `docs/proof/platform/JARVIS_MEMORY_BOARD_V1_PROOF.md` (not yet created).

## 9. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan + genome |
| Identity | Slot taxonomy + default profile frozen in active doc |
| Structure | Governance gate + lineage lane extension |
| Implementation | Universal board governance on memory promotion paths |
| Verification | V1 proof + `make memory-board-gate` |

## 10. Related

- [JARVIS_MEMORY_BOARD_DOCTRINE.md](../../contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md)
- [JARVIS_PROTOCOL.md](../../contracts/JARVIS_PROTOCOL.md)
- [CISIV_OPERATOR_LINEAGE_CONSOLE.md](./CISIV_OPERATOR_LINEAGE_CONSOLE.md)
- [AAIS_SUBSYSTEM_SPEC.md](../../runtime/AAIS_SUBSYSTEM_SPEC.md) § Memory Governance Stack

## 11. Activation Order Notes And Minimal Invariants

**Recommended activation order (batch):** **2** of 3 (`barebones-summon-wave-2026-06`)

**Depends on:** Jarvis operator runtime (live); benefits from **Capability Service Bridge** (order 1) for governed execute context

**Minimal invariants:**

- `controller_approved` required for every install
- `supported_slot` must match target slot id
- Migrations preserve trust class and slot role
