# Multi-Being Continuity Contract (Social Federation)

Status: **active contract** (Mythic Stage 11 / Anatomical Layer 13 / Release 41)

Not UGR federation grant governance, not Alt-8 continuity witness, not single-organism SCC archive bonds.

## Purpose

Governed **cross-organism continuity pacts** fusing identity, narrative, agency, social bonds, UGR federation grants, dual-ledger graphs, and paired mission receipts — admitted to Memory Board federation slot (slot_07) only after operator promotion and Jarvis authorization.

## Pact envelope

Schema: [schemas/operator_multi_being_pact.v1.json](../../schemas/operator_multi_being_pact.v1.json)

## Multi-being coordination classes

| Class | Meaning |
|-------|---------|
| MBC-0 | Observe-only cross-organism drift + pact candidate surfacing |
| MBC-1 | Multi-being pact proposal |
| MBC-2 | Adopted pact (operator + Jarvis federation-slot admission) |
| MBC-3 | Federation-influenced routing (Jarvis + existing gates) |

## Rules

1. Nova may interpret cross-organism context; Jarvis must authorize federation-slot admission ([jarvis_multi_being_authority.py](../../src/jarvis_multi_being_authority.py))
2. Identity (ICC-2), narrative (NCC-2), agency (AAC-2), and social bonds (SCC-2) constrain pacts — never auto-promote upstream layers
3. Federation slot is cross-organism continuity ([JARVIS_MEMORY_BOARD_DOCTRINE.md](./JARVIS_MEMORY_BOARD_DOCTRINE.md) § reserved slot_07)
4. UGR federation grants remain technical admission; MBC pacts are continuity posture layered on grants + digest-verified graphs
5. Dreamspace consolidation is proposal-only
6. SCC archive bonds describe single-organism relational posture; MBC pacts describe lawful multi-being federation continuity

## APIs

- `GET /api/operator/multi-being`
- `POST /api/operator/multi-being/observe`
- `GET /api/operator/multi-being/pacts`
- `POST /api/operator/multi-being/pacts/adopt`
