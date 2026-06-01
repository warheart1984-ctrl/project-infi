# Seam Test Checklist

Use this checklist whenever a seam is suspected, reproduced, or hardened.

This file is the execution companion to [SEAM_LAW.md](SEAM_LAW.md).

## 1. Detection Capture

- [ ] Record the first instability signal.
- [ ] Record why it felt structural instead of random.
- [ ] Name the user-visible symptom.
- [ ] Name the likely boundary where the symptom appears.

## 2. Reproduction Pressure

- [ ] Reproduce the original path.
- [ ] Reproduce a materially different path aimed at the same boundary.
- [ ] Add repetition pressure if the seam is intermittent.
- [ ] Add long-turn pressure if the seam could accumulate over time.
- [ ] Add malformed-fragment pressure if partial carryover is plausible.
- [ ] Add budget pressure if context or output sizing is involved.
- [ ] Add routing ambiguity if lane or provider selection is involved.

## 3. Seam Classification

- [ ] Assign one primary seam class.
- [ ] Record any secondary seam classes involved.
- [ ] Name the exact runtime boundary where closure must land.

Primary classes:

- `identity_seam`
- `routing_seam`
- `prompt_assembly_seam`
- `memory_seam`
- `context_window_seam`
- `tool_invocation_seam`
- `governance_seam`
- `output_shape_seam`

## 4. Law Definition

- [ ] Write the invariant that must always be true.
- [ ] State what invalid state must be rejected.
- [ ] Identify the single source of truth for this boundary.
- [ ] Identify any duplicate injection or interpretation paths to remove.

Examples:

- one semantic identity per singleton prompt block
- no assistant scaffold echo re-entry
- reply budget floor survives provider estimation
- tool execution cannot bypass governance

## 5. Enforcement Design

- [ ] Enforce the law at the boundary, not downstream from it.
- [ ] Fail closed on invalid state.
- [ ] Make diagnostics explicit and non-vague.
- [ ] Keep required governance intact while removing duplicated or malformed state.

## 6. Diagnostic Quality

- [ ] Error explains what failed.
- [ ] Error explains why it failed.
- [ ] Error explains where it failed.
- [ ] Trace exposes the seam-specific proof fields.
- [ ] Operator-visible traces stay safe and do not leak hidden context.

## 7. Verification Coverage

- [ ] Add a deterministic reproduction test.
- [ ] Add a regression test for the original failure.
- [ ] Add a stress test with repeated pressure.
- [ ] Add a mixed-pressure test if the seam crosses multiple systems.
- [ ] Add a long-turn accumulation test if growth or drift is possible.

Suggested stress matrix:

- same input across repeated turns
- mixed intent over repeated turns
- malformed fragment carryover
- memory cue duplication pressure
- provider or route variation
- near-max prompt or context pressure

## 8. Proof Checks

- [ ] The seam reproduces before the fix.
- [ ] The seam stops reproducing after the fix.
- [ ] The boundary is now explicit and inspectable.
- [ ] Growth remains bounded over repeated runs.
- [ ] No hidden re-inflation appears in traces.
- [ ] No critical rule or governance loss was introduced by the fix.

## 9. Admission Gate

Do not call the seam closed until all are true:

- [ ] reproduced
- [ ] classified
- [ ] bounded by law
- [ ] fail-closed at the boundary
- [ ] diagnosed clearly
- [ ] verified by regression coverage
- [ ] verified by stress coverage

## 10. Seam Report Template

Use this compact template when capturing a seam:

```md
# Seam Report

## Title
[Short seam name]

## First signal
[What felt wrong]

## Why it stood out
[Why this did not look like random output noise]

## Probe 1
[Original hit]

## Probe 2
[Different path]

## Shared behavior
[What stayed the same]

## Seam class
- [primary class]
- [secondary class if needed]

## Boundary
[Exact runtime seam location]

## Law
[What must always be true]

## Enforcement
[How invalid state is rejected]

## Verification
[Tests and stress passes added]
```

## Final Rule

If the seam is not proven under pressure, it is not closed.
