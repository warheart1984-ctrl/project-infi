# AAIS Status Audit

Snapshot date: 2026-04-29

This file is the working inventory of what is clearly documented, what is intentionally unfinished, and what currently needs repair or cleanup.

It is based on:

- current canonical docs in `docs/`
- current runtime code
- latest verified backend snapshot
- current frontend test/build snapshot for this documentation pass
- current mobile typecheck and dependency-audit snapshot for this documentation pass

It intentionally treats `docs/archive/source-docx/` as reference material unless the live markdown/code paths point back to it.

## 1. What Is Already Documented

These files currently do a good job of describing the live system or one bounded subsystem:

- [README.md](../../README.md)
  - best high-level summary of the current AAIS runtime, its lanes, and the OTEM boundary
- [AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md)
  - best concise handbook for state hygiene, visibility rules, and the canonical runtime spine
- [AAIS_HUMAN_GUIDE.md](../spine/AAIS_HUMAN_GUIDE.md)
  - human-facing project entry guide
- [AAIS_AI_OPERATING_CONTRACT.md](../spine/AAIS_AI_OPERATING_CONTRACT.md)
  - AI-facing project operating law
- [AAIS_MASTER_SPEC.md](../spine/AAIS_MASTER_SPEC.md)
  - full project spec ledger across the live system
- [STABILIZE_AND_FREE.md](../spine/STABILIZE_AND_FREE.md)
  - canonical project doctrine for governed stability and operator cognitive load reduction
- [AAIS_DOC_PROTOCOL.md](../contracts/AAIS_DOC_PROTOCOL.md)
  - explains how to trust and rank repo docs
- [ARIS_RUNTIME_CONTRACT.md](../contracts/ARIS_RUNTIME_CONTRACT.md)
  - admits ARIS as an embedded AAIS runtime profile and carries the canonical non-copy clause
- [DEPENDENCY_GATE_POLICY.md](../contracts/DEPENDENCY_GATE_POLICY.md)
  - canonical contract for pinned dependency admission, lockfile evidence, and drift rejection
- [TINY_NOVA_CANONICAL.md](../subsystems/nova/TINY_NOVA_CANONICAL.md)
  - canonical markdown source for Tiny/Small Nova identity, memory boundaries, growth stages, and the Jarvis authority split
- [NOVA_HUMAN_GUIDE.md](../subsystems/nova/NOVA_HUMAN_GUIDE.md), [NOVA_AI_OPERATING_CONTRACT.md](../subsystems/nova/NOVA_AI_OPERATING_CONTRACT.md), and [NOVA_STAGE_SPEC.md](../subsystems/nova/NOVA_STAGE_SPEC.md)
  - now describe the live Session Archive boundary as opt-in, local-only, encrypted archive state that re-enters Nova only as explicit document context rather than memory
- [SEAM-SN-001-super-nova-governance-boundary.md](../contracts/seams/SEAM-SN-001-super-nova-governance-boundary.md)
  - canonical seam record for the live guarded Super Nova boundary, including phase gate before execution, watchdog after generation, bounded immune protocol observation, and Project Infi final-truth admission before completion
- [AAIS Documentation Map](../README.md) and [AAIS Spine](../spine/README.md)
  - point readers at the live runtime spine and the project-wide canonical reading path
- [AAIS_RUNTIME_CANONICAL.md](../runtime/AAIS_RUNTIME_CANONICAL.md)
  - practical runtime and workspace map for what is canonical, functional, separate, or archive-only
- [README.md](../../README.md), [AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md), [AAIS_DOC_PROTOCOL.md](../contracts/AAIS_DOC_PROTOCOL.md), [AAIS Documentation Map](../README.md), and [AAIS Spine](../spine/README.md)
  - now agree on Project Infi runtime ownership, the L2 truth guard, Chronos TTL, `WAIT`, recoverable `FRACTURE`, and shared law/logbook handling
- [AAIS_MASTER_SPEC.md](../spine/AAIS_MASTER_SPEC.md), [AAIS_HUMAN_GUIDE.md](../spine/AAIS_HUMAN_GUIDE.md), [AAIS_AI_OPERATING_CONTRACT.md](../spine/AAIS_AI_OPERATING_CONTRACT.md), and the active Nova pack
  - now agree that Super Nova is a live guarded companion lane with `persona_mode=super_nova`, `response_mode=governed_full`, explicit activation, phase-gated execution, bounded immune protocol observation, and Project Infi final-truth admission
- [AAIS_MODULE_GOVERNANCE_PROTOCOL.md](../contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md)
  - admission and immune-law contract for modules
