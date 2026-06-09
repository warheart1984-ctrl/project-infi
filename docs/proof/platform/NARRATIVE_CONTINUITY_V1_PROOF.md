# Narrative Continuity V1 Proof

Status: **Release 38 / Anatomical Stage 7**

## Scope

Governed life-story continuity fusing identity, habits, mesh, Nova narrative, and ledger under AAIS law: NCC-0 drift observation, NCC-2 operator + Jarvis session adoption, NCC-3 narrative-influenced suggestion elevation (never execution bypass).

## Contract

- [NARRATIVE_CONTINUITY_CONTRACT.md](../../contracts/NARRATIVE_CONTINUITY_CONTRACT.md)
- Schemas: `operator_narrative_beat.v1`, `narrative_drift.v1`

## Modules

| Module | Role |
|--------|------|
| `src/narrative_continuity_runtime.py` | Drift fusion, candidate surfacing, governed adoption |
| `src/narrative_continuity_registry.py` | Adopted beat registry |
| `src/jarvis_narrative_authority.py` | Jarvis gate for session admission and NCC-3 influence |
| `src/narrative_beat_adoption_bridge.py` | Brain accept → adoption approval enqueue |

## APIs

| Route | Behavior |
|-------|----------|
| `GET /api/operator/narrative` | Life-story snapshot |
| `POST /api/operator/narrative/observe` | NCC-0 drift observe |
| `GET /api/operator/narrative/beats` | Adopted + candidates |
| `POST /api/operator/narrative/beats/adopt` | NCC-2 promote (403 without operator_approved + Jarvis auth) |

## Verification

```bash
make narrative-continuity-body-gate
python -m pytest tests/test_narrative_continuity_observe.py tests/test_narrative_continuity_adopt.py -q
```

## Success criteria

- Drift observation surfaces NCC-0/1 candidates without writing session slot
- NCC-2 adoption requires operator approval **and** Jarvis authorization; ledger receipt emitted
- Beats contradicting identity/anchor are rejected at validation
- Brain accept enqueues narrative adoption approval; does not auto-adopt
- Stable ICC-2 identity + HCC-2 habits surface NCC-1 candidates only (38c); no auto-promotion
- Somatic panel shows `adopted_beats` / narrative drift counts
- `narrative_continuity_organ` reads live runtime posture
- NCC-3 narrative boost applies to mesh suggestion scoring only
