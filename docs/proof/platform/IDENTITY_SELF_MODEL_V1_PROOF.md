# Identity Self-Model V1 Proof

Status: **Release 37 / Anatomical Stage 6**

## Scope

Stable self-models under constitutional law: ICC-0 drift observation, ICC-2 operator + Jarvis foundation adoption, ICC-3 identity-influenced suggestion elevation (never execution bypass).

## Contract

- [IDENTITY_SELF_MODEL_CONTRACT.md](../../contracts/IDENTITY_SELF_MODEL_CONTRACT.md)
- Schemas: `operator_identity_claim.v1`, `identity_drift.v1`

## Modules

| Module | Role |
|--------|------|
| `src/identity_self_model_runtime.py` | Drift observe, candidate surfacing, governed adoption |
| `src/identity_self_model_registry.py` | Adopted claim registry |
| `src/jarvis_identity_authority.py` | Jarvis gate for foundation admission and ICC-3 influence |
| `src/identity_claim_adoption_bridge.py` | Brain accept → adoption approval enqueue |

## APIs

| Route | Behavior |
|-------|----------|
| `GET /api/operator/identity` | Identity snapshot |
| `POST /api/operator/identity/observe` | ICC-0 drift observe |
| `GET /api/operator/identity/claims` | Adopted + candidates |
| `POST /api/operator/identity/claims/adopt` | ICC-2 promote (403 without operator_approved + Jarvis auth) |

## Verification

```bash
make identity-self-model-gate
python -m pytest tests/test_identity_self_model_observe.py tests/test_identity_self_model_adopt.py -q
```

## Success criteria

- Drift observation surfaces ICC-0/ICC-1 candidates without writing foundation slot
- ICC-2 adoption requires operator approval **and** Jarvis authorization; ledger receipt emitted
- Claims violating anchor `immutable_law` are rejected at validation
- Brain accept enqueues identity adoption approval; does not auto-adopt
- Stable HCC-2 habits surface as ICC-1 candidates only (37c); no auto-promotion to foundation
- Somatic panel shows `adopted_claims` / identity drift counts
- ICC-3 identity boost applies to mesh suggestion scoring only when adopted boundary claims match
