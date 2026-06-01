# AAIS Runtime Guide

This is the current handbook for AAIS as it runs today.

If this file disagrees with runtime code, runtime code still wins. The point of
this handbook is to match the live system closely enough that one operator can
understand AAIS without reading half the repo.

## 1. What AAIS Is

AAIS is a Jarvis-centered orchestration shell.

It is not just:

- one model
- one prompt
- one UI
- one memory file

AAIS coordinates:

- Jarvis operator/runtime state
- protocol and reasoning packets
- provider routing and fallback
- specialist selection
- memory and review governance
- mission, approval, and execution discipline
- operator surfaces like the Workbench and Jarvis Console

### Stabilize And Free

[Stabilize and Free](../spine/STABILIZE_AND_FREE.md) is the active doctrine behind the runtime handbook.

> A system must first be stabilized through defined law, verified structure, and bounded behavior.
> Once stable, the system must free the operator from continuous cognitive load by carrying the responsibility of correctness, flow, and reference.
>
> Stability precedes freedom.
> Freedom without stability creates drift.
> Stability without freedom creates stagnation.

In runtime terms, that means governed architecture, explicit law, and verification come before any claim that AAIS is reducing operator load.

## 2. Canonical Runtime Spine

The main runtime files are:

- `app/main.py`
- `src/api.py`
- `src/conversation_memory.py`
- `src/jarvis_operator.py`
- `src/project_infi_law.py`
- `src/project_infi_state_machine.py`
- `src/jarvis_protocol.py`
- `src/jarvis_reasoning_protocol.py`
- `src/jarvis_modular.py`
- `src/v10_runtime.py`
- `src/provider_registry.py`
- `src/governance_layer.py`
- `src/run_ledger.py`
- `src/patch_review_store.py`
- `frontend/src/pages/JarvisConsole.jsx`
- `frontend/src/pages/Dashboard.jsx`

## 3. Workflow Shell And Legacy Bridge

AAIS currently has a second app shell in addition to the canonical Jarvis lane.

- `src/api.py` remains the main AAIS/Jarvis operator runtime
- `app/main.py` hosts the canonical FastAPI workflow and onboarding shell
- `app/main.py` also mounts the legacy Flask AAIS app through a bridge so older `/api/*` behavior still resolves during the transition
- the packaged AAIS app is now served from `/app` on that FastAPI shell so browser routes do not collide with workflow API routes
- workflow shell CISIV defaults are now operational:
- mission creation starts in `concept`
- onboarding completion records `identity`
- saved workflow definitions record `structure`
- queued runs and approvals record `implementation`
- simulations and browser-verification style evidence record `verification`

That bridge explains why some workflow/frontend docs mention FastAPI while the canonical AAIS docs still center `src/api.py`.

The important rule is:

- use `src/api.py` to understand core AAIS/Jarvis behavior, operator semantics, and runtime truth
- use `app/main.py` to understand the workflow shell, onboarding flow, and bridge layer
- treat workflow pages such as `frontend/src/pages/WorkflowBuilder.jsx` and `frontend/src/pages/Onboarding.jsx` as canonical workflow-shell surfaces, not reference-only prototypes
- do not let the workflow shell redefine Jarvis authority just because it can bridge into `/api/*`

## 4. Project Infi Runtime

Project Infi now runs as one governed runtime instead of scattered local checks.

The governing files are:

- `src/project_infi_state_machine.py`
- `src/project_infi_law.py`

Current cycle shape:

- `0001 -> 1000 -> 1001 -> 1010 -> 1111 -> 1001`
- if final L2 truth is not truthful, the cycle returns `rejected_no_admission`, propagates debt and risk, and ends lawfully
- if final L2 truth is truthful, legitimacy and Chronos decide whether the change is ready now or must wait

Chronos and wait rules:

- Chronos always computes a bounded TTL and `ready_at`
- if `now < ready_at`, the runtime applies recovery drift, schedules a recheck, and returns `WAIT`
- `WAIT` is a governed moving state, not a deadlock

FRACTURE rule:

