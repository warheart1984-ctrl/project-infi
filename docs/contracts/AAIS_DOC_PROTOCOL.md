# AAIS Doc Protocol

This file is the protocol for reading, trusting, and integrating the documentation tree inside `AAIS-main`.

It exists because the repo contains multiple document roles that should not be flattened into one authority layer.

## Core Rule

The docs in this repo are authoritative in layers, not all at once.

Authority order:

1. live runtime code
2. canonical current docs
3. foundational lineage docs
4. aspirational or infrastructure docs
5. outside reference projects

If two sources conflict, the higher layer wins.

## Documentation Placement Rule

Documentation now lives in explicit layers:

- `README.md`
  root overview only
- `docs/spine/`
  project-wide canonical spine
- `docs/runtime/`
  runtime and spec surfaces
- `docs/contracts/`
  active law, contracts, and protocols
- `docs/subsystems/`
  subsystem packs
- `docs/audit/`
  audits, status, and canonical logbook
- `docs/_archive/legacy/workspace/`
  workspace-support and reference material
- `docs/_archive/`
  legacy and archive material

Do not treat subsystem docs, workspace docs, or archive docs as if they are interchangeable with the project-wide canonical spine.

## Folder Entry Inheritance Rule

Folder-local entry docs inherit project-wide law.

That includes the external suggestion admission rule:

- outside proposals may be discussed, compared, critiqued, summarized,
  pressure-tested, or used for inspiration in folder docs
- folder docs must not present those proposals as adopted system truth unless
  the admitted form has already been law-filtered and documented

Conversation is not admission.

Folder-local explanation is not admission either.

## Runtime Authority

These files are the real system before any markdown explanation:

- `app/main.py`
- `src/api.py`
- `src/conversation_memory.py`
- `src/jarvis_operator.py`
- `src/project_infi_law.py`
- `src/project_infi_state_machine.py`
- `src/jarvis_protocol.py`
- `src/jarvis_modular.py`
- `src/provider_registry.py`
- `src/run_ledger.py`
- `src/patch_review_store.py`
- `src/v10_runtime.py`
- `src/v8_runtime.py`
- `src/god_brain.py`
- `src/model_routing.py`
- `src/specialist_registry.py`
- `frontend/src/pages/JarvisConsole.jsx`

If a doc says one thing and these files do another, the code is the truth.

Ownership rule:

- `src/api.py` is the source of truth for core Jarvis runtime behavior
- `app/main.py` is the source of truth for the workflow/onboarding shell and compatibility bridge
- the workflow shell may proxy or mount the Flask lane, but it does not silently replace Jarvis authority
- `src/project_infi_state_machine.py` is the source of truth for the governed Project Infi cycle
- `src/project_infi_law.py` is the source of truth for how that cycle binds runtime actions, repo-changing actions, verification, and logbook alignment
- new governed paths should use these shared law primitives instead of inventing local bypass logic

## Canonical Current Docs

The main reading set for the current AAIS system is:

