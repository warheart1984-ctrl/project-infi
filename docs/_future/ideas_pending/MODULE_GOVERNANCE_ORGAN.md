# Module Governance Organ

CISIV stage: **concept**

Status: pending — Alt-13 summon wave `alt13-summon-wave-2026-06`.

## 1. Purpose

Read-only module governance controller posture; fail-closed on major violations.

Wraps: [`src/module_governance.py`](../../src/module_governance.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous escalation or repo mutation
- No replacement of underlying governed subsystems
- No full Story Forge front door, game lane, or text-to-3D activation

## 4. Organ Contract

Schema: [schemas/module_governance_organ.v1.json](./schemas/module_governance_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-MGO-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/module-governance/status` — read-only status
- `src/module_governance_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/MODULE_GOVERNANCE_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/module_governance_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt13-summon-wave-2026-06` — order **2**

**Depends on:** `ul_lineage_console_organ`, `safety_envelope_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-MGO-01`
