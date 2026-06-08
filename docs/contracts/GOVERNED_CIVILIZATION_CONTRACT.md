# Governed Civilization Contract

Status: **active contract** (Mythic Stage 18 / Anatomical Layer 20 / Release 48)

## Purpose

Top-level **civilization registry** binding multiple CEC charters, NFD treaties, ISD accords, and MGM policies into a single governed civilization envelope — Jarvis treats as federation-scope constitution; Nova interprets only.

## Coordination classes

| Class | Meaning |
|-------|---------|
| GCV-0 | Observe civilization drift (member churn, accord conflicts) |
| GCV-1 | Civilization charter proposal |
| GCV-2 | Adopted civilization (operator + Jarvis; requires ≥2 CEC charters or equivalent evidence) |
| GCV-3 | Civilization-influenced coherence elevation (somatic/coherence fabric read-only) |

## APIs

- `GET /api/operator/civilizations`
- `POST /api/operator/civilizations/observe`
- `GET /api/operator/civilizations/charters`
- `POST /api/operator/civilizations/charters/adopt`

## Verification

```bash
make governed-civilization-body-gate
make civilizational-arc-gate
```
