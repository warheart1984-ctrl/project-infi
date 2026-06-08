# Inter-Substrate Diplomacy V1 Proof

Status: **Release 45 / Civilizational Stage 15 / Anatomical Layer 17 — claim: proven**

Sign-off: [`CIVILIZATIONAL_ARC_PROVEN_SIGNOFF.md`](../../audit/CIVILIZATIONAL_ARC_PROVEN_SIGNOFF.md)

## Scope

Governed diplomatic accords across substrates: ISD-0 drift observation, ISD-2 operator + Jarvis dual gate, no execution bypass via accord.

## Verification

```bash
make inter-substrate-diplomacy-body-gate
python -m pytest tests/test_inter_substrate_diplomacy_observe.py tests/test_inter_substrate_diplomacy_adopt.py -q
```

## APIs

| Route | Behavior |
|-------|----------|
| `GET /api/operator/diplomacy` | Diplomacy snapshot |
| `GET /api/operator/diplomacy/accords` | Adopted + candidates |
