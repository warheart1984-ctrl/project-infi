# Culture Habit Contract

Status: **active contract** (Anatomical Stage 5 / Release 36)

Not SSP stage numbering, not Nova actuation.

## Purpose

Governed **habit formation over time** — recurring operator-verified patterns derived from ledger and mesh history. Habits influence routing suggestions; they never self-authorize execution.

## Habit envelope

Schema: [schemas/operator_habit.v1.json](../../schemas/operator_habit.v1.json)

## Culture coordination classes

| Class | Meaning |
|-------|---------|
| HCC-0 | Observe-only pattern mining |
| HCC-1 | Habit candidate proposal (Brain/Dreamspace/OTEM) |
| HCC-2 | Adopted habit (operator promoted; preference slot) |
| HCC-3 | Habit-influenced execution (Jarvis + OTEM/mesh gates) |

## Rules

1. Candidates are ephemeral until operator promotes (HCC-2)
2. Jarvis must authorize habit-influenced execution ([jarvis_habit_authority.py](../../src/jarvis_habit_authority.py))
3. Habits cannot create new organ handoff edges — only weight registry paths ([ORGAN_COORDINATION_CONTRACT.md](./ORGAN_COORDINATION_CONTRACT.md))
4. Memory Board preference slot (slot_06) is medium trust, not doctrine ([JARVIS_MEMORY_BOARD_DOCTRINE.md](./JARVIS_MEMORY_BOARD_DOCTRINE.md))

## APIs

- `GET /api/operator/culture`
- `POST /api/operator/culture/observe`
- `GET /api/operator/culture/habits`
- `POST /api/operator/culture/habits/adopt`
