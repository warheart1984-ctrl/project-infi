# Jarvis Memory Board — MVP Plan

CISIV stage: concept → implementation target

Status: planned (not yet implemented)

Batch: `barebones-summon-wave-2026-06`

Concept origin: [./JARVIS_MEMORY_BOARD.md](./JARVIS_MEMORY_BOARD.md)

## 1. Minimal Runtime Surface

| Surface | Planned location | Notes |
|---------|------------------|-------|
| module | `src/jarvis_memory_board.py` | Exists — formalize as governed family |
| api | `GET /api/jarvis/memory/board` | Exists — align response to schema v1 |
| gate | `make memory-board-gate` | Doctrine + controller law |
| lineage | `src/ul_lineage.py` | `memory_promotion` emission on promote paths |

## 2. Code Artifacts

- `src/api.py` — ensure board snapshot validates against `jarvis_memory_board.v1`
- `.github/scripts/check-memory-board-governance.py` — gate script
- `docs/subsystems/platform/JARVIS_MEMORY_BOARD.md` — active doc on promotion

## 3. Tests

- `tests/test_jarvis_memory_board.py` — extend: controller reject, migration trust, snapshot schema
- `tests/test_ul_lineage.py` — memory_promotion node on promotion fixture

## 4. Fixtures

- `fixtures/memory_board/default-profile.json` — six-slot populated board
- `fixtures/memory_board/controller-reject.json` — direct install without approval

## 5. Gates

| Gate | Script | Sequence |
|------|--------|----------|
| `make memory-board-gate` | `.github/scripts/check-memory-board-governance.py` | after `make capability-bridge-gate` (soft dep) |

## 6. Proof Bundle

Target: `docs/proof/platform/JARVIS_MEMORY_BOARD_V1_PROOF.md`

| Claim | Label | Evidence |
|-------|-------|----------|
| Board API matches schema snapshot | `none_yet` | Requires implementation |
| Controller rejects unapproved install | `none_yet` | Requires verification |
| Migration preserves trust class | `none_yet` | Requires verification |

## 7. Reproduction Commands

```bash
python -m pytest tests/test_jarvis_memory_board.py -q
make memory-board-gate
make genome-gate
```

## 8. Activation Dependencies

**Existing subsystems required:** Jarvis operator, `JARVIS_MEMORY_BOARD_DOCTRINE`, `cisiv_operator_lineage_console`

**Order among batch:** **2** — after Capability Service Bridge

**Rationale:** Memory promotions need governed execute context; pipeline turn traces consume board snapshots in order 3.
