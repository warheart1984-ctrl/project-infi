# Organ Coordination Contract

Status: **active contract** (Anatomical Stage 4 / Release 35)

Not SSP Stage 4, not Nova Stage 3 actuation.

## Purpose

Governed **multi-organ coordination** among the six workflow-family organs. Organs never call each other directly — all handoffs pass through `OrganCoordinationRuntime` with Jarvis authorization.

## Handoff envelope

Schema: [schemas/organ_handoff.v1.json](../../schemas/organ_handoff.v1.json)

Required fields: `source_family_id`, `target_family_id`, `chain_id`, `artifact_ref`, `claim_label`.

## Coordination classes

| Class | Meaning |
|-------|---------|
| OCC-0 | Observe-only plan |
| OCC-1 | Dry-run handoff |
| OCC-2 | Live handoff — requires operator ack or OTEM mesh approval |

## Mediation rules

1. Handoff graph is registry-only ([governance/workflow_family_registry.v1.json](../../governance/workflow_family_registry.v1.json)); runtime may not invent edges
2. Jarvis must authorize before mesh execution ([src/jarvis_organ_mesh_authority.py](../../src/jarvis_organ_mesh_authority.py))
3. Every handoff emits ledger receipt (`decision_kind: organ_handoff`)
4. Swarm Law applies: yield on low readiness, stop on conflict ([SWARM_LAW.md](./SWARM_LAW.md))

## APIs

- `GET /api/operator/organs/mesh`
- `POST /api/operator/organs/mesh/plan`
- `POST /api/operator/organs/mesh/runs`
- `GET /api/operator/organs/mesh/runs/<run_id>`
