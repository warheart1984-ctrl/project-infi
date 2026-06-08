# Constitutional Ecosystem Contract (Beyond the Body)

Status: **active contract** (Mythic Stage 13 / Anatomical Layer 15 / Release 43)

Not COB shared norms, not MBC bilateral pacts, not Tier-5 genome DNA replacement.

## Purpose

Governed **ecosystem charters** binding multiple MBC-2 pacts and COB-2 norms under federation-scope constitutional frames — admitted to Memory Board ecosystem overlay (slot_08) only after operator promotion and Jarvis authorization.

## Charter envelope

Schema: [schemas/operator_ecosystem_charter.v1.json](../../schemas/operator_ecosystem_charter.v1.json)

## Constitutional ecosystem coordination classes

| Class | Meaning |
|-------|---------|
| CEC-0 | Observe ecosystem drift (member churn, pact conflicts, digest posture) |
| CEC-1 | Charter proposal |
| CEC-2 | Adopted charter (operator + Jarvis slot_08 overlay) |
| CEC-3 | Charter-influenced adaptive governance elevation |

## Rules

1. Nova may interpret ecosystem context; Jarvis must authorize slot_08 admission ([jarvis_ecosystem_authority.py](../../src/jarvis_ecosystem_authority.py))
2. CEC-2 requires evidence from ≥2 adopted MBC-2 pacts; never auto-promote COB norms → charter
3. Ecosystem overlay is slot_08 ([JARVIS_MEMORY_BOARD_DOCTRINE.md](./JARVIS_MEMORY_BOARD_DOCTRINE.md))
4. Tier-5 contextual gates may reference adopted charters; they do not replace Alt-4 promotion engines
5. Conflicting charters → ledger `ecosystem_arbitration`, operator supervision, fail-closed

## APIs

- `GET /api/operator/ecosystems`
- `POST /api/operator/ecosystems/observe`
- `GET /api/operator/ecosystems/charters`
- `POST /api/operator/ecosystems/charters/adopt`
