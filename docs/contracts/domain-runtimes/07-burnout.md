# Burnout runtime

## StateObjects

- **BurnoutState** — `snapshot_id`, `sleep_quality`, `stress_level`, `cognitive_load`, `meeting_load`, `recovery_index`, `trend`
- **RecoveryPlanState** — `plan_id`, `measures`, `duration`, `adherence`
- **LoadSourceState** — `source_id`, `type` (project, role, relationship), `load_contribution`

## Receipts

| Type | Kinds |
|------|-------|
| `BurnoutObservationReceiptV2` | Observation, Warning, Critical |
| `RecoveryReceiptV2` | PlanCreate, PlanAdjust, PlanComplete |
| `LoadReceiptV2` | Spike, Reduce |
| `BurnoutRemediationReceiptV2` | Closure when metrics return to safe band |

## Invariants

- **BR-1:** No sustained operation in Critical burnout state.
- **BR-2:** Warnings must trigger a RecoveryPlan within bounded time.
- **BR-3:** High cognitive + high meeting load must not persist without explicit acceptance.

## Remediation

**Trigger:** `BurnoutObservation` Warning or Critical.

**Path:** Identify load sources → Reduce/redistribute → Enforce recovery → Monitor.

## Risk / learning / amendments

Risk: trends in sleep, stress, load, recovery adherence.

Learning: recovery plan effectiveness (time to safe band, recurrence).

Amendments: Warning/Critical thresholds, mandatory recovery, non-negotiable limits.
