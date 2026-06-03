# Project Infi State Machine Organ

CISIV stage: **concept**

Status: pending — Alt-18 summon wave `alt18-summon-wave-2026-06`.

## 1. Purpose

Read-only governed cycle state machine posture.

Wraps: [`src/project_infi_state_machine.py`](../../src/project_infi_state_machine.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths
- No autonomous law or patch authority via organ API

## 4. Organ Contract

Schema: [schemas/project_infi_state_machine_organ.v1.json](./schemas/project_infi_state_machine_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-PIS-01` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/project-infi-state-machine/status` — read-only status
- `src/project_infi_state_machine_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/PROJECT_INFI_STATE_MACHINE_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/project_infi_state_machine_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [JARVIS_PROTOCOL.md](../../contracts/JARVIS_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt18-summon-wave-2026-06` — order **1**

**Depends on:** `operator_cognition_coherence_fabric`, `ul_lineage_console_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-PIS-01`
