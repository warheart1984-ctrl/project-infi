# Inter-Substrate Diplomacy Contract

Status: **active contract** (Mythic Stage 15 / Anatomical Layer 17 / Release 45)

Not UGR federation grant governance, not MGM permeability alone, not platform IMXP fork.

## Purpose

Governed **diplomatic accords** between substrates (UL substrate, Memory Board overlays, platform IMXP, operator ledger scopes) under adopted charters and membrane policies — ISD-2 adoption requires operator promotion and Jarvis authorization.

## Accord envelope

Schema: [schemas/operator_diplomatic_accord.v1.json](../../schemas/operator_diplomatic_accord.v1.json)

## Inter-substrate coordination classes

| Class | Meaning |
|-------|---------|
| ISD-0 | Observe cross-substrate drift (unsigned handoffs, charter/substrate mismatch) |
| ISD-1 | Diplomatic accord proposal |
| ISD-2 | Adopted accord (operator + Jarvis; diplomacy overlay) |
| ISD-3 | Accord-influenced admission elevation (never execution bypass) |

## Rules

1. Nova may interpret cross-substrate context; Jarvis must authorize diplomacy overlay admission
2. MGM-2 policies and CEC-2 charters constrain accords — never auto-promote upstream layers
3. Diplomacy overlay uses `civilizational_tier` metadata (not doctrine slot until proof gates pass)
4. UGR and IMXP wrappers remain technical admission; ISD accords are negotiated posture layered on membrane + charter evidence
5. Dreamspace consolidation is proposal-only

## APIs

- `GET /api/operator/diplomacy`
- `POST /api/operator/diplomacy/observe`
- `GET /api/operator/diplomacy/accords`
- `POST /api/operator/diplomacy/accords/adopt`

## Verification

```bash
make inter-substrate-diplomacy-body-gate
```
