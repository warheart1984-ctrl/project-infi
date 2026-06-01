# AAIS Runtime Canonical

This file explains the current project map around AAIS, what is live now, what
is functional but separate, and what is still reference-only.

This is not a full audit.

It is the practical answer to:

- what the canonical AAIS project is
- what else exists in the workspace
- what is actually functional right now
- what is not part of the live AAIS runtime

Current rule:

- `AAIS-main` is the canonical project
- the workspace contains other projects, references, and archives
- a project can be functional without being canonical
- in-progress lanes inside `AAIS-main` do not become canonical just because
  files exist in the worktree
- AAIS behaves as an organismic system: layered, role-specialized,
  self-protective, and adaptive without surrendering identity
- surface priority does not replace authority; promoting Nova must not
  de-route Jarvis

## 1. Canonical Decision

The live AAIS product is:

- `AAIS-main`

That is the system that currently owns:

- the Jarvis runtime
- the Jarvis Console
- the Workbench
- the memory/governance stack
- the review/apply flow
- the state hygiene and knowledge authority layer
- the current local-first operator shell

If another project disagrees with `AAIS-main`, `AAIS-main` wins for current
runtime truth.

## 2. Workspace Project Map

### `AAIS-main`

Status:

- canonical
- functional
- active development base

What it is:

- the real AAIS/Jarvis desktop and local product shell
- the only project that should define current AAIS runtime truth

What is functional now:

- cross-platform `python -m aais` launcher and packaged `/app` shell
- Flask backend and Jarvis API surface
- Jarvis Console
- Workbench
- Memory Bank
- Mission Board
- patch review/apply gate
- run ledger
- governance, security, immune, continuity, and state hygiene layers
- V9 and V10 bounded creative runtimes
- knowledge authority snapshot
- OTEM reason-only lane under Jarvis authority
- Small Nova home surface under Jarvis authority
- Tiny Nova as the lighter bounded companion tier beneath Small Nova
- Forge contractor lane
- ForgeEval evaluator lane
- EvolveEngine mutation/search lane with Hall of Fame and Hall of Shame traces

What still needs bounded ownership discipline:

- active lanes only count as canonical when they are documented, bounded, and
  integrated into the cross-lane rules
- workflow/onboarding surfaces are now treated as canonical workflow-shell
  surfaces, but they still do not override Jarvis runtime authority in
  `src/api.py`

### `NVIDIA`

Status:

- separate
- functional as its own repo
- non-canonical for AAIS

What it is:

- a separate private API / Spiral research sandbox

What is functional:

- its own repo structure and app surface

What it is not:

- not the AAIS base
- not the current Jarvis runtime

### `mystic`

Status:

- separate
- functional as its own repo
- non-canonical for AAIS

What it is:

- a separate small project with its own frontend/repo identity

What is functional:

- its own project shell

What it is not:

- not the AAIS runtime
- not a drop-in replacement for Jarvis

### `Ui jarvis`

Status:

- reference
- partial / prototype
- non-canonical

What it is:

- a visual and voice reference lane

What is still useful:

- Jarvis identity direction
- orb / command-deck visual language
- voice-first interaction ideas

What is not functional in AAIS terms:

- not the maintained runtime base
- not the source of truth for backend behavior

### `code`

Status:

- reference container
- partially mined
- non-canonical

What it is:

- a workspace bucket containing architecture references, including
  `evolving_ai`

What is still useful:

- provider abstraction patterns
- workspace/review/execution ideas
- memory / approval / agent-run lineage

What is not functional as one project:

- it is not one clean current product
- it should be mined selectively, not adopted whole

### `jarvis`

Status:

- reference
- structurally messy
- non-canonical

What it is:

- an older feature-heavy Jarvis project tree

What is still useful:

- longer-term ideas around jobs, assistants, RAG, and orchestration

What is not functional for current AAIS ownership:

- not the live base
- not the cleanest structure
- not the place to anchor current runtime truth

### `Spiral-Companion-main`

Status:

- separate
- substantial reference project
- non-canonical

What it is:

- a separate project with its own direction

What it is not:

