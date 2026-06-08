# Identity Self-Model Contract

Status: **active contract** (Anatomical Stage 6 / Release 37)

Not Nova stage numbering, not Super Nova stage promotion.

## Purpose

Governed **stable self-models under constitutional law** — identity claims admitted to Memory Board foundation slot (slot_01) only after operator promotion and Jarvis authorization.

## Claim envelope

Schema: [schemas/operator_identity_claim.v1.json](../../schemas/operator_identity_claim.v1.json)

## Identity coordination classes

| Class | Meaning |
|-------|---------|
| ICC-0 | Observe-only drift + claim candidate surfacing |
| ICC-1 | Identity claim proposal |
| ICC-2 | Adopted claim (operator + Jarvis foundation admission) |
| ICC-3 | Identity-influenced routing (Jarvis + existing gates) |

## Rules

1. Personality is projection of identity anchor ([super_nova_anchor.py](../../src/super_nova_anchor.py))
2. Jarvis must authorize foundation admission ([jarvis_identity_authority.py](../../src/jarvis_identity_authority.py))
3. Culture habits (HCC-2) may surface ICC-1 candidates only — never auto-promote to foundation
4. Foundation slot is canonical trust ([JARVIS_MEMORY_BOARD_DOCTRINE.md](./JARVIS_MEMORY_BOARD_DOCTRINE.md) § Slot 01)

## APIs

- `GET /api/operator/identity`
- `POST /api/operator/identity/observe`
- `GET /api/operator/identity/claims`
- `POST /api/operator/identity/claims/adopt`
