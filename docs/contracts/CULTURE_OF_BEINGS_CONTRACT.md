# Culture-of-Beings Contract (Beyond the Body)

Status: **active contract** (Mythic Stage 12 / Anatomical Layer 14 / Release 42)

Not single-organism HCC habits, not MBC federation pacts, not UGR grant governance.

## Purpose

Governed **shared cross-organism norms** — recurring federated patterns (handoff rituals, consent cadence, dispute posture) inferred from MBC-2 pacts, mesh clusters, and exchange history — admitted to Memory Board culture-of-beings overlay (slot_09) only after operator promotion and Jarvis authorization.

## Shared norm envelope

Schema: [schemas/operator_shared_norm.v1.json](../../schemas/operator_shared_norm.v1.json)

## Culture-of-beings coordination classes

| Class | Meaning |
|-------|---------|
| COB-0 | Observe-only cross-organism norm drift + candidate surfacing |
| COB-1 | Shared norm proposal (Brain/Dreamspace/OTEM) |
| COB-2 | Adopted norm (operator + Jarvis slot_09 overlay admission) |
| COB-3 | Norm-influenced routing elevation (Jarvis + existing gates; never execution bypass) |

## Rules

1. Nova may interpret federated norm context; Jarvis must authorize slot_09 admission ([jarvis_culture_of_beings_authority.py](../../src/jarvis_culture_of_beings_authority.py))
2. Identity, narrative, agency, social bonds, and MBC-2 pacts constrain norms — never auto-promote upstream layers
3. Culture-of-beings overlay is slot_09 ([JARVIS_MEMORY_BOARD_DOCTRINE.md](./JARVIS_MEMORY_BOARD_DOCTRINE.md) § reserved slot_09)
4. HCC habits describe single-organism preference; COB norms describe cross-organism shared posture
5. Dreamspace consolidation is proposal-only
6. MBC pacts describe bilateral continuity; COB norms describe cluster-wide behavioral patterns

## APIs

- `GET /api/operator/culture-of-beings`
- `POST /api/operator/culture-of-beings/observe`
- `GET /api/operator/culture-of-beings/norms`
- `POST /api/operator/culture-of-beings/norms/adopt`