- not current AAIS runtime truth
- not the Jarvis operator shell

### `Nova, The North Star`

Status:

- spec / prototype lane
- not integrated as a live product
- non-canonical

What it is:

- concept and prototype material for a user-side cognitive companion

What is useful:

- interface ideas
- cognition-side contracts
- separation-of-minds thinking

What is not functional yet:

- not the live Nova-Jarvis integration layer
- not a shipped runtime in this workspace
- the live AAIS law is stricter: Nova-style companion presence may front the
  surface inside `AAIS-main`, but Jarvis remains the routing and state authority

### `God engine`

Status:

- historical reference
- not live
- non-canonical

What it is:

- older source material that fed later AAIS ideas

What is useful:

- lineage for orchestration, control, and "system as shell" thinking

What is not functional now:

- not the maintained runtime
- not the live operator surface

### `project`

Status:

- storage / scaffold bucket
- non-canonical
- not a current product

What it is:

- loose files, starter material, and workspace overflow

What it is not:

- not a live app
- not a canonical repo

## 3. What Is Live Inside `AAIS-main`

These are the current functional AAIS pillars.

### Desktop / Packaged Shell

- `aais/launcher.py`
- `app/main.py`

Functional now:

- `python -m aais start`, `prepare`, and `doctor`
- packaged frontend serving from `/app`
- one cross-platform launcher path for Windows, Linux, and macOS
- workflow-shell hosting plus compatibility bridge into the canonical Jarvis
  runtime

### Operator Surfaces

- `frontend/src/pages/NovaPage.jsx`
- `frontend/src/pages/JarvisPage.jsx`
- `frontend/src/pages/RepoManager.jsx`
- `frontend/src/pages/MemoryBank.jsx`
- `frontend/src/pages/WorkflowBuilder.jsx`

Functional now:

- Small Nova home surface at `/` and `/nova`
- Jarvis operator console at `/jarvis`
- repo review and management surface at `/jarvis/repo-manager`
- memory editing and governance views at `/memory`
- workflow-shell routes at `/workflows/*` and `/onboarding`
- packaged browser/desktop shell served from `/app`

### Runtime Spine

- `app/main.py`
- `src/api.py`
- `src/conversation_memory.py`
- `src/jarvis_operator.py`
- `src/jarvis_protocol.py`
- `src/jarvis_reasoning_protocol.py`
- `src/provider_mind.py`
- `src/governance_layer.py`

Functional now:

- packaged shell and compatibility bridge ownership
- turn contract resolution
- mode/scope/voice control
- provider routing and fallback containment
- operator-safe response finalization
- Jarvis remains the control lane even when Small Nova fronts the default user
  surface and Tiny Nova is selected as the lighter companion tier

### Governance And State

- `src/state_hygiene.py`
- `src/knowledge_authority.py`
- `src/run_ledger.py`
- `src/patch_review_store.py`
- `src/mission_board.py`

Functional now:

- state class / truth status / retention status taxonomy
- live-vs-all truth scoping
- review and apply gatekeeping
- mission state tracking
- knowledge precedence snapshot

### Creative / Bounded Runtimes

- `src/creative_core_runtime.py`
- `src/v9_runtime.py`
- `src/v10_runtime.py`

Functional now:

- bounded runtime wrappers
- runtime state and event feeds
- Workbench/runtime card visibility

### Reasoning And OTEM

- current OTEM route and turn-contract wiring under Jarvis

Functional now:

- deterministic reason-only OTEM planning
- session-scoped OTEM state
- operator-task posture anchoring

Not yet fully canonical as a larger subsystem:

- broader OTEM evolution stages described in the docs
- any future workflow-heavy OTEM expansion

## 4. Current In-Repo Lanes With Separate Authority Rules

These lanes are present in the current `AAIS-main` worktree and are not all
equal. Some are canonical but scoped. Others remain bounded or non-authoritative.

### Workflow / Onboarding Lane

Examples:

- `frontend/src/pages/WorkflowBuilder.jsx`
- `frontend/src/pages/WorkflowRuns.jsx`
- `frontend/src/pages/WorkflowApprovals.jsx`
- `frontend/src/pages/WorkflowTemplates.jsx`
- `frontend/src/pages/Onboarding.jsx`

