# Direct Challenge Organ

CISIV stage: **concept**

Status: pending — Alt-12 summon wave `alt12-summon-wave-2026-06`.

## 1. Purpose

Read-only direct challenge / relational lane severity posture.

Wraps: [`src/direct_challenge_module.py`](../../src/direct_challenge_module.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous escalation or repo mutation
- No replacement of underlying governed subsystems

## 4. Organ Contract

Schema: [schemas/direct_challenge_organ.v1.json](./schemas/direct_challenge_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-DC-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/direct-challenge/status` — read-only status
- `src/direct_challenge_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/DIRECT_CHALLENGE_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/direct_challenge_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt12-summon-wave-2026-06` — order **2**

**Depends on:** `otem_bounded_organ`, `operator_profile_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-DC-01`
