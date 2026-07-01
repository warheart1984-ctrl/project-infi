# 8. Safe‑Mode Specification

Safe‑mode is a governed operational state entered automatically under critical conditions.

---

## 8.1 Entry Conditions

- PWR_FAILSAFE_FLOOR_LOST
- GOV_INVARIANT_EVAL_FAILURE
- Repeated Class B faults
- Explicit ground command

---

## 8.2 Allowed Behaviors

| Subsystem | Allowed Behavior |
|-----------|------------------|
| Governance | CRK‑1 + CAS remain online |
| Telemetry | Increased cadence |
| Power | Governance floor only |
| Propulsion | Hard‑coded fault protection only |
| Ground Relay | Signed policy updates allowed |

---

## 8.3 Forbidden Actions

- All LLM runs
- All planning/simulation
- Model load/update
- Discretionary propulsion
- Any action outside Section 8.2

---

## 8.4 Exit Protocol

Exit requires:

1. Class A faults cleared
2. Ground authorization
3. ModeTransition receipt
4. Graduated recovery to THROTTLED

---
