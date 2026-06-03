# Intent Agency Organ — MVP Plan

CISIV stage: **structure**

Batch: `alt8-summon-wave-2026-06`

## MVP Surface

| Kind | Path |
|------|------|
| module | `src/intent_agency_organ.py` |
| api | `GET /api/jarvis/intent-agency/status` |
| gate | `make intent-agency-gate` |

## Gates

| Target | Script |
|--------|--------|
| `make intent-agency-gate` | `.github/scripts/check-intent-agency-governance.py` |

## Proof

`docs/proof/cognitive_runtime/INTENT_AGENCY_ORGAN_V1_PROOF.md`

## Promotion

`concept → prototype → mvp` via `tools/governance/alt8_promote_mvp.py`.
