# Autobiographical Agency V1 Proof

Status: **Release 39 / Anatomical Stage 8**

## Scope

Governed ongoing-work agency fusing identity, narrative, habits, intent, mesh, and in-flight operator work under AAIS law: AAC-0 drift observation, AAC-2 operator + Jarvis operational adoption, AAC-3 agency-influenced suggestion elevation (never execution bypass).

## Contract

- [AUTOBIOGRAPHICAL_AGENCY_CONTRACT.md](../../contracts/AUTOBIOGRAPHICAL_AGENCY_CONTRACT.md)
- Schemas: `operator_autobiographical_episode.v1`, `autobiographical_drift.v1`

## Modules

| Module | Role |
|--------|------|
| `src/autobiographical_agency_runtime.py` | Drift fusion, candidate surfacing, governed adoption |
| `src/autobiographical_agency_registry.py` | Adopted episode registry |
| `src/jarvis_autobiographical_authority.py` | Jarvis gate for operational admission and AAC-3 influence |
| `src/autobiographical_episode_adoption_bridge.py` | Brain accept → adoption approval enqueue |

## APIs

| Route | Behavior |
|-------|----------|
| `GET /api/operator/autobiographical` | Agency snapshot |
| `POST /api/operator/autobiographical/observe` | AAC-0 drift observe |
| `GET /api/operator/autobiographical/episodes` | Adopted + candidates |
| `POST /api/operator/autobiographical/episodes/adopt` | AAC-2 promote (403 without operator_approved + Jarvis auth) |

## Verification

```bash
make autobiographical-agency-body-gate
python -m pytest tests/test_autobiographical_agency_observe.py tests/test_autobiographical_agency_adopt.py -q
```

## Success criteria

- Drift observation surfaces AAC-0/1 candidates without writing operational slot
- AAC-2 adoption requires operator approval **and** Jarvis authorization; ledger receipt emitted
- Episodes contradicting identity/narrative/anchor are rejected at validation
- Brain accept enqueues autobiographical adoption approval; does not auto-adopt
- Stable NCC-2 beats + ICC-2 identity + HCC-2 habits + intent commitments surface AAC-1 candidates only (39c); no auto-promotion
- Somatic panel shows `adopted_episodes` / autobiographical drift / ongoing work counts
- `intent_agency_organ` reads live runtime posture
- AAC-3 agency boost applies to mesh suggestion scoring only
