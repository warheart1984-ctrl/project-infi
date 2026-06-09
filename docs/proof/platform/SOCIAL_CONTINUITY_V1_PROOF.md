# Social Continuity V1 Proof

Status: **Release 40 / Anatomical Stage 9**

## Scope

Governed relational continuity fusing identity, narrative, agency, federation grants, mesh handoffs, and ledger cross-tenant signals under AAIS law: SCC-0 drift observation, SCC-2 operator + Jarvis archive adoption, SCC-3 social-influenced suggestion elevation (never execution bypass).

## Contract

- [SOCIAL_CONTINUITY_CONTRACT.md](../../contracts/SOCIAL_CONTINUITY_CONTRACT.md)
- Schemas: `operator_social_bond.v1`, `social_drift.v1`

## Modules

| Module | Role |
|--------|------|
| `src/social_continuity_runtime.py` | Relational drift fusion, candidate surfacing, governed adoption |
| `src/social_continuity_registry.py` | Adopted bond registry |
| `src/jarvis_social_authority.py` | Jarvis gate for archive admission and SCC-3 influence |
| `src/social_bond_adoption_bridge.py` | Brain accept → adoption approval enqueue |
| `src/social_continuity_organ.py` | Live runtime posture for coherence fabric |

## APIs

| Route | Behavior |
|-------|----------|
| `GET /api/operator/social` | Social snapshot |
| `POST /api/operator/social/observe` | SCC-0 drift observe |
| `GET /api/operator/social/bonds` | Adopted + candidates |
| `POST /api/operator/social/bonds/adopt` | SCC-2 promote (403 without operator_approved + Jarvis auth) |

## Verification

```bash
make social-continuity-body-gate
python -m pytest tests/test_social_continuity_observe.py tests/test_social_continuity_adopt.py -q
```

## Success criteria

- Drift observation surfaces SCC-0/1 candidates without writing archive slot
- SCC-2 adoption requires operator approval **and** Jarvis authorization; ledger receipt emitted
- Bonds contradicting identity/narrative/agency/anchor are rejected at validation
- Brain accept enqueues bond adoption approval; does not auto-adopt
- AAC-2 episodes + NCC-2 beats + federation grants + mesh handoffs surface SCC-1 candidates only (40c); no auto-promotion
- Somatic panel shows `adopted_bonds` / social drift / federated peer counts
- `social_continuity_organ` reads live runtime posture
- SCC-3 social boost applies to mesh suggestion scoring only