- FRACTURE is severe, slowed, and operator-aware
- FRACTURE does not mean terminal forever; recovery drift can reduce risk over time under restricted legitimacy

Carryover rule:

- debt, scar, risk, binding, PrimeDepth, and wait timing state carry across cycles
- runtime actions, verification decisions, and repo-changing actions emit structured stage logs through the shared Project Infi law layer

## 5. State Hygiene Taxonomy

AAIS now uses one shared state hygiene taxonomy.

Do not collapse these concepts:

- `state_class`
- `truth_status`
- `retention_status`

### State Class

`state_class` answers:

what environment or lane did this record come from?

Current values:

- `live`
- `demo`
- `smoke`
- `test`

### Truth Status

`truth_status` answers:

how authoritative is this record?

Current values:

- `canonical`
- `derived`
- `reference`
- `historical`

Examples:

- a live operator memory can be `state_class=live`, `truth_status=canonical`
- a smoke verification run can be `state_class=smoke`, `truth_status=derived`
- a doctrine doc can be `state_class=live`, `truth_status=reference`

### Retention Status

`retention_status` answers:

should this still read like current operator truth?

Current values:

- `current`
- `archived`
- `expired`

## 6. Shared Projection Rules

AAIS should not let each surface invent its own meaning for state.

The shared helpers are the authority:

- `is_operator_visible(record)`
- `retention_policy_for(record)`
- `badge_for_state(record)`
- `precedence_rank(source_type, truth_status)`

The UI should mostly render these projections, not reinterpret them.

## 7. Operator Visibility Rule

Operator surfaces default to:

- `truth_scope=live`

That means:

- live current truth is visible by default
- demo, smoke, and test artifacts are still stored
- archived and expired records remain inspectable
- `truth_scope=all` is the explicit inspection escape hatch

## 8. Store Lifecycle Rules

AAIS keeps current truth and history separate.

### Memories

- live active memories are visible operator truth
- archived memories stay readable but stop acting like current truth
- non-live memories should be compacted out of current views

### Patch Reviews

- proposal is not authority
- accepted review is the apply gate
- non-live review artifacts should archive out of current operator views

### Run Ledger

- open live runs stay visible
- stale non-live open runs should expire
- completed runs remain historical evidence, not current state
- logbook entries should carry the CISIV stage they belong to so Concept, Identity, Structure, Implementation, and Verification stay inspectable in history
- workflow shell ledgers and mission history now carry the same CISIV stage field so shell records and Jarvis records can be read as one progression

### Governance

- active break-glass and live policy posture are current truth
- governance events are audit history
- non-live governance artifacts can be pruned without losing live posture

## 9. Canonical Knowledge Layer

AAIS now has one governed knowledge snapshot that combines:

- memory bank
- document knowledge
- live research
- workspace intel
- doctrine docs

The purpose is not to flatten them into one blob.

The purpose is to show:

- what source each fact came from
- what precedence it has
- what truth status it carries
- which source wins on conflict

## 10. Conflict Rule

Knowledge conflicts resolve by precedence.

General rule:

1. canonical override memory
2. live canonical operator memory
3. live governance/continuity state
4. workspace truth
5. document/reference truth
6. live research
7. doctrine/reference docs
8. review and run history
9. governance event history

If two sources disagree, the higher precedence source wins.

## 11. Workbench Contract

The Workbench should show:

- live operator truth by default
- execution cockpit state
- review/apply history
- memory governance
- governance posture
- workspace lane
- knowledge authority summary

It should not make demo or browser-verification residue look like live operator truth.

## 12. Security / Ops Closeout

The remaining manual security closeout is:

- rotate the OpenRouter key

The repo now includes a local helper for this process, but account-side key
revocation still must happen in the OpenRouter dashboard.

## 13. Local Runtime Data

Some data under the repo exists only as local runtime state.

Current rule:

- `data/chroma/` is a local Chroma runtime store
- it is rebuildable cache/state, not canonical product source
- runtime sqlite contents should stay local and should not be treated as documentation, memory truth, or product-owned data
- docs, code, and governed stores outrank local vector-cache state for system truth
