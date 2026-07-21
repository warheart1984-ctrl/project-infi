# Governance Loop

The governance loop evaluates substrate signals, actions, ledger entries, and invariant results on every tick.

## Text Sketch

Authority -> Replay -> Audit -> Accountability -> Compliance -> Authority

```
GOVERNANCE LOOP

(1) AUTHORITY
  |
  v
(2) REPLAY
  |
  v
(3) AUDIT
  |
  v
(4) ACCOUNTABILITY
  |
  v
(5) COMPLIANCE
  |
  v
(back to) AUTHORITY
```

## Expanded Constitutional Flow

```
AUTHORITY
  |  declares who may act
  v
REPLAY
  |  reconstructs how they acted
  v
AUDIT
  |  inspects whether they acted correctly
  v
ACCOUNTABILITY
  |  assigns responsibility for the action
  v
COMPLIANCE
  |  validates alignment with rules
  v
AUTHORITY (updated)
  ^  adjusts future authority based on compliance outcomes
```

This shows the self-correcting nature of governed reasoning.

## Governance Loop With Evidence Anchors

```
AUTHORITY
  |  (Authority Record)
  v
REPLAY
  |  (Reasoning Trace)
  v
AUDIT
  |  (Audit Record)
  v
ACCOUNTABILITY
  |  (Steward Record)
  v
COMPLIANCE
  |  (Policy Receipt)
  v
AUTHORITY (updated)
  ^  (Governance Feedback)
```

Every step is backed by a Proof & Challenge Surface in the Constitutional Evidence Graph.

## Governance Loop With Failure Modes

```
AUTHORITY
  |
  v
REPLAY
  |
  v
AUDIT
  |
  v
ACCOUNTABILITY
  |
  v
COMPLIANCE
  |
  v
AUTHORITY
```

If any link breaks:

- Missing Replay -> reasoning cannot be reconstructed
- Missing Audit -> authority becomes unchecked
- Missing Accountability -> responsibility becomes unassigned
- Missing Compliance -> rule drift occurs
- Missing Authority -> decisions become orphaned

This is the constitutional fault map.

## Governance Loop With Constitutional Guarantees

```
AUTHORITY
  |  Guarantee: Every decision declares its authority source
  v
REPLAY
  |  Guarantee: Every decision is reproducible
  v
AUDIT
  |  Guarantee: Every decision is inspectable
  v
ACCOUNTABILITY
  |  Guarantee: Every decision has a responsible steward
  v
COMPLIANCE
  |  Guarantee: Every decision satisfies governing constraints
  v
AUTHORITY (updated)
  ^  Guarantee: Authority evolves based on compliance outcomes
```

This is the AAES-Governance v1.1 guarantee set.
