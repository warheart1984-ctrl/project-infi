# Governed Civilization V1 Proof

Status: **Release 48 / Mythic Stage 18 / Anatomical Layer 20 — claim: proven**

Sign-off: [`CIVILIZATIONAL_ARC_PROVEN_SIGNOFF.md`](../../audit/CIVILIZATIONAL_ARC_PROVEN_SIGNOFF.md)

## Scope

Top-level governed civilization envelope binding CEC charters, NFD treaties, ISD accords, and MGM policies: GCV-0 drift observation, GCV-2 operator + Jarvis civilization overlay adoption, GCV-3 coherence elevation (read-only).

## Contract

- [GOVERNED_CIVILIZATION_CONTRACT.md](../../contracts/GOVERNED_CIVILIZATION_CONTRACT.md)
- Schemas: `operator_civilization_charter.v1`, `civilization_drift.v1`

## Modules

| Module | Role |
|--------|------|
| `src/governed_civilization_runtime.py` | Civilization drift fusion, candidate surfacing, governed adoption |
| `src/governed_civilization_registry.py` | Adopted civilization registry |
| `src/jarvis_civilization_authority.py` | Jarvis gate for civilization overlay admission |
| `src/governed_civilization_organ.py` | Live runtime posture for coherence fabric |

## Verification

```bash
make governed-civilization-body-gate
make civilizational-arc-gate
```
