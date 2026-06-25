# AAIS Master Spec

This file is the full system spec ledger for `AAIS-main`.

It is the one-file answer to:

- what subsystems exist
- what each subsystem owns
- what is live
- what is bounded
- what is still incomplete

If this file conflicts with runtime code, runtime code still wins.

## Project Doctrine

[Stabilize and Free](./STABILIZE_AND_FREE.md) is the canonical doctrine that governs how this spec should be interpreted.

In spec terms:

- stability means defined law, verified structure, and bounded behavior
- freedom means CLR: the system carries correctness, flow, and reference so the operator does not have to reconstruct them by hand
- any subsystem that increases operator burden before it is stable is violating the doctrine

## System Scope

AAIS currently includes these major areas:

- Jarvis core runtime
- Nova companion line
- embedded ARIS runtime profile
- Project Infi governed runtime
- workflow shell
- Forge lanes
- Evolve lane
- OTEM lane
- V9/V10 creative/runtime lanes
- governance, security, immune, continuity, and ledger layers

## Ownership Matrix

| Area | Primary files | Owns | Current status |
| --- | --- | --- | --- |
| Jarvis core | `src/api.py`, `src/jarvis_operator.py` | routing, state, core runtime behavior | Live |
| Workflow shell | `app/main.py`, `app/workflow_runtime.py`, `app/db.py` | workflow/onboarding/runs/approvals shell | Live |
| Project Infi law | `src/project_infi_law.py`, `src/project_infi_state_machine.py` | governed cycle, action law, records | Live |
| Conversation substrate | `src/conversation_memory.py` | session memory, persona, runtime prompt assembly | Live |
| Nova companion line | `src/api.py`, `src/conversation_memory.py`, `frontend/src/pages/NovaLandingPage.jsx` | Tiny/Small/Super companion surfaces | Live |
| Embedded ARIS | `src/aris_integration.py`, `src/cognitive_bridge.py`, `src/project_infi_law.py` | repo-intelligence boundary, non-copy clause, signature-only pattern sharing law | Live |
| Forge | `src/jarvis_operator.py`, `forge/service.py` | governed repo review/apply lanes | Live but bounded |
| Evolve | evolve-related clients and runtime state | evaluation/mutation/search lane | Live but bounded |
| OTEM | `src/jarvis_reasoning_protocol.py`, `src/otem_runtime.py`, `src/otem_ceiling.py` | reasoning/proposal lane; L20 sovereign recovery ceiling | Live (L10 default; L20 operator-only) |
| V9/V10 | `src/v9_runtime.py`, `src/v10_runtime.py` | bounded creative/runtime cores | Live |
| Governance and record | `src/module_governance.py`, `src/run_ledger.py`, `src/governance_layer.py` | module law, CISIV, logs, governance | Live |

## Tri-Core Spec

Current Tri-Core responsibilities:

- authority lane
- mode guidance
- turn contracts
- provider selection
- response finalization
- sovereignty and anti-drift integration
- bridge attestation and detachment containment

Jarvis must remain the main source of runtime truth.
Protected Jarvis ingress must also remain inside the Cognitive Bridge boundary and
fail closed when attestation, runtime context, or review status does not clear.

## Nova Companion Spec

Current Nova stages:

| Stage | Persona mode | Response mode | Status | Surface role |
| --- | --- | --- | --- | --- |
| Tiny Nova | `tiny_nova` | `tiny` | Live | lower bounded companion |
| Small Nova | `small_nova` | `small` | Live | installed bridge companion surface |
| Super Nova | `super_nova` | `governed_full` | Live guarded | final higher-capacity companion |

Canonical public path:

1. Tiny Nova
2. Super Nova

Current runtime bridge:

- Small Nova remains the installed bridge stage while Super Nova requires
  explicit activation and governed admission

Current companion laws:

