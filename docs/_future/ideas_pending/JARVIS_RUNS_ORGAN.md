# Jarvis Runs Subsystem

CISIV stage: **concept**

Status: pending — Release 20 (`alt20-summon-wave-2026-06`).

## 1. Purpose

Read-only Jarvis runs ledger API posture.

Wraps: [`src/api.py`](../../src/api.py).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only subsystem surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths
- No autonomous law or patch authority via subsystem API

## 4. Subsystem Contract

Schema: [schemas/jarvis_runs_organ.v1.json](./schemas/jarvis_runs_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-JRN-01` |
| `status_summary` | Bounded subsystem snapshot |

## 5. Runtime (Proposed)

- `GET /api/jarvis/jarvis-runs/status` — read-only status
- `src/jarvis_runs_organ.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required subsystem fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/JARVIS_RUNS_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/jarvis_runs_organ.py` |
| Implementation | API route + gate |
| Verification | V1 proof + subsystem gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [JARVIS_PROTOCOL.md](../../contracts/JARVIS_PROTOCOL.md)

## 10. Activation Order

**Release:** `alt20-summon-wave-2026-06` — order **3**

**Depends on:** `run_ledger_organ`, `run_ledger_binding_organ`

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `AAIS-JRN-01`
