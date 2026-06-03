# Phase Gate Organ

CISIV stage: **concept**

Status: pending — Alt-9 summon wave `alt9-summon-wave-2026-06`.

## 1. Purpose

Formalize **Phase Gate** ([`src/phase_gate.py`](../../src/phase_gate.py)) as a governed Alt-9 organ:
read-only exposure of component registration, phase histogram, and last violations
without granting activation authority through the organ surface.

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Subordinate to Jarvis admission law;
organ observes phase registry only.

## 3. Non-Goals

- No silent promotion to `active` without audit trail
- No replacement for `promote_component` / `assert_executable` call sites
- No universal phase enforcement across every subsystem in v1

## 4. Organ Contract

Schema: [schemas/phase_gate_organ.v1.json](./schemas/phase_gate_organ.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `AAIS-PG-01` |
| `registered_count` | Governed components in registry |
| `phase_histogram` | Counts per phase |
| `last_violation_summary` | Bounded last phase block event |

## 5. Runtime (Proposed)

- `GET /api/jarvis/phase-gate/status` — read-only phase gate snapshot
- `src/phase_gate_organ.py` — wraps `list_components` / `list_phase_events`

## 6. Failsafe

Empty registry returns bounded idle snapshot; organ remains read-only.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns phase snapshot | `none_yet` | Requires MVP |
| Phase histogram surfaced | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/platform/PHASE_GATE_ORGAN_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/phase_gate_organ.py` stub |
| Implementation | API route + gate |
| Verification | V1 proof + `make phase-gate-organ-gate` |

## 9. Related

- [CAPABILITY_SERVICE_BRIDGE.md](./CAPABILITY_SERVICE_BRIDGE.md)
- [AAIS_MODULE_GOVERNANCE_PROTOCOL.md](../../contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md)
- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `alt9-summon-wave-2026-06` — order **1** (admission fabric)

**Depends on:** Alt-8 governed mind-plane organs; capability service bridge phase assertions

**Minimal invariants:**

- Existence ≠ activation
- Read-only v1 — no write path from phase gate organ
- `module_id` frozen to `AAIS-PG-01`
