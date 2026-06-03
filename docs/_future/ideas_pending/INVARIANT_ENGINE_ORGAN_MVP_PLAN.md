# Invariant Engine Organ — MVP Plan

CISIV stage: **structure**

Batch: `alt9-summon-wave-2026-06`

## MVP Surface

| Kind | Path |
|------|------|
| module | `src/invariant_engine_organ.py` |
| api | `GET /api/jarvis/invariant-engine/status` |
| gate | `make invariant-engine-organ-gate` |

## Gates

| Target | Script |
|--------|--------|
| `make invariant-engine-organ-gate` | `.github/scripts/check-invariant-engine-organ-governance.py` |

## Proof

`docs/proof/platform/INVARIANT_ENGINE_ORGAN_V1_PROOF.md`

## Promotion

`concept → prototype → mvp` via `tools/governance/alt9_promote_mvp.py`.
