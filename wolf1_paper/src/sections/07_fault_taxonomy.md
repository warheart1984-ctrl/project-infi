# 7. Fault Code Taxonomy

WOLF‑1 defines four fault classes and seven fault codes.

## 7.1 Fault Classes

| Class | Severity | Reaction |
|--------|----------|----------|
| **A** | Critical | Immediate SAFE‑MODE |
| **B** | High | Shed LLM load; restrict tools |
| **C** | Medium | Throttle cognitive runs |
| **D** | Informational | Log only |

---

## 7.2 Fault Code Table

| Fault Code | Class | Invariant | Trigger |
|------------|--------|-----------|----------|
| PWR_SOLAR_BUDGET_EXCEEDED | C | INV.PWR.SOLAR_PRIMARY | Solar/storage below thresholds |
| PWR_FAILSAFE_FLOOR_LOST | A | INV.PWR.NUCLEAR_FAILSAFE_MIN | Governance floor lost |
| PWR_THERMAL_BOUND_BREACH | B | INV.PWR.THERMO_BOUNDS | Thermal bounds exceeded |
| PROP_LLM_ACTUATION_ATTEMPT | B | INV.HW.NO_DIRECT_ACTUATION | LLM attempted actuator command |
| PROP_BURN_CONFLICT | C | INV.PLAN.PROPOSAL_ONLY | Cognitive run during active burn |
| GOV_SAFE_MODE_POLICY_VIOLATION | B | INV.GOV.SAFE_MODE_PROFILE | Disallowed action in safe‑mode |
| GOV_INVARIANT_EVAL_FAILURE | A | INV.GOV.FAILED_INVARIANTS_FAIL_CLOSED | Invariant engine failure |

---
