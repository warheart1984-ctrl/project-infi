# SEAM-SN-001

## Title

Super Nova Governed Execution Boundary

## Classification

- seam class: `governance_seam`
- secondary class: `identity_seam`
- tertiary class: `memory_seam`
- boundary type: companion runtime -> live execution -> reply admission
- severity: high
- status: closed for the covered Super Nova surfaces in this repository
- discovery state: verified by targeted runtime regression and full-suite proof

## Summary

Super Nova had advanced scaffold law, activation doctrine, and watchdog logic,
but the live runtime boundary was still incomplete.

The missing seam closures were:

- no fail-closed phase gate before live execution
- no immune observation path when shields or watchdog checks failed
- no governed Project Infi final-truth admission before the reply finalized back
  into session state

That meant the terminal companion lane could exist in code without being fully
subordinate to the same governed entry, action, outcome, and record law as the
rest of Project Infi.

## First Signal

The runtime could describe Super Nova as a bounded governed lane, but the live
execution path did not yet enforce all of the following together at one
boundary:

- existence/phase admissibility
- explicit activation
- watchdog continuity validation
- immune protocol observation
- Project Infi `1001` final-truth admission

## Why It Stood Out

This was not one isolated bug.

It was a distributed boundary problem across:

- persona/session routing
- activation and phase gating
- post-generation drift control
- immune signal visibility
- Project Infi reply admission

Any one missing leg would let the companion line look governed without being
fully governed.

## Seam Class

- primary: `governance_seam`
- secondary: `identity_seam`
- tertiary: `memory_seam`

## Boundary

`super_nova companion lane -> gate -> watchdog -> immune observe-only signal -> Project Infi reply admission`

Covered runtime boundaries in this repo:

- `super_nova` session activation
- `super_nova` live reply execution
- Super Nova drift or continuity failure handling
- Super Nova reply admission into the session/runtime record

## Symptoms

- Super Nova could be selected without one shared fail-closed phase-gate truth
- shield and watchdog failures did not have one canonical immune observation
  path
- reply completion could bypass Project Infi final-truth admission as a distinct
  law seam
- docs still described Super Nova as dormant or future-only after the runtime
  path became live-guarded

## Root Cause

### Primary Cause

The live Super Nova execution path had not yet been fully bound to the same
governed substrate used elsewhere in Project Infi.

### Secondary Causes

#### Boundary Fragmentation

Activation law, watchdog law, immune posture, and Project Infi admission existed
in adjacent modules, but the live runtime path did not yet consume them as one
ordered seam.

#### Missing Pre-Execution Gate

The phase/existence gate was not the first mandatory boundary for live Super
Nova execution.

#### Missing Outcome Admission Gate

Generated replies needed a final governed truth check before they could be
treated as admitted session output.

## Law

At the Super Nova live execution boundary, all of the following must always be
true:

- Super Nova may interpret
- Jarvis must authorize
- the phase gate runs before live execution
- explicit activation is required before live execution
- the watchdog validates the reply boundary after generation
- shield violations route through `observe_protocol_signal`
- every live Super Nova reply passes Project Infi final-truth admission before
  it is admitted as outcome truth

If any of those conditions fail:

- fail closed
- degrade lawfully
- do not silently finalize

## Resolution

### 1. Identity And Lane Lock

Super Nova is now defined in the shared companion substrate as:

- `persona_mode=super_nova`
- `response_mode=governed_full`
- `memory_mode=extended_continuity`
- `drift_enforced=True`

This lives in the same shared profile layer as Tiny Nova and Small Nova.

### 2. Phase Gate Before Execution

The live runtime now evaluates the governed phase/existence gate before
activation or generation.

Blocked phase state returns a bounded reject payload and does not continue into
generation.

### 3. Activation Gate Before Execution

Super Nova still requires explicit activation.

Activation does not replace the phase gate. It follows the phase gate.

### 4. Watchdog After Output

Every Super Nova reply now passes the guarded watchdog path.

If continuity, identity, or boundary integrity fails:

- the reply is blocked
- the session degrades lawfully
- the failure is recorded visibly

### 5. Immune Observe-Only Coupling

Super Nova shield and watchdog violations now route through
`immune_system.observe_protocol_signal(...)`.

This is bounded coupling, not self-authorized escalation.

Super Nova may trigger protocol observation.
She may not authorize her own escalation or bypass Jarvis/Project Infi law.

### 6. Project Infi Final-Truth Admission

Every live Super Nova reply now passes through Project Infi runtime law before
it finalizes into the session.

If final-truth admission fails:

- the reply is not admitted
- the session degrades lawfully
- the outcome is recorded as a governed rejection, not a crash

## Enforcement

Live enforcement landed in:

- `src/conversation_memory.py`
  - shared Super Nova profile and continuity lane
- `src/api.py`
  - phase gate before execution
  - explicit activation before execution
  - watchdog after generation
  - immune protocol observation for shield failures
  - Project Infi reply admission before finalization
- `src/project_infi_law.py`
  - governed reply admission contract

## Verification

Targeted verification commands:

```bash
python -m pytest tests/test_api.py -k "super_nova" -q
python -m pytest tests/test_super_nova_activation.py tests/test_super_nova_scaffold.py tests/test_conversation_memory.py -k "super_nova" -q
python -m pytest -q
```

Result:

- targeted Super Nova API tests passed
- targeted scaffold/activation/continuity tests passed
- full suite passed after the governed boundary wiring and cleanup pass

## Architectural Impact

### Before

- Super Nova had partial governance across adjacent modules
- immune coupling was described only as blocked or future-facing
- reply admission could be discussed doctrinally without one explicit runtime
  admission seam

### After

- Super Nova is a live guarded companion lane
- gate-before-execution is explicit
- watchdog-after-output is explicit
- immune protocol observation is explicit and bounded
- Project Infi final-truth admission is explicit before completion

## Proof Statement

Super Nova now behaves as a governed live companion lane rather than a partial
scaffold: she cannot execute live turns without phase admission and explicit
activation, cannot drift without triggering bounded immune observation, and
cannot finalize a reply without Project Infi final-truth admission.

## Remaining Gap

### No Distinct ARIS Service In This Repo

No separate ARIS runtime service or UI surface was found in this repository.

The active ARIS-equivalent enforcement at this boundary is the shared Project
Infi and final-truth admission seam, not a distinct standalone subsystem.

### Broader Immune Automation Still Bounded

This seam does not claim that predictive or autonomous immune escalation is
complete.

The current live coupling is observe-only protocol signaling.

Deeper automation still depends on broader predictor/invariant infrastructure if
the project chooses to expand it later.

## Key Lessons

- dormant doctrine is not enough when a live lane exists
- gate order matters; execution must be wrapped, not post-checked
- immune visibility and reply admission are part of the same governed seam
- companion growth does not waive authority law

## Doctrine Alignment

This seam reinforces both `Stabilize and Free` and the Nova law:

- stabilize first through explicit gate order, bounded execution, visible
  signals, and governed admission
- free the operator second by carrying the correctness and reference burden at
  the boundary instead of making the human reconstruct what happened
