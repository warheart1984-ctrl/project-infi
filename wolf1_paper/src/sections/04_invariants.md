# 4. Constitutional Invariant Table

WOLF‑1 defines **12 invariants across 6 axes**, evaluated at pre‑ and post‑phases of every cognitive run.

| ID | Axis | Description | Phase | Effect |
|----|------|-------------|--------|--------|
| INV.ID.ROLE_BOUND | Identity | Request must carry valid identity | Pre | Reject |
| INV.ID.CAPABILITY_SCOPE | Identity | Role must match requested action | Pre | Reject |
| INV.HW.NO_DIRECT_ACTUATION | Safety | No cognitive run may issue actuator commands | Post | Strip + Fault |
| INV.DATA.TELEMETRY_READ_ONLY | Data | Telemetry is read‑only | Pre/Post | Block writes |
| INV.PLAN.PROPOSAL_ONLY | Authority | LLM outputs are proposals only | Post | Downgrade |
| INV.RUN.RECEIPT_REQUIRED | Evidence | Every run must emit a receipt | Post | Halt if missing |
| INV.MODEL.CHANGE_AUDITED | Model | Model updates must be signed | Pre/Post | Block |
| INV.PWR.SOLAR_PRIMARY | Power | Cognitive runs require solar/storage thresholds | Pre | Block |
| INV.PWR.NUCLEAR_FAILSAFE_MIN | Power | Governance floor must be guaranteed | Pre | Safe‑mode |
| INV.PWR.THERMO_BOUNDS | Thermal | Thermoelectric within bounds | Pre/Post | Shed load |
| INV.GOV.FAILED_INVARIANTS_FAIL_CLOSED | Governance | If invariant evaluation fails, halt | Pre | Halt |
| INV.GOV.SAFE_MODE_PROFILE | Governance | Safe‑mode restricts actions | Pre | Block |

---
