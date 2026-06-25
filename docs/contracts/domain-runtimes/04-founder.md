# Founder runtime

## StateObjects

- **RoleState** — `role_id`, `role` (Architect, Builder, Leader, …), `active`, `time_share`
- **EnergyState** — `snapshot_id`, `energy_level`, `focus_quality`, `fatigue_signals`
- **PriorityState** — `priority_id`, `domain`, `rank`, `alignment_with_role`
- **DecisionLoadState** — `snapshot_id`, `decisions_pending`, `decisions_made`, `complexity_index`

## Receipts

| Type | Kinds |
|------|-------|
| `RoleSwitchReceiptV2` | EnterRole, ExitRole, ForcedSwitch |
| `EnergyReceiptV2` | Observation |
| `DecisionLoadReceiptV2` | Spike, Relief |
| `FounderRemediationReceiptV2` | Closure |

## Invariants

- **FR-1:** No sustained operation in a role with `energy_level` below threshold.
- **FR-2:** No critical decision under overloaded decision load.
- **FR-3:** Context switches bounded per day/week.

## Remediation

**Trigger:** overload, chronic low energy, excessive role switching.

**Path:** Reduce load → Reassign roles → Enforce recovery → Reassess.
