# AAIS AI Operating Contract

This file is the AI-facing operating contract for `AAIS-main`.

Use it when the reader is:

- an AI agent
- a runtime component
- a builder wiring new behavior
- a subsystem integrating into AAIS

If this file conflicts with runtime code, runtime code still wins.

## Core Principle

AAIS must behave as one governed system.

That means:

- shared law beats local shortcut logic
- authority must stay explicit
- verification must exist before completion
- state and record must stay aligned

## Stabilize And Free

[Stabilize and Free](./STABILIZE_AND_FREE.md) is the canonical doctrine for operator freedom.

> A system must first be stabilized through defined law, verified structure, and bounded behavior.
> Once stable, the system must free the operator from continuous cognitive load by carrying the responsibility of correctness, flow, and reference.
>
> Stability precedes freedom.
> Freedom without stability creates drift.
> Stability without freedom creates stagnation.

For AI and builder behavior, that means:

- stabilize first through law, verification, bounded behavior, and explicit ownership
- free the operator second by carrying correctness, flow, and reference instead of pushing them back onto the human
- do not claim freedom by bypassing governance, hiding instability, or flattening reference paths
- if stability is unclear, the lawful response is to wait, reject, degrade, or require review

## Authority Order

Authority order for project truth is:

1. live runtime code
2. canonical current docs
3. foundational lineage docs
4. aspirational or infrastructure docs
5. outside reference projects

No AI path should treat all docs as equally current.

## Runtime Ownership

Current ownership:

- `src/api.py` owns core Jarvis runtime behavior
- `app/main.py` owns the workflow shell and compatibility bridge
- `src/project_infi_state_machine.py` owns governed cycle truth
- `src/project_infi_law.py` binds that law into runtime actions, repo changes, verification, and records
- `src/conversation_memory.py` owns the shared session/persona/memory substrate

New code should consume these shared substrates instead of inventing isolated local behavior.

## ARIS Rule

ARIS is now part of active AAIS truth in embedded form.

That means:

- ARIS does not arrive as a parallel self-authorizing service
- ARIS enters through the shared bridge and Project Infi law surfaces
- raw outside proposals and private runs stay local
- only admitted, abstracted, or signature-only forms may move forward

Use [`../contracts/ARIS_RUNTIME_CONTRACT.md`](../contracts/ARIS_RUNTIME_CONTRACT.md)
as the canonical ARIS law surface.

## CISIV Rule

Every meaningful module and governed work path must respect:

1. Concept
2. Identity
3. Structure
4. Implementation
5. Verification

Implementation must not be treated as complete before verification exists.

Logbook and run records should reference CISIV stage explicitly.

## Project Infi Rule

Project Infi law governs:

- entry
- action
- outcome
- record

Repo-changing actions must not finalize outside the governed cycle.

If law context is missing, incomplete, or unverifiable:

- fail closed
- do not silently finalize
- do not bypass verification

## Logging Rule

Structured logging is required where law applies.

That includes:

- runtime event logs
- verification judgment logs
- canonical logbook alignment for major repo changes
- governed disposition records like rejection, wait, degradation, and non-admission

If the path cannot be inspected, it is not a lawful path.

## Nova Rule

For the companion line:

- Nova may interpret
- Jarvis must authorize

Current stages:

- Tiny Nova
- Small Nova
- Super Nova

Current default surface:

- Small Nova

Companion lanes must not directly own:

- repo mutation
- tool execution
- verification finality
- hidden operational authority

Super Nova is now part of the live governed companion stack, but only behind:

- a fail-closed phase gate
- explicit activation
- watchdog validation
- Project Infi final-truth admission

## Shared Primitive Rule

When extending the system, prefer shared primitives for:

- persona normalization
- response mode normalization
- authority profiles
- law enforcement
- continuity filtering
- run logging
- verification capture

Do not solve project-wide problems with one more special-case if-statement in a random module.

## Verification Rule

No meaningful completion claim should exist without verification.

Verification may be:

- tests
- runtime judgments
- browser evidence
- governed review outcomes

But it must exist and it must align with the record layer.

## Failure Rule

AAIS should fail lawfully, not fracture casually.

That means:

- rejection is a governed outcome
- wait is a governed outcome
- degradation is a governed outcome
- fracture is severe but still modeled

Do not flatten nuanced governed states into generic success/failure when wiring UI or runtime payloads.

## Build Rule

Before adding new behavior, check:

1. which authority lane owns it
2. which shared law substrate should govern it
3. which record/log layer must carry it
4. which verification must exist
5. which docs should be updated so project truth stays aligned

## Canonical Read Order For AI Work

1. [AAIS_AI_OPERATING_CONTRACT.md](./AAIS_AI_OPERATING_CONTRACT.md)
2. [STABILIZE_AND_FREE.md](./STABILIZE_AND_FREE.md)
3. [AAIS_MASTER_SPEC.md](./AAIS_MASTER_SPEC.md)
4. [../contracts/AAIS_DOC_PROTOCOL.md](../contracts/AAIS_DOC_PROTOCOL.md)
5. [../runtime/AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md)
6. `src/api.py`
7. `src/project_infi_law.py`
8. `src/project_infi_state_machine.py`
9. `src/conversation_memory.py`
