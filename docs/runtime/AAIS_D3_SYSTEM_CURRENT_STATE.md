# AAIS / D3 System Current State

This document records the current implementation posture of the AAIS/D3
governed execution kernel.

## Core Pipeline

```text
IG_k
  -> EGL
  -> SCIL
  -> SDAF
  -> SSAGL
  -> SCOL
  -> Execution Layer
```

Layer responsibilities:

- `IG_k`: invariant input state object carrying goal, seed, and runtime state.
- `EGL`: epistemic governance layer for replay and truth stability validation.
- `SCIL`: sovereign cognitive integration layer for normalization and semantic binding.
- `SDAF`: domain coherence layer for structural validation and constraint enforcement.
- `SSAGL`: sovereign authorization layer for permissioning and governance control.
- `SCOL`: sovereign cognitive orchestration layer for DAG-based planning and execution ordering.
- Execution layer: runtime mutation or action execution after governance acceptance.

## Current Implementation Summary

AAIS Kernel v0.1 operationalizes the conceptual stack as an executable runtime:

```text
IG_k -> EGL -> SCIL -> SDAF -> SSAGL -> SCOL -> EXECUTION
```

Each layer is represented as a deterministic transformation or gate:

- `IG_k`: invariant input state.
- `EGL`: hashing, replay anchors, and truth stability checks.
- `SCIL`: semantic normalization.
- `SDAF`: domain coherence validation.
- `SSAGL`: authorization and governance admission.
- `SCOL`: minimal DAG planner, currently `parse -> analyze -> execute`.
- Execution: deterministic step execution.

## Working Capabilities

### Deterministic Execution Kernel

The kernel target is:

```text
same input + same seed -> identical output
```

Current implementation validates reproducible behavior for the kernel path that
has deterministic fixtures and stable inputs.

### Execution Ledger

The ledger records stage transitions and hashed state so decisions can be
traced across the pipeline.

Logged data includes:

- stage name
- hashed state
- transition order
- trace history

### Replay System

Replay can re-run identical inputs across fresh kernel instances. The purpose is
to validate deterministic stability, not just re-execute the action path.

### Jon Fuzz Engine

The Jon role is modeled as a controlled fuzzing and perturbation layer. It
injects bounded input variation to expose hidden invariance failures.

Mutation modes include:

- goal drift
- state noise injection
- controlled perturbation under fixed seed conditions

The fuzz layer is not intended to produce final output. It exists to test
whether the system remains structurally invariant under pressure.

### Trace Diff Engine

The trace diff layer compares runs and detects divergence.

It checks:

- identical versus non-identical outputs
- final-state hash equality
- trace-shape divergence

## Roles

### Operator

The operator is the human or system controller that defines runtime constraints
and execution intent. The operator remains the final authority over execution
acceptance.

### Jon

Jon is the adversarial mutation role. Jon perturbs inputs and state surfaces to
test the stability of AAIS invariants.

## Maturity State

| Area | Current state |
| --- | --- |
| Full pipeline execution | Working |
| Determinism | Validated for deterministic fixtures |
| Replayability | Validated for stable replay paths |
| Mutation testing | Working |
| DAG planning | Minimal but functional |
| Production scaling | Next phase |

## Current Limitation

SCOL is currently a fixed linear DAG. It is not yet adaptive,
constraint-driven, or causal-graph optimized.

The main enforcement gap is that determinism and invariance are architectural
goals across the whole system, but not all layers have hard invariant checks
yet. SCOL, ledger, and replay exist, but invariant enforcement needs to become
tighter across every stage transition.

## Next Evolution

The next step is to upgrade SCOL into a dynamic DAG and causal planner with
`CG_k` integration.

That work should make planning:

- state-driven
- constraint-aware
- replay-verifiable
- causal-graph optimized

## One-Line Summary

AAIS/D3 is a multi-layer governed execution kernel with planning (`SCOL`),
validation (`EGL`), normalization (`SCIL`), domain coherence (`SDAF`),
authorization (`SSAGL`), and traceability through ledger plus replay, with a
Jon fuzz layer used to stress-test invariance under controlled mutation.
