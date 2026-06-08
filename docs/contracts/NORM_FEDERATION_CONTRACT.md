# Norm Federation Contract

Status: **active contract** (Mythic Stage 16 / Anatomical Layer 18 / Release 46)

## Purpose

Governed **norm federation treaties** linking multiple COB-2 norms and CEC evidence across ecosystems — candidates only from adopted norms; never auto-promote norm → federation.

## Coordination classes

| Class | Meaning |
|-------|---------|
| NFD-0 | Observe federation drift (conflicting norms, treaty gaps) |
| NFD-1 | Federation treaty proposal |
| NFD-2 | Adopted treaty (operator + Jarvis) |
| NFD-3 | Federation-influenced routing elevation |

## APIs

- `GET /api/operator/norm-federations`
- `POST /api/operator/norm-federations/observe`
- `GET /api/operator/norm-federations/treaties`
- `POST /api/operator/norm-federations/treaties/adopt`

## Verification

```bash
make norm-federation-body-gate
```
