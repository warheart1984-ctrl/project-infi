# AAIS Human Guide

This is the human-facing guide to `AAIS-main`.

Use this file when you want to understand the project without reading code first.

It answers:

- what AAIS is
- what is live right now
- what the main surfaces are
- what Jarvis, Nova, Project Infi, Forge, and Workflows are
- what is still unfinished

If this file conflicts with runtime code, runtime code still wins.

## What AAIS Is

AAIS is a governed local AI system.

It is not just one chatbot.
It is a layered project with:

- a Jarvis runtime core
- a companion line through Tiny Nova and Small Nova
- a governed Project Infi action cycle
- an embedded ARIS repo-intelligence boundary and non-copy clause
- workflow and approval surfaces
- repo and review tooling
- continuity, governance, security, and logbook systems

The current project is meant to behave like one system, not a loose pile of features.

## Stabilize And Free

[Stabilize and Free](./STABILIZE_AND_FREE.md) is the canonical doctrine for how AAIS should feel to a human operator.

> A system must first be stabilized through defined law, verified structure, and bounded behavior.
> Once stable, the system must free the operator from continuous cognitive load by carrying the responsibility of correctness, flow, and reference.
>
> Stability precedes freedom.
> Freedom without stability creates drift.
> Stability without freedom creates stagnation.

In plain terms:

- stability means the system is governed, bounded, and verified first
- freedom means the system carries more of the correctness and reference burden so the operator does not have to remember everything manually
- this is the project doctrine behind CLR, which here means cognitive load reduction

## What Is Live Now

The current live project truth is:

- `src/api.py` is the main Jarvis runtime authority
- `app/main.py` is the workflow shell and compatibility bridge
- Small Nova is the installed companion surface
- Tiny Nova remains available as the lighter bounded companion stage
- Super Nova is available as a guarded explicitly activated companion lane
- Project Infi law and the governed runtime cycle are live
- CISIV is enforced in governance and operationally carried through the live workflow surfaces

The project currently passes its verified backend and frontend suites in the repo environment.

## Documentation Placement

AAIS now places its docs by role instead of leaving active and historical material mixed together.

- `docs/spine/` is the project-wide canonical spine
- `docs/runtime/` holds runtime and spec truth
- `docs/contracts/` holds active law, contracts, and protocols
- `docs/subsystems/` holds subsystem packs such as Nova
- `docs/audit/` holds status, cleanup, and logbook material
- `docs/_archive/legacy/workspace/` holds workspace-support and reference material
- `docs/_archive/` holds retained legacy or reference material

## The Main Pieces

### Jarvis

Jarvis is the core runtime and authority lane.

Jarvis owns:

- routing
- state
- safety
- verification
- execution authority
- turn contracts

Jarvis is the part of the system that must stay truthful and operationally grounded.

### Nova

Nova is the companion line.

Right now that means:

- Tiny Nova
- Small Nova

Nova helps with:

- reflection
- orientation
- calm conversation
- bounded continuity

Nova does not replace Jarvis as authority.

### Project Infi

Project Infi is the governed runtime law spine for meaningful action.

It governs:

- entry
- action
- outcome
- record

This is where lawful runtime behavior, verification, rejection, wait, degradation, and governed carryover are handled.

### ARIS

ARIS is now active in AAIS as embedded governed repo intelligence.

That means:

- ARIS strengthens ingress, verification, and sharing law
- ARIS does not exist here as a separate self-authorizing service
- raw outside proposals and private runs must not be copied directly into
  system truth
- only admitted, abstracted, or signature-only forms may move forward

### Forge

Forge is the contractor/repo-change lane.

It is not a free mutation engine.
It is governed, review-aware, and law-bound.

### Workflows

The workflow shell is the operational product layer around:

- definitions
- runs
- approvals
- onboarding
- run history

This shell is live, but it does not replace Jarvis runtime authority.

## Companion Stages

The current companion growth path is:

1. Tiny Nova
2. Small Nova
3. Super Nova

Current state:

- Tiny Nova is live
- Small Nova is live and installed
- Super Nova is live as a guarded lane, not the default home surface

## Current Boundaries

AAIS is intentionally bounded.

Important boundaries:

- Nova may interpret, Jarvis must authorize
- repo-changing paths must stay governed
- verification must exist before completion
- CISIV must be respected
- Project Infi law must fail closed when context is missing or unverifiable

The system should not silently flatten everything into generic success or failure.

## What Is Still Not Finished

The project is now stable enough to build on, but some larger pieces are still incomplete.

The biggest remaining items are:

- OTEM is still capped and not a full execution layer
- PatchForge is still not a full autonomous authoring system
- broader Super Nova immune automation beyond the current observe-only governed path is not yet implemented
- some older docs are still lineage/reference material rather than canonical current truth

## Best Reading Path

If you want to understand the project quickly, read these in order:

1. [AAIS_HUMAN_GUIDE.md](./AAIS_HUMAN_GUIDE.md)
2. [STABILIZE_AND_FREE.md](./STABILIZE_AND_FREE.md)
3. [AAIS_AI_OPERATING_CONTRACT.md](./AAIS_AI_OPERATING_CONTRACT.md)
4. [AAIS_MASTER_SPEC.md](./AAIS_MASTER_SPEC.md)
5. [README.md](../../README.md)
6. [../runtime/AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md)
7. [../runtime/AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md)

If you want Nova specifically after that, then read:

1. [../subsystems/nova/NOVA_HUMAN_GUIDE.md](../subsystems/nova/NOVA_HUMAN_GUIDE.md)
2. [../subsystems/nova/NOVA_AI_OPERATING_CONTRACT.md](../subsystems/nova/NOVA_AI_OPERATING_CONTRACT.md)
3. [../subsystems/nova/NOVA_STAGE_SPEC.md](../subsystems/nova/NOVA_STAGE_SPEC.md)
4. [../subsystems/nova/TINY_NOVA_CANONICAL.md](../subsystems/nova/TINY_NOVA_CANONICAL.md)
