# Social Continuity Contract

Status: **active contract** (Anatomical Stage 9 / Release 40)

Not Nova stage numbering, not UGR federation grant governance, not Alt-8 continuity witness.

## Purpose

Governed **stable relational bonds** fusing identity, narrative, agency episodes, federation grants, mesh handoffs, and ledger cross-tenant signals — admitted to Memory Board archive slot (slot_04) only after operator promotion and Jarvis authorization.

## Bond envelope

Schema: [schemas/operator_social_bond.v1.json](../../schemas/operator_social_bond.v1.json)

## Social coordination classes

| Class | Meaning |
|-------|---------|
| SCC-0 | Observe-only relational drift + bond candidate surfacing |
| SCC-1 | Social bond proposal |
| SCC-2 | Adopted bond (operator + Jarvis archive admission) |
| SCC-3 | Social-influenced routing (Jarvis + existing gates) |

## Rules

1. Nova may interpret relational context; Jarvis must authorize archive admission ([jarvis_social_authority.py](../../src/jarvis_social_authority.py))
2. Identity (ICC-2), narrative beats (NCC-2), and agency episodes (AAC-2) constrain bonds — never auto-promote upstream layers
3. Archive slot is durable relational memory ([JARVIS_MEMORY_BOARD_DOCTRINE.md](./JARVIS_MEMORY_BOARD_DOCTRINE.md) § Slot 04)
4. UGR federation grants remain technical admission; SCC bonds are relational continuity posture only
5. Dreamspace consolidation is proposal-only
6. AAC operator_partnership episodes describe first-person work; SCC bonds describe dyadic relational posture

## APIs

- `GET /api/operator/social`
- `POST /api/operator/social/observe`
- `GET /api/operator/social/bonds`
- `POST /api/operator/social/bonds/adopt`
