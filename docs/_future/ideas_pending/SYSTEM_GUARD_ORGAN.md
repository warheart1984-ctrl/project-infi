# System Guard Organ

CISIV stage: **concept**

Status: pending — Alt-18 summon wave `alt18-summon-wave-2026-06`.

## 1. Purpose

Read-only system guard control posture.

Wraps: [`src/system_guard.py`](../../src/system_guard.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths
- No autonomous law or patch authority via organ API

## 4. Organ Contract

Schema: [schemas/system_guard_organ.v1.json](./schemas/system_guard_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-SGO-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/system-guard/status` — read-only status
- `src/system_guard_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/SYSTEM_GUARD_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/system_guard_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [JARVIS_PROTOCOL.md](../../contracts/JARVIS_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt18-summon-wave-2026-06` — order **9**

**Depends on:** `governance_layer_organ`, `security_protocol_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-SGO-01`
