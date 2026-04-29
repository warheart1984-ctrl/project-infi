# Document Corpus Subsystem Audit

Snapshot date: 2026-04-28

This file audits the full AAIS document corpus for feature and subsystem
coverage relative to the current verified desktop system.

The goal is to answer:

- which subsystem families are clearly represented in live AAIS truth
- which ones are only partial or under-documented
- which important families exist only in archive material and have not been
  admitted into active AAIS docs or code

## Corpus Basis

This pass processed the full mirrored document corpus currently reachable from
inside `AAIS-main`:

- `docs/`
- `docs/_archive/workspace_pull/project-infi-root/`
- `docs/_archive/workspace_pull/external-archives/workspace-root-docs/`

Processed counts:

- total documents: `431`
- `.md`: `124`
- `.docx`: `267`
- `.html`: `10`
- `.pdf`: `26`
- `.txt`: `4`

Extraction result:

- extraction failures: `0`

Method:

- read active markdown/text/html directly
- extracted `.docx` bodies from OOXML
- extracted `.pdf` text with PDF parsing
- compared recurring feature/subsystem families against active docs and live
  code in `docs/`, `src/`, `app/`, `forge*`, `evolve_engine/`, `external/`,
  `integrations/`, and `tests/`

## Status Classes

- `covered_live`
  - clearly represented in active AAIS docs and/or runtime code
- `partial_live`
  - has live footprint, but the broader documented family is still only
    partially admitted or under-documented
- `archive_only_high_signal`
  - appears materially in the document corpus but has no active AAIS
    documentation or code footprint
- `reference_not_current`
  - important archive family, but current AAIS truth explicitly does not treat
    it as a distinct live subsystem

## Covered Live

These families are not missing from AAIS. They already have active footprint.

### Cognitive Bridge

- status: `covered_live`
- live evidence:
  - [`src/cognitive_bridge.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/cognitive_bridge.py>)
  - [`src/api.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/api.py>)
  - [`docs/contracts/AAIS_TRACING_PROTOCOL.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/contracts/AAIS_TRACING_PROTOCOL.md>)

### Tracing / Proof Layer

- status: `covered_live`
- live evidence:
  - [`docs/contracts/AAIS_TRACING_PROTOCOL.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/contracts/AAIS_TRACING_PROTOCOL.md>)
  - [`src/governed_direct_pipeline.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/governed_direct_pipeline.py>)
  - [`src/governed_event_chain.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/governed_event_chain.py>)

### Direct Internal Pipeline

- status: `covered_live`
- live evidence:
  - [`src/governed_direct_pipeline.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/governed_direct_pipeline.py>)
  - [`docs/contracts/AAIS_TRACING_PROTOCOL.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/contracts/AAIS_TRACING_PROTOCOL.md>)

### Realtime Event-Cause Predictor

- status: `covered_live`
- live evidence:
  - [`src/realtime_event_cause_predictor.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/realtime_event_cause_predictor.py>)
  - [`docs/contracts/REALTIME_EVENT_CAUSE_PREDICTION_MODULE.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/contracts/REALTIME_EVENT_CAUSE_PREDICTION_MODULE.md>)

### Invariant Engine

- status: `covered_live`
- live evidence:
  - [`src/invariant_engine.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/invariant_engine.py>)
  - [`docs/runtime/AAIS_SUBSYSTEM_SPEC.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/runtime/AAIS_SUBSYSTEM_SPEC.md>)

### OTEM

- status: `covered_live`
- live evidence:
  - [`src/otem_runtime.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/otem_runtime.py>)
  - [`docs/runtime/AAIS_SUBSYSTEM_SPEC.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/runtime/AAIS_SUBSYSTEM_SPEC.md>)

### Nova / Super Nova

