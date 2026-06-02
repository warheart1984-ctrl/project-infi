# Operator Profile Organ

CISIV stage: **concept**

Status: pending — Alt-5 summon wave `alt5-summon-wave-2026-06`.

## 1. Purpose

Normalize **operator profile** identity (`profile_id`, authority lane, capability preferences)
scattered across Nova/UGR into one governed organ aligned with operator supremacy.

## 2. Authority And Precedence

Operator supremacy per [NOVA_CORTEX_FORMAL_SPEC.md](../../runtime/NOVA_CORTEX_FORMAL_SPEC.md) §8.

## 3. Non-Goals

- Not a replacement for full UGR operator console
- No per-user adaptive scopes in v1
- No credential storage

## 4. Profile Contract

Schema: [schemas/operator_profile_organ.v1.json](./schemas/operator_profile_organ.v1.json)

## 5. Runtime (Proposed)

- `GET /api/jarvis/operator-profile` — normalized profile snapshot
- `src/operator_profile_organ.py` — bridge to `knowledge_authority`

## 6. Failsafe

Missing profile yields explicit default lane `operator` with asserted posture.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required fields | `asserted` | Schema + this document |
| Profile API returns lane + capabilities | `none_yet` | Requires MVP |
| Aligns with knowledge_authority sources | `none_yet` | Requires verification |

Target proof packet: `docs/proof/platform/OPERATOR_PROFILE_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/operator_profile_organ.py` stub |
| Implementation | API route + gate |
| Verification | V1 proof + `make operator-profile-gate` |

## 9. Related

- [knowledge_authority.py](../../../src/knowledge_authority.py)
- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt5-summon-wave-2026-06` — order **2** (after Safety Envelope)

**Depends on:** `jarvis`, `knowledge_authority`

**Minimal invariants:**

- profile_id never empty on live path
- authority_lane defaults to operator
- No elevation without explicit operator action