- Nova may interpret
- Jarvis must authorize
- companion lanes do not own repo mutation
- companion lanes do not own tool execution
- continuity is filtered before prompt assembly
- Super Nova runs behind a phase gate, watchdog boundary, bounded immune
  protocol observation, and Project Infi final-truth admission

## Project Infi Spec

Project Infi governs:

- entry
- action
- outcome
- record

Current governed behavior includes:

- truth guard before admission
- adaptive TTL / Chronos wait handling
- governed wait with drift and recheck
- lawful rejection and non-admission
- degradation and fracture handling
- carryover state across cycles

## ARIS Spec

ARIS is live in AAIS as an embedded runtime profile, not a separate service.

Current ARIS laws:

- nothing happens without verification
- ARIS does not self-apply changes
- build/runtime separation remains load-bearing
- raw outside proposals and private runs stay local
- only admitted, abstracted, or signature-only forms may move forward

## Workflow Shell Spec

The workflow shell currently covers:

- definitions
- templates
- runs
- approvals
- onboarding
- run history

It is a live product surface, not just a reference page.

It does not replace Jarvis authority.

## Forge Spec

Forge currently exists as a governed contractor lane.

Current characteristics:

- law-bound
- review-aware
- structured service contract
- not a free bypass around Project Infi or Jarvis authority

Current limitation:

- still bounded and not a full autonomous general patch author

## OTEM Spec

OTEM operates on a four-band authority lattice (levels 1–20):

- **autonomous** (1–9): normal immune defend/heal/harden
- **governed** (10–15): default `AAIS_OTEM_CAPABILITY_LEVEL=10`; execution via approvals
- **containment** (16–19): pause + diagnostic bundle
- **sovereign** (20): non-delegable constitutional recovery ceiling

Level 20 is implemented (`src/otem_ceiling.py`): diagnostic bundle → preview →
explicit operator decision → ODL closure → post-decision hardening. Operator
surface: `/operator/ceiling`, console snapshot `otem_ceiling` (v1.3).

Current limitation set:

- capped execution scope below sovereign band
- proposal/reasoning emphasis at governed band
- L20 Voss re-anchor is IR genesis reset stub; full calculus deferred

## CISIV Spec

CISIV is now part of project law.

Stages:

1. Concept
2. Identity
3. Structure
4. Implementation
5. Verification

Current project rule:

- implementation should not be treated as complete without verification
- records and logbook entries should carry CISIV context

## Logging And Record Spec

Current project record expectations:

- structured event logs for runtime actions
- structured judgment logs for verification decisions
- canonical logbook alignment for major repo changes
- run ledger continuity
- immune posture and incident visibility
- Collective Pattern Ledger guidance and defense traces where implemented
- swarm-originated deliberation must remain bridge-governed where implemented
- governed rejection/degradation/wait records where applicable

## Current Incomplete Areas

The biggest still-incomplete areas are:

- OTEM execution substrate durability and autonomous workflow creation (below L20)
- PatchForge/Forge as a fuller autonomous authoring lane
- broader predictor/invariant-driven immune automation beyond the current
  observe-only Super Nova coupling
- some lineage and infrastructure docs still needing reclassification or cleanup

## Canonical Build Path

If someone is building across the whole project, the read order is:

1. [AAIS_HUMAN_GUIDE.md](./AAIS_HUMAN_GUIDE.md)
2. [AAIS_AI_OPERATING_CONTRACT.md](./AAIS_AI_OPERATING_CONTRACT.md)
3. [STABILIZE_AND_FREE.md](./STABILIZE_AND_FREE.md)
4. [AAIS_MASTER_SPEC.md](./AAIS_MASTER_SPEC.md)
5. [README.md](../../README.md)
6. [../contracts/AAIS_DOC_PROTOCOL.md](../contracts/AAIS_DOC_PROTOCOL.md)
7. [../runtime/AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md)

Then move into subsystem packs like Nova, Project Infi, Forge, or Workflows.
