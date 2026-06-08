# Narrative Continuity Contract

Status: **active contract** (Anatomical Stage 7 / Release 38)

Not Nova stage numbering, not Story Forge export.

## Purpose

Governed **life-story continuity** fusing identity, habits, mesh, Nova narrative, and ledger signals into coherent operator narrative beats admitted to Memory Board session slot (slot_03) only after operator promotion and Jarvis authorization.

## Beat envelope

Schema: [schemas/operator_narrative_beat.v1.json](../../schemas/operator_narrative_beat.v1.json)

## Narrative coordination classes

| Class | Meaning |
|-------|---------|
| NCC-0 | Observe-only drift + beat candidate surfacing |
| NCC-1 | Narrative beat proposal |
| NCC-2 | Adopted beat (operator + Jarvis session admission) |
| NCC-3 | Narrative-influenced routing (Jarvis + existing gates) |

## Rules

1. Nova Narrative remains observe-only ([NOVA_NARRATIVE.md](../runtime/NOVA_NARRATIVE.md))
2. Jarvis must authorize session admission ([jarvis_narrative_authority.py](../../src/jarvis_narrative_authority.py))
3. Identity claims (ICC-2) constrain beats — never auto-promote identity/habits to session registry
4. Session slot is rolling continuity ([JARVIS_MEMORY_BOARD_DOCTRINE.md](./JARVIS_MEMORY_BOARD_DOCTRINE.md) § Slot 03)
5. Dreamspace consolidation is proposal-only

## APIs

- `GET /api/operator/narrative`
- `POST /api/operator/narrative/observe`
- `GET /api/operator/narrative/beats`
- `POST /api/operator/narrative/beats/adopt`