- [AAIS_PROJECT_CLEANUP_AUDIT.md](AAIS_PROJECT_CLEANUP_AUDIT.md)
  - cross-project cleanup inventory for canonical and non-canonical lanes
- [FOLDER_DOCUMENTATION_AUDIT.md](FOLDER_DOCUMENTATION_AUDIT.md)
  - folder-by-folder inventory of which active directories still need a local
    entry document
- [DESKTOP_SYSTEM_DOCUMENTATION_AUDIT.md](DESKTOP_SYSTEM_DOCUMENTATION_AUDIT.md)
  - missing, stale, and non-canonical doc audit relative to the verified
    desktop launcher and packaged shell
- [LOGBOOK.md](LOGBOOK.md)
  - canonical logbook for major project-alignment changes
- [WORKSPACE_INDEX.md](../_archive/legacy/workspace/WORKSPACE_INDEX.md)
  - workspace-support entry point that separates support docs from runtime authority
- [FORGE_CONTRACTOR.md](../contracts/FORGE_CONTRACTOR.md)
  - bounded contractor service contract
- [FORGEEVAL_CONTRACT.md](../contracts/FORGEEVAL_CONTRACT.md)
  - bounded evaluator service contract
- [EVOLVE_ENGINE_CONTRACT.md](../contracts/EVOLVE_ENGINE_CONTRACT.md)
  - bounded evolution/search lane contract
- [../../aais/README.md](../../aais/README.md)
  - local launcher/package entry doc for the verified cross-platform app path
- [../../app/README.md](../../app/README.md)
  - local workflow-shell entry doc for `app/main.py` and related shell modules
- [../../src/README.md](../../src/README.md)
  - local runtime-spine entry doc for the core Jarvis authority files
- [frontend/README.md](../../frontend/README.md)
  - frontend dev/build/test workflow, including workflow smoke context
- [frontend/DEPENDENCY_AUDIT.md](../../frontend/DEPENDENCY_AUDIT.md)
  - current dependency-health summary for the frontend

## 2. Intentionally Unfinished Or Bounded

These are not hidden bugs. They are explicit limits in the current design.

- OTEM is implemented through v5 only.
  - `README.md` calls out the current ceiling explicitly.
  - [src/otem_runtime.py](../../src/otem_runtime.py) keeps OTEM proposal-only and sets `version_ceiling` to `v5`.
  - Out of scope right now: direct execution, workflow creation without confirmation, and durable OTEM writes by default.
- PatchForge is still a review-first planning surface, not a true autonomous patch author.
  - [src/patchforge.py](../../src/patchforge.py) still emits `after_snippet` placeholder text, `status="proposal_only"`, and `preview_only=True`.
  - [src/patch_apply_engine.py](../../src/patch_apply_engine.py) explicitly blocks placeholder text from being applied.
- The remaining manual security closeout is still OpenRouter key rotation.
  - [AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md) still points readers to the current runtime and operator discipline surfaces, while the remaining workspace planning file stays archived.
- [roadmap.csv](../_archive/legacy/workspace/roadmap.csv) is only a thin phase outline.
  - It names Memory Bank, Security Fabric, and Governance Layer, but it is not a maintained progress tracker yet.

## 3. Currently Broken Or Needing Follow-Up

- The major V10 Core contract break from the prior audit pass is now repaired.
  - `v10_runtime` now wraps the real V10 creative core instead of the placeholder action engine.
  - The V10-focused API tests pass again.
- [src/jarvis_modular2.py](../../src/jarvis_modular2.py) is no longer syntactically broken.
  - It now compiles cleanly and is marked as a legacy experimental copy rather than a canonical runtime file.
- The Project Infi runtime seam is now repaired and governed.
  - non-truthful final truth now ends lawfully as `rejected_no_admission`
  - admission no longer runs after untruthful L2 state
  - Chronos TTL, `WAIT`, recovery drift, and recoverable `FRACTURE` are live and tested
- The Super Nova guarded runtime seam is now repaired and documented.
  - Super Nova is no longer described as dormant or future-only in the active truth surfaces
  - the live boundary now reflects phase gate before execution, explicit activation, watchdog enforcement, bounded immune protocol observation, and Project Infi final-truth admission
- The dependency hardening pass is now repaired and deterministic.
  - `api/uv.lock` now resolves `pillow 12.2.0`
  - `frontend/package-lock.json` now carries exact governed versions for `axios`, `follow-redirects`, `lodash`, and `postcss`
  - `mobile/package-lock.json` now carries exact governed versions for `axios`, `@xmldom/xmldom`, `follow-redirects`, `postcss`, and `uuid`