- status: `covered_live`
- live evidence:
  - [`docs/subsystems/nova/NOVA_STAGE_SPEC.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/subsystems/nova/NOVA_STAGE_SPEC.md>)
  - [`src/conversation_memory.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/conversation_memory.py>)
  - [`src/super_nova_gate.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/super_nova_gate.py>)

### Beatbox

- status: `covered_live`
- live evidence:
  - [`external/ai/beatbox/adapter.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/external/ai/beatbox/adapter.py>)
  - [`integrations/contracts/beatbox_contract.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/integrations/contracts/beatbox_contract.md>)

### Jarvis Memory Board

- status: `covered_live`
- live evidence:
  - [`src/jarvis_memory_board.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/jarvis_memory_board.py>)
  - [`docs/contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md>)

## Partial Or Under-Documented

These families are important and present, but not fully surfaced as first-class
active subsystem contracts yet.

### Immune Protocol

- status: `covered_live`
- why:
  - the live runtime has immune behavior and code
  - AAIS now has a dedicated active contract file for the immune layer
- live evidence:
  - [`src/immune_protocol.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/immune_protocol.py>)
  - [`src/immune_system.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/immune_system.py>)
  - [`docs/contracts/AAIS_IMMUNE_PROTOCOL.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/contracts/AAIS_IMMUNE_PROTOCOL.md>)
- archive lineage:
  - [AAIS Immune Protocol.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/AAIS Immune Protocol.docx>)

### Swarm Law

- status: `partial_live`
- why:
  - live code already routes swarm-originated bridge traffic
  - the archive corpus contains a distinct swarm-law family
  - AAIS now has an active Swarm Law contract, but the broader multi-agent
    field-runtime embodiment remains partial rather than fully installed
- live evidence:
  - [`src/cognitive_bridge.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/cognitive_bridge.py>)
  - [`src/governed_direct_pipeline.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/governed_direct_pipeline.py>)
  - [`docs/contracts/SWARM_LAW.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/contracts/SWARM_LAW.md>)
- archive lineage:
  - [swarm law (2).docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/swarm law (2).docx>)

### Story Forge

- status: `partial_live`
- why:
  - Story Forge has active subsystem presence
  - the archive corpus shows a much broader pipeline family than the current
    live docs surface
  - the current admitted subsystem pack is still thin compared with the archive
    design depth
- live evidence:
  - [`docs/subsystems/storyforge/README.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/subsystems/storyforge/README.md>)
  - [`src/capabilities/story_forge_audio.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/capabilities/story_forge_audio.py>)
- archive lineage:
  - [Story Forge.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Story Forge.docx>)
  - [story_forge_pipeline_v1_1.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/story_forge_pipeline_v1_1.docx>)
  - [# src_story_forge_movie_renderer.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/# src_story_forge_movie_renderer.docx>)

### Multi-LLM Provider Governance

- status: `partial_live`
- why:
  - the live repo has governed LLM/module work and lane routing
  - the archive corpus contains a broader `Jarvis Multi-LLM Fabric` concept
  - there is no admitted active contract named as the wider fabric
- live evidence:
  - [`src/aais_llm_lanes.py.txt`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/aais_llm_lanes.py.txt>)
  - [`src/cognitive_bridge.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/cognitive_bridge.py>)
- archive lineage:
  - [Jarvis Multi-LLM Fabric.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Jarvis Multi-LLM Fabric.docx>)

## Archive-Only High-Signal Families

These are the strongest document families that still have no active AAIS
documentation or runtime/code footprint.

### Collective Pattern Ledger

- status: `partial_live`
- why it matters:
  - it is framed as an integration contract and links directly to admission,
    classification, severity, immune routing, and guidance
  - it is now admitted into active AAIS law, but runtime coverage is still
    strongest in EvolveEngine rather than universal across all AAIS lanes