Status:

- functional
- canonical as the workflow/onboarding shell
- not the source of core Jarvis runtime truth

Authority rule:

- `app/main.py` owns this shell
- `frontend/src/pages/WorkflowBuilder.jsx`, `WorkflowRuns.jsx`,
  `WorkflowApprovals.jsx`, `WorkflowTemplates.jsx`, and `Onboarding.jsx` are
  live workflow-shell pages, not reference-only prototypes
- the shell may bridge into Flask routes, but `src/api.py` still owns Jarvis
  operator/runtime authority

### Forge / ForgeEval Lane

Examples:

- `forge/`
- `forge_eval/`
- `src/forge_client.py`
- `src/forge_eval_client.py`
- `FORGE_CONTRACTOR.md`
- `FORGEEVAL_CONTRACT.md`

Status:

- bounded service lane
- functional and integrated through explicit contracts
- subordinate to Jarvis authority and bounded-service rules

### Alternate App / Control Lane

Examples:

- `control/`
- `api/`

Status:

- present in worktree
- not current AAIS runtime authority
- should not silently replace `src/api.py` or the canonical workflow shell in `app/main.py`

## 5. Older Files That Became Real AAIS Features

These older ideas are still important, but their live forms now exist elsewhere.

### `core.py` and `angels.py`

They became:

- orchestrator patterns in `src/jarvis_operator.py` and related runtime files
- specialist and routing logic in the current Jarvis stack

### `god_dashboard.py`

It became:

- the Jarvis Console
- the Workbench

### `emergency_stop.py`, `hooks.py`, `killswitch_init.py`, and `killswitch_gui.py`

They became:

- guarded stop/pause/resume behavior
- policy and system-guard posture in the current runtime
- optional local emergency-control tooling for operators

## 6. What Is Reference-Only

These should still be read as lineage or idea sources, not as runtime truth:

- `core.py`
- `angels.py`
- `god_cli.py`
- `god_dashboard.py`
- `emergency_stop.py`
- `hooks.py`
- `killswitch_init.py`
- `killswitch_gui.py`
- most old standalone design notes that describe a system larger than the live
  current runtime

## 7. What Is Functional Versus Canonical

Keep this distinction clear:

- canonical means "current AAIS truth"
- functional means "works as its own thing"

So:

- `AAIS-main` is canonical and functional
- `NVIDIA` and `mystic` appear functional, but are not canonical
- `Ui jarvis`, `code`, `jarvis`, `Nova, The North Star`, and `God engine`
  remain reference or prototype lanes unless explicitly integrated

## 8. Clean Mental Model

If you want the simplest way to think about the workspace now:

- `AAIS-main` is the real product
- other folders are either separate projects or reference reservoirs
- current AAIS truth lives in the launcher, Jarvis runtime, Small Nova home
  surface, and workflow shell inside `AAIS-main`
- presence in the workspace does not equal canonical ownership

## 9. Enforcement Rule

This is not only a description of the workspace.

It is also a runtime governance rule.

### Canonical Enforcement

- no non-canonical project may alter AAIS runtime behavior
- no reference file may override canonical logic
- no external lane becomes authoritative by convenience, proximity, or partial
  implementation
- any integration that affects AAIS runtime behavior must be explicitly declared
  and documented
- silent adoption of external logic is invalid

### Practical Meaning

If behavior changes in the live AAIS runtime, the authority must be visible in:

- `AAIS-main` runtime code
- canonical AAIS docs
- explicit integration points

Not in:

- reference-project files
- copied prototype behavior
- undocumented side lanes
- loose workspace material

### Integration Standard

A cross-project idea is only valid for AAIS when all of these are true:

- it is intentionally pulled into `AAIS-main`
- it is bounded to the Jarvis/AAIS runtime shape
- it is documented as an integration or canonical feature
- it does not silently replace existing canonical authority

If those conditions are not met, the material remains reference-only even if it
is useful, functional elsewhere, or present in the workspace.
