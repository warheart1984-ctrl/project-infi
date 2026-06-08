# Norm Federation V1 Proof

Status: **Release 46 / Civilizational Stage 16 — claim: proven**

Sign-off: [`CIVILIZATIONAL_ARC_PROVEN_SIGNOFF.md`](../../audit/CIVILIZATIONAL_ARC_PROVEN_SIGNOFF.md)

## Scope

Governed norm federation treaties: NFD-0 drift observation, treaty adoption with operator + Jarvis gate, federation posture read-only.

## Verification

```bash
make norm-federation-body-gate
python -m pytest tests/test_norm_federation_observe.py tests/test_norm_federation_adopt.py -q
```

## APIs

| Route | Behavior |
|-------|----------|
| `GET /api/operator/norm-federations` | Federation snapshot |
| `GET /api/operator/norm-federations/treaties` | Adopted + candidates |
