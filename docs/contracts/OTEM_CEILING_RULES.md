# OTEM Ceiling Rules Contract

**Schema:** `aais.otem_ceiling.v1`  
**Status:** Normative for constitutional recovery at OTEM Level 20

## Authority bands

| Band | Numeric levels | Role |
|------|----------------|------|
| `autonomous` | 1–9 | Low/medium immune posture; defend-heal-harden without operator gate |
| `governed` | 10–15 | High immune / governed escalation; execution via workflow approvals |
| `containment` | 16–19 | Pre-ceiling pause; diagnostic bundle; observe/propose only |
| `sovereign` | 20 | Constitutional recovery; recovery primitives only within constitution |

Default deployment (`AAIS_OTEM_CAPABILITY_LEVEL=10`) remains in the `governed` band with `ceiling_active=false`.

## Activation triggers

Ceiling containment (band ≥ 16) may activate when any of:

1. Repeated governed escalations within a sliding window
2. Substrate drift beyond configured threshold
3. Irreversible mutation blocked at operator checkpoint
4. Immune `critical` incident after local containment
5. Governance IR core invariant violation
6. Explicit operator invocation (`AAIS_OTEM_CEILING_INVOKE=1` or audited CLI)
7. Compiler escalation hook `escalate_to: otem_ceiling`

Level 20 (`ceiling_active=true`) requires explicit operator decision after mandatory pipeline stages. No silent autonomous L20 recovery.

## Constitutional vs mutable law

**Constitutional** (cannot be overridden at L20 without `constitutional_amendment` decision):

- `human_principal_root`
- `fail_closed`
- `no_self_delegation_of_ceiling_authority`
- `auditability_odl_binding`
- `defensive_only`
- `monotonic_authority_constraints`

**Mutable** (L20 may reset/narrow within constitution):

- `authority_mask_spec`
- `hardening_thresholds`
- `escalation_rules`
- `admission_rules`
- Compiler-generated check graphs

Invariant entries in Governance IR carry `law_class: constitutional|mutable`. Compiler emits `constitutional_amendment_required: true` when an L20 action would touch constitutional entries.

## Mandatory pipeline (L20)

1. **Diagnostic bundle** — IR snapshot, violation trace, ODL causal subgraph, heal/harden projections, authority delta
2. **Preview** — dry-run recovery action (`preview_only=true`)
3. **Explicit decision** — operator selects one of five recovery options
4. **Ledger closure** — root-signed ODL events for each stage
5. **Post-decision hardening** — compiler re-emit and immune policy enrollment

Pipeline states: `idle` → `diagnostic` → `preview` → `awaiting_decision` → `closing_ledger` → `idle`

## Operator decision options

| Option | Effect |
|--------|--------|
| `rollback_to_checkpoint` | Restore last ODL-anchored IR checkpoint |
| `quarantine_archive` | Quarantine affected scope and archive diagnostic bundle |
| `safe_mode_reanchor` | Safe-mode reset with IR genesis re-anchor + ODL event |
| `accept_containment` | Acknowledge containment without structural recovery |
| `constitutional_amendment` | Amendment pipeline for constitutional law changes |

## Operator unavailable

When `operator_unavailable_policy.timeout_minutes` elapses without decision:

- Fallback: `quarantine_archive` only
- Never: autonomous L20 recovery execution

## Edge cases

- **Ceiling overuse:** telemetry surfaced on operator console frequency tile
- **Voss binding:** v1 re-anchor = IR genesis reset + ODL event (not full Voss calculus)
- **CoGOS PID 1:** preview-only stub in v1; direct control deferred to Phase 3b

## IR projection

Governance IR includes `otem_ceiling_rules` (see `GOVERNANCE_IR.md`). Numeric `numeric_level` and semantic `otem_level` are projected from the same capability snapshot.