- live evidence:
  - [`docs/contracts/COLLECTIVE_PATTERN_LEDGER.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/contracts/COLLECTIVE_PATTERN_LEDGER.md>)
  - [`evolve_engine/trace_store.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/evolve_engine/trace_store.py>)
  - [`evolve_engine/service.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/evolve_engine/service.py>)
- archive evidence:
  - [Collective Pattern Ledger — Integration Contract.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Collective Pattern Ledger — Integration Contract.docx>)
  - [hall of fame_shame real world feature.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/hall of fame_shame real world feature.docx>)

### Bloodrose

- status: `archive_only_high_signal`
- why it matters:
  - it appears as a full subsystem family with contractor, render, operator,
    event-table, and integration docs
- archive evidence:
  - [Bloodrose — Modular Architecture Document v0.1.pdf](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Bloodrose — Modular Architecture Document v0.1.pdf>)
  - [Bloodrose — Render Pipeline Spec v0.1.pdf](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Bloodrose — Render Pipeline Spec v0.1.pdf>)
  - [Bloodrose — Story Forge Integration Layer v0.1.pdf](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Bloodrose — Story Forge Integration Layer v0.1.pdf>)

### Lumen

- status: `archive_only_high_signal`
- why it matters:
  - the corpus carries embodiment and voice doctrine material
  - there is no real active AAIS subsystem pack or runtime contract for it
- archive evidence:
  - [📜 LUMEN EMBODIMENT SPEC — v1.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/📜 LUMEN EMBODIMENT SPEC — v1.docx>)
  - [lumen_voice_doctrine.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/lumen_voice_doctrine.docx>)

### World Pack / Text-to-3D / 3D Print

- status: `archive_only_high_signal`
- why it matters:
  - the corpus contains a coherent world-generation and output-production
    family
  - there is no active subsystem entry for it in current AAIS docs
- archive evidence:
  - [🕯️ WORLD PACK_.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/🕯️ WORLD PACK_.docx>)
  - [Text‑to‑3D world pipeline (single giant chain).docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Text‑to‑3D world pipeline (single giant chain).docx>)
  - [3d print lane.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/3d print lane.docx>)

### Recipe Module

- status: `archive_only_high_signal`
- archive evidence:
  - [Recipe module (1).docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Recipe module (1).docx>)
  - [recipemodule.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/recipemodule.docx>)

### Imagine Generator / Pattern

- status: `archive_only_high_signal`
- archive evidence:
  - [Imagine generator.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Imagine generator.docx>)
  - [Imagine pattern.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Imagine pattern.docx>)

### Human Notes / Voice Extraction

- status: `archive_only_high_signal`
- archive evidence:
  - [human_notes_extraction.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/human_notes_extraction.docx>)
  - [Jon Halstead - Human Voice Extracted.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Jon Halstead - Human Voice Extracted.docx>)

### Render Adapter Layer

- status: `archive_only_high_signal`
- archive evidence:
  - [multi adapter for rendering.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/multi adapter for rendering.docx>)
  - [multi adapter for rendering (1).docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/multi adapter for rendering (1).docx>)

## Reference But Not Current Live Subsystem

### ARIS Runtime Family

- status: `partial_live`
- why:
  - the corpus contains many ARIS runtime and pipeline docs
  - AAIS now admits ARIS as an embedded runtime profile through the shared
    bridge and Project Infi law surfaces
  - the broader standalone ARIS pipeline family remains lineage rather than a
    separate live service in this repository
- archive evidence:
  - [Aris Pipeline.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Aris Pipeline.docx>)
  - [Project Infi - ARIS Unified Runtime Specification v2.0.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Project Infi - ARIS Unified Runtime Specification v2.0.docx>)
- active clarification:
  - [`docs/contracts/ARIS_RUNTIME_CONTRACT.md`](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/contracts/ARIS_RUNTIME_CONTRACT.md>)
  - [`src/aris_integration.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/aris_integration.py>)

## Highest-Signal Missing Or Thin Areas

If the goal is “make sure we did not miss any important subsystem,” the highest
signal remaining gaps are:

1. a fuller Story Forge subsystem pack
2. explicit classification of Bloodrose, Lumen, World/3D, Recipe, Imagine, and
   Human Extraction families as either:
   - future candidates
   - separate reference projects
   - or permanent archive-only lineage

## Bottom Line

No, the repo had not yet captured every important documented feature or
subsystem family.

The biggest true remaining miss from the current live documentation tree is:

- the broader Story Forge pipeline family

The biggest archive-only subsystem families still waiting for an explicit AAIS
decision are:

- Bloodrose
- Lumen
- World Pack / Text-to-3D / 3D Print
- Recipe Module
- Imagine Generator / Pattern
- Human Notes / Voice Extraction