- [../spine/AAIS_HUMAN_GUIDE.md](../spine/AAIS_HUMAN_GUIDE.md)
- [../spine/AAIS_AI_OPERATING_CONTRACT.md](../spine/AAIS_AI_OPERATING_CONTRACT.md)
- [../spine/AAIS_MASTER_SPEC.md](../spine/AAIS_MASTER_SPEC.md)
- [../spine/STABILIZE_AND_FREE.md](../spine/STABILIZE_AND_FREE.md)
- [README.md](../../README.md)
- [../runtime/AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md)
- [../runtime/AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md)
- [../contracts/AAIS_DOC_PROTOCOL.md](../contracts/AAIS_DOC_PROTOCOL.md)
- [../contracts/SEAM_LAW.md](../contracts/SEAM_LAW.md)
- [../contracts/SEAM_TEST_CHECKLIST.md](../contracts/SEAM_TEST_CHECKLIST.md)
- [../contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
- [../contracts/ARIS_RUNTIME_CONTRACT.md](../contracts/ARIS_RUNTIME_CONTRACT.md)
- [../contracts/seams/SEAM-VC-002-visible-scaffold-leakage.md](../contracts/seams/SEAM-VC-002-visible-scaffold-leakage.md)
- [../contracts/seams/SEAM-SN-001-super-nova-governance-boundary.md](../contracts/seams/SEAM-SN-001-super-nova-governance-boundary.md)
- [../spine/README.md](../spine/README.md)
- [../audit/AAIS_STATUS_AUDIT.md](../audit/AAIS_STATUS_AUDIT.md)
- [../runtime/AAIS_RUNTIME_CANONICAL.md](../runtime/AAIS_RUNTIME_CANONICAL.md)
- [../contracts/JARVIS_PROTOCOL.md](../contracts/JARVIS_PROTOCOL.md)
- [../contracts/AAIS_UL_DOCTRINE.md](../contracts/AAIS_UL_DOCTRINE.md)
- [../runtime/SPECIALIST_REGISTRY_SPEC.md](../runtime/SPECIALIST_REGISTRY_SPEC.md)
- [../_archive/legacy/workspace/WORKSPACE_INDEX.md](../_archive/legacy/workspace/WORKSPACE_INDEX.md)

Project-wide doc spine rule:

- humans start with [../spine/AAIS_HUMAN_GUIDE.md](../spine/AAIS_HUMAN_GUIDE.md)
- AIs and builders start with [../spine/AAIS_AI_OPERATING_CONTRACT.md](../spine/AAIS_AI_OPERATING_CONTRACT.md)
- exact subsystem and ownership detail starts with [../spine/AAIS_MASTER_SPEC.md](../spine/AAIS_MASTER_SPEC.md)
- subsystem packs like Nova live beneath that spine in `docs/subsystems/`
- subsystem design notes such as Nova touch-input doctrine may explain future
  surfaces, but they must not be read as proof of live runtime behavior unless
  code and tests confirm them

## Stabilize And Free

[Stabilize and Free](../spine/STABILIZE_AND_FREE.md) is the canonical doctrine for documentation placement as well as runtime behavior.

That means:

- stabilize truth first through explicit ownership, verified references, and bounded document layers
- free the operator second by making correctness, flow, and reference easy to carry from the docs themselves

If the document tree is not stable, it cannot legitimately reduce operator cognitive load.

## Foundation And Archive Docs

Use archive material for lineage, not for active override.

Examples:

- `docs/_archive/legacy/doctrine/`
- `docs/_archive/raw_imports/`
- `docs/_archive/legacy/infrastructure/`

Use them for:

- doctrine intent
- older boundary language
- planning or design lineage

Do not use them to override runtime behavior directly.

## Integration Protocol

When pulling ideas from docs into the runtime, use this order:

1. confirm the idea is still compatible with runtime code
2. confirm it does not violate UL, protocol, or guardrails
3. identify whether it belongs to:
   - shell
   - protocol
   - provider fabric
   - specialist layer
   - workbench/tools
   - doctrine/guardrail layer
4. if the idea is external, apply the external suggestion admission rule before adoption and preserve the ARIS non-copy clause while doing it
5. implement it in a modular zone
6. expose it through one runtime truth, not parallel logic
7. add tests or an inspectable API surface

## Shared State Rule

AAIS should use one shared state hygiene taxonomy across:

- memories
- runs
- reviews
- governance
- Workbench projections

Do not collapse:

- `state_class`
- `truth_status`
- `retention_status`

Use shared helpers instead of local surface logic:

- `is_operator_visible(record)`
- `retention_policy_for(record)`
- `badge_for_state(record)`
- `precedence_rank(source_type, truth_status)`

If a surface invents its own interpretation of live/demo/test truth, drift has already started.

## Knowledge Authority Rule

AAIS should expose one canonical knowledge authority layer that explains:

- which knowledge source is being shown
- what truth status it carries
- what precedence it has
- what wins if sources disagree

Memory, document knowledge, live research, workspace intel, and doctrine docs should project through one authority snapshot instead of acting like unrelated islands.

## Merge Rules

When borrowing from sibling projects or older docs:

- `AAIS-main` stays the active base
- reference repos are sources of ideas, not replacements
- nothing enters Jarvis raw
- external suggestions may pressure or inspire the system, but they do not become truth without law-filtered admitted form
- raw outside proposals and private runs stay local; only admitted, abstracted, or signature-only forms may move forward
- new subsystems must speak the existing Jarvis protocol or UL shape
- visible guardrail state must come from one canonical runtime evaluation
- external ideas may enrich the shell, but they do not redefine Jarvis identity

## Reading Order

If someone needs to understand the repo quickly, use this order:

1. [README.md](../../README.md)
2. [../spine/AAIS_HUMAN_GUIDE.md](../spine/AAIS_HUMAN_GUIDE.md)
3. [../spine/AAIS_AI_OPERATING_CONTRACT.md](../spine/AAIS_AI_OPERATING_CONTRACT.md)
4. [../spine/STABILIZE_AND_FREE.md](../spine/STABILIZE_AND_FREE.md)
5. [../spine/AAIS_MASTER_SPEC.md](../spine/AAIS_MASTER_SPEC.md)
6. [../runtime/AAIS_RUNTIME_GUIDE.md](../runtime/AAIS_RUNTIME_GUIDE.md)
7. [../runtime/AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md)
8. [../spine/README.md](../spine/README.md)
9. [../audit/AAIS_STATUS_AUDIT.md](../audit/AAIS_STATUS_AUDIT.md)
10. [../runtime/AAIS_RUNTIME_CANONICAL.md](../runtime/AAIS_RUNTIME_CANONICAL.md)
11. [../contracts/JARVIS_PROTOCOL.md](../contracts/JARVIS_PROTOCOL.md)
12. [../contracts/SEAM_LAW.md](../contracts/SEAM_LAW.md)
13. [../contracts/SEAM_TEST_CHECKLIST.md](../contracts/SEAM_TEST_CHECKLIST.md)
14. [../contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
15. [../contracts/seams/SEAM-VC-002-visible-scaffold-leakage.md](../contracts/seams/SEAM-VC-002-visible-scaffold-leakage.md)
16. [../contracts/seams/SEAM-SN-001-super-nova-governance-boundary.md](../contracts/seams/SEAM-SN-001-super-nova-governance-boundary.md)
17. [../contracts/AAIS_UL_DOCTRINE.md](../contracts/AAIS_UL_DOCTRINE.md)
18. [../runtime/SPECIALIST_REGISTRY_SPEC.md](../runtime/SPECIALIST_REGISTRY_SPEC.md)
19. [../_archive/legacy/workspace/WORKSPACE_INDEX.md](../_archive/legacy/workspace/WORKSPACE_INDEX.md)

After that, read runtime code.

## Decision Rule

Before accepting a doc-driven idea into AAIS, ask:

- is it live truth, lineage, or aspiration
- where does it plug into the current spine
- does it preserve protocol and guardrail integrity
- is it inspectable
- is `AAIS-main` still the owning shell after the change

If those answers are unclear, the idea is not ready yet.
