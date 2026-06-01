# Seam Law

Detection • Pressure • Closure

## Purpose

This file defines the non-negotiable law for detecting, classifying, closing,
and proving runtime seams in AAIS.

It applies whenever work touches:

- identity
- intent
- routing
- memory
- prompt assembly
- tool execution
- governance
- output shaping
- context-window behavior

Use this law for debugging, hardening, regression work, and runtime integrity
repairs.

## Definition

A seam is a boundary where system behavior can diverge from intended law under
pressure.

Seams usually exist at transitions between system layers rather than inside a
single isolated component.

A seam is not just a bug.

A seam is a latent failure surface.

## Core Principle

All seams must be:

- discoverable
- classifiable
- closable under pressure

If a seam cannot be:

- reproduced
- explained
- bounded

it is still open.

## Signal Phase

Seams are first identified by instability signals, not by waiting for hard
errors.

Primary signals:

- behavior shifts under repetition
- output mutates across identical inputs
- identity becomes generic or drifts
- duplicate rules or context appear
- incorrect lane activation appears
- long-context quality degrades gradually
- responses truncate, clip, or stall
- tools do not execute, misfire, or vanish silently

Operator rule:

If it feels wrong, it is a valid detection signal.

Detection does not require proof.

Detection triggers pressure testing.

## Pressure Phase

A seam must be forced into visibility through structured pressure.

Pressure vectors:

- repetition
- mixed intent injection
- long-turn accumulation
- memory carryover stress
- malformed or partial fragments
- token or budget pressure
- identity ambiguity
- tool-routing ambiguity
- conflicting instructions

Goal:

Convert intuition into deterministic reproduction.

If the seam does not reproduce, increase pressure complexity instead of
declaring closure.

## Seam Classes

Every seam must be assigned a class before closure work begins.

- `identity_seam`
  missing, duplicated, generic, or drifting identity
- `routing_seam`
  incorrect lane, module, provider, or subsystem activation
- `prompt_assembly_seam`
  duplication, clipping, reinjection, contamination, or overflow
- `memory_seam`
  leakage, echo, duplication, stale carryover, or trust-layer drift
- `context_window_seam`
  degradation under long context or unsafe budget pressure
- `tool_invocation_seam`
  tool not called, misused, bypassed, or silently suppressed
- `governance_seam`
  rules not enforced, not visible, or applied inconsistently
- `output_shape_seam`
  structure instability, truncation, hidden-shape bleed, or reply collapse

If it cannot be classified, it cannot be closed.

## Closure Requirements

A seam is closed only by enforcing law at the boundary where it appears.

Closure requires all of the following:

### 1. Boundary Definition

Name where the seam exists.

Examples:

- prompt assembly between memory normalization and final model payload
- provider routing between route selection and token budgeting
- tool execution between governed intent and provider call

### 2. Explicit Law

State what must always be true at that boundary.

Examples:

- one semantic identity per singleton guidance block
- assistant scaffold echoes may not re-enter system guidance
- reply budget floor must survive provider-specific prompt estimation

### 3. Fail-Closed Enforcement

Reject invalid states instead of degrading silently.

Examples:

- reject unlabeled system guidance
- reject malformed scaffold fragments
- reject tool envelopes that bypass governance

### 4. Diagnostic Visibility

Errors and traces must explain:

- what failed
- why it failed
- where it failed

Diagnostics are part of the architecture, not a debugging afterthought.

### 5. Single Source Of Truth

Do not allow duplicated injection or interpretation paths for:

- identity
- memory
- rules
- provider sizing policy
- governance decisions

## Verification And Proof

A seam is not closed when it stops happening once.

It is closed when it is proven bounded.

Verification requirements:

- deterministic reproduction test exists
- regression coverage exists
- stress coverage exists
- no gradual re-inflation or drift appears across repeated runs
- traces expose the relevant boundary evidence

Required stress dimensions:

- repetition
- mixed pressure
- long-turn usage
- malformed input or fragment pressure
- budget pressure where applicable

Proof standard:

Testing produces evidence.

Verification determines truth.

Proof grants admission.

## Required Trace Evidence

Seam closure work must expose enough evidence to prove the boundary now holds.

Trace payloads should include the seam-specific fields needed for proof.

Examples:

- prompt size before cleanup
- prompt size after cleanup
- duplicates removed
- malformed fragments removed

## Closed Seam Records

Closed seam records for this repo live under `docs/contracts/seams/`.

Current documented closure records:

- [SEAM-VC-002-visible-scaffold-leakage.md](seams/SEAM-VC-002-visible-scaffold-leakage.md)
- semantic identities included
- provider budget policy and reserved reply floor
- routing decision and active lane
- tool execution status and normalized result

Trace output must remain safe for operator-visible surfaces.

## Anti-Patterns

These are false-closure patterns and are not acceptable seam repairs.

- false closure
  symptom disappears without law enforcement
- patch without boundary
  fix lands without naming the seam location
- silent degradation
  system absorbs failure without visibility
- duplicate injection
  multiple layers inject the same rule, memory, or identity state
- unbounded growth
  context, memory, rules, or retries accumulate without control
- scale before law
  complexity increases before the seam is governed

## Operational Loop

All seam handling follows this loop:

Detect → Pressure → Reproduce → Classify → Define Law → Enforce → Verify → Lock

No seam exits the loop without law and proof.

## Doctrine Alignment

Seam Law enforces:

- one job, one purpose
- bounded behavior under pressure
- fail-closed over fail-soft
- law before scale
- stability over convenience

## Runtime Alignment

This law should be applied directly at the live boundary in runtime code.

Typical current seam surfaces include:

- `src/api.py`
- `src/conversation_memory.py`
- `src/prompt_assembly.py`
- `src/jarvis_operator.py`
- `src/provider_registry.py`

If a markdown note and runtime code disagree, the code is the live truth and the
law must be enforced there.

## Final Statement

A system without seams is impossible.

A system with unmanaged seams is unstable.

A system with enforced seam law is governed.