- The detachment governance and ingress identity seams are now repaired.
  - the detachment guard is exposed through governed read and clear API routes
  - message, stream, and compat ingress lanes now preserve distinct bridge route and surface attribution
  - detachment audit labels no longer collapse across API boundaries
- The workflow shell still carries one bridge-era implementation detail that should be revisited later.
  - [app/main.py](../../app/main.py) is now named as the AAIS workflow shell, but it still mounts the legacy Flask bridge for compatibility.
  - That bridge is intentional for now, but it remains a transition seam worth tracking.
- The previous backend deprecation warning is now cleaned up.
  - [app/main.py](../../app/main.py) now uses the maintained `a2wsgi` bridge instead of Starlette's deprecated WSGI middleware.

## 4. Documentation Drift Or Missing Documentation

- The canonical reading set is now aligned on the live runtime spine.
  - [README.md](../../README.md), [AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md), [AAIS_DOC_PROTOCOL.md](../contracts/AAIS_DOC_PROTOCOL.md), [AAIS Documentation Map](../README.md), and [AAIS Spine](../spine/README.md) now agree on:
  - `src/api.py` as the Jarvis runtime authority
  - `app/main.py` as the workflow/onboarding shell and bridge
  - `src/project_infi_state_machine.py` plus `src/project_infi_law.py` as the shared Project Infi runtime substrate
- The active Nova and seam-reading path is now aligned on the live guarded Super Nova lane.
  - the active Nova docs no longer describe Super Nova as unassigned or dormant
  - [SEAM-SN-001-super-nova-governance-boundary.md](../contracts/seams/SEAM-SN-001-super-nova-governance-boundary.md) now records the live boundary law and explicitly notes that ARIS enforcement in this repo is embedded through shared AAIS law rather than a separate service
- ARIS is now active AAIS truth in embedded form.
  - [ARIS_RUNTIME_CONTRACT.md](../contracts/ARIS_RUNTIME_CONTRACT.md), [EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md), and [COLLECTIVE_PATTERN_LEDGER.md](../contracts/COLLECTIVE_PATTERN_LEDGER.md) now agree on the non-copy clause
- Folder-level entry documentation is still incomplete across several active
  code and support directories.
  - [FOLDER_DOCUMENTATION_AUDIT.md](FOLDER_DOCUMENTATION_AUDIT.md) now tracks the
    remaining gaps, especially `api/`, `data/`, `docs/`, `evals/`, and `tests/`
- Desktop-system doc drift is now tracked separately from the broader status
  inventory.
  - [DESKTOP_SYSTEM_DOCUMENTATION_AUDIT.md](DESKTOP_SYSTEM_DOCUMENTATION_AUDIT.md)
    now focuses on the remaining launcher/package docs-tree gap,
    `frontend/README.md` drift, and the non-canonical status of the old
    `COMPONENT_AUDIT.md` inventory
- The runtime-data policy for local Chroma state is explicit.
  - [AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md) and [README.md](../../README.md) treat `data/chroma/` as local rebuildable runtime state rather than canonical source truth.
- The main remaining drift is now mostly confined to archive material.
  - legacy and infrastructure notes have been moved under `docs/archive/`
  - they remain useful as planning/reference material, but they are not the source of current runtime truth

## 5. Verification Snapshot

- Backend tests: latest verified snapshot is `668 passed`, `12 subtests passed`
- Frontend tests: `47 passed`, `0 failed`
- Frontend production build: passes
- Frontend dependency audit: `0 vulnerabilities`
- Mobile dependency audit: `0 vulnerabilities`
- Mobile typecheck: passes
- Link sanity for the updated Super Nova truth surfaces: `SUPER_NOVA_DOC_LINKS_OK`
- The dependency hardening and detachment-governance pass reran the full backend suite, the full frontend test suite, the frontend production build, mobile typecheck, and the frontend/mobile dependency audits.

## 6. Recommended Next Documentation Moves

- Continue adding machine-readable tags or metadata if you want archive classification to be queryable automatically.
- Decide whether to convert more archive lineage into curated markdown summaries or leave it source-only in `docs/archive/source-docx/`.
- Author the highest-priority local entry docs listed in
  [FOLDER_DOCUMENTATION_AUDIT.md](FOLDER_DOCUMENTATION_AUDIT.md), starting with
  `api/`, `tests/`, `evals/`, `data/`, and `docs/`.
- Turn [roadmap.csv](../_archive/legacy/workspace/roadmap.csv) into a real maintained tracker or leave it clearly archived as planning-only material.
