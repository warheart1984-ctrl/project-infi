# Autobiographical Agency Contract

Status: **active contract** (Anatomical Stage 8 / Release 39)

Not Nova stage numbering, not Alt-8 intent-agency organ governance.

## Purpose

Governed **ongoing work with the operator** — autobiographical episodes fusing identity, narrative beats, habits, intent commitments, and in-flight work, admitted to Memory Board operational slot (slot_02) only after operator promotion and Jarvis authorization.

## Episode envelope

Schema: [schemas/operator_autobiographical_episode.v1.json](../../schemas/operator_autobiographical_episode.v1.json)

## Autobiographical coordination classes

| Class | Meaning |
|-------|---------|
| AAC-0 | Observe-only drift + episode candidate surfacing |
| AAC-1 | Autobiographical episode proposal |
| AAC-2 | Adopted episode (operator + Jarvis operational admission) |
| AAC-3 | Agency-influenced routing (Jarvis + existing gates) |

## Rules

1. Nova Intent remains consult-only ([NOVA_INTENT_CORE.md](../runtime/NOVA_INTENT_CORE.md))
2. Jarvis must authorize operational admission ([jarvis_autobiographical_authority.py](../../src/jarvis_autobiographical_authority.py))
3. Identity (ICC-2) and narrative beats (NCC-2) constrain episodes — never auto-promote upstream layers
4. Operational slot is stable working knowledge ([JARVIS_MEMORY_BOARD_DOCTRINE.md](./JARVIS_MEMORY_BOARD_DOCTRINE.md) § Slot 02)
5. Dreamspace consolidation is proposal-only

## APIs

- `GET /api/operator/autobiographical`
- `POST /api/operator/autobiographical/observe`
- `GET /api/operator/autobiographical/episodes`
- `POST /api/operator/autobiographical/episodes/adopt`
