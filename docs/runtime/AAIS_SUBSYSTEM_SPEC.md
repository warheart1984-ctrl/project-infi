# AAIS Subsystem Spec

This file is the structured subsystem map for `AAIS-main`.

It is meant to answer:

- what subsystems are clearly live
- which subsystems are partial, implied, hidden, or only seeded
- what each subsystem owns
- what each subsystem depends on
- what can be activated safely next

If this file conflicts with runtime code, runtime code still wins.

## 1. Status Legend

- `live`
  actively routed or surfaced in the current runtime
- `partial`
  implemented and partially integrated, but not yet the full intended subsystem
- `concept`
  explicit design seed or code library with no complete live runtime role yet
- `dormant`
  intentionally bounded or kept off by default
- `deprecated`
  legacy compatibility or experimental copy; not a current authority surface
- `missing`
  implied externally or by naming, but not actually present as a real subsystem
  in this repository

## 2. Layer Model

AAIS subsystems currently cluster into these architectural layers:

- authority and cognition
- governance, memory, and knowledge
- execution lanes
- product shell and operator surfaces
- hidden or seeded subsystem primitives

## 3. Subsystem Records

### Jarvis Core Runtime

- status: `live`
- primary purpose: main authority shell for turn routing, tool envelopes, reply
  finalization, and operator-visible traces
- architectural layer: authority and cognition
- dependencies:
  - `src/api.py`
  - `src/jarvis_operator.py`
  - `src/conversation_memory.py`
  - `src/jarvis_protocol.py`
  - `src/model_routing.py`
- governed inputs and outputs:
  - input: session state, user turns, tool results, provider results
  - output: turn contracts, responses, response traces, lane metadata
- related files/modules:
  - `src/api.py`
  - `src/jarvis_operator.py`
  - `src/jarvis_protocol.py`
- invariants or doctrine surfaces:
  - `docs/contracts/JARVIS_PROTOCOL.md`
  - `docs/contracts/JARVIS_REASONING_PROTOCOL.md`
  - `docs/spine/AAIS_MASTER_SPEC.md`
- current implementation gaps:
  - still monolithic in `src/api.py`
  - still carries transition-era bridge logic for some neighboring surfaces
- integration risk: `high`
- recommended priority: `P0 maintain`

### Conversation And Continuity Substrate

- status: `live`
- primary purpose: session memory, persona mode, continuity filtering, and
  prompt-lane shaping
- architectural layer: authority and cognition
- dependencies:
  - `src/conversation_memory.py`
  - `src/continuity_profile.py`
  - `src/preference_profile.py`
- governed inputs and outputs:
  - input: turn history, persona mode, continuity profile, session metadata
  - output: filtered memory cues, prompt blocks, companion-safe continuity
- related files/modules:
  - `src/conversation_memory.py`
  - `src/continuity_profile.py`
  - `src/preference_profile.py`
- invariants or doctrine surfaces:
  - `docs/runtime/AAIS_RUNTIME_GUIDE.md`
  - `docs/subsystems/nova/TINY_NOVA_CANONICAL.md`
- current implementation gaps:
  - memory-board law is not yet the single enforcement path for all memory
    writes and reads
- integration risk: `high`
- recommended priority: `P1 harden`

### Jarvis Protocol And Reasoning Fabric

- status: `live`
- primary purpose: shared bounded contract for messages, tools, providers,
  reasoning objectives, and output contracts
- architectural layer: authority and cognition
- dependencies:
  - `src/jarvis_protocol.py`
  - `src/jarvis_reasoning_protocol.py`
  - `src/reasoning_types.py`
- governed inputs and outputs:
  - input: user turn, context hints, mode, lane-specific triggers
  - output: protocol packets, objective selection, reasoning constraints, output
    contracts
- related files/modules:
  - `src/jarvis_protocol.py`
  - `src/jarvis_reasoning_protocol.py`
  - `src/reasoning_types.py`
- invariants or doctrine surfaces:
  - `docs/contracts/JARVIS_PROTOCOL.md`
  - `docs/contracts/JARVIS_REASONING_PROTOCOL.md`
- current implementation gaps:
  - much of the lane logic still lives in one large reasoning file
- integration risk: `high`
- recommended priority: `P0 maintain`

### Orchestration Core

- status: `live`
- primary purpose: God Brain, V8 event spine, specialist selection, and model
  route choice
- architectural layer: authority and cognition
- dependencies:
  - `src/god_brain.py`
  - `src/v8_runtime.py`
  - `src/specialist_registry.py`
  - `src/model_routing.py`
  - `src/provider_mind.py`
- governed inputs and outputs:
  - input: turn metadata, response mode, workspace hints, provider preferences
  - output: route decisions, specialist context, event log state
- related files/modules:
  - `src/god_brain.py`
  - `src/v8_runtime.py`
  - `src/specialist_registry.py`
  - `src/model_routing.py`
  - `src/provider_mind.py`
- invariants or doctrine surfaces:
  - `docs/runtime/SPECIALIST_REGISTRY_SPEC.md`
  - `src/aais_blueprint.py`
- current implementation gaps:
  - authority is explicit, but cross-lane decomposition is still partly implicit
    in code rather than isolated per subsystem
- integration risk: `high`
- recommended priority: `P1 refine`

### Safety And Response Integrity Stack

- status: `live`
- primary purpose: anti-drift, prompt cleanup, output completion, visible
  scaffold suppression, and identity-safe finalization
- architectural layer: authority and cognition
- dependencies:
  - `src/anti_drift.py`
  - `src/prompt_assembly.py`
  - `src/output_completion.py`
  - `src/corrigibility.py`
  - `src/api.py`
- governed inputs and outputs:
  - input: draft reply, prompt blocks, route metadata, output budget metadata
  - output: operator-safe complete reply, cleanup traces, fail-closed notices
- related files/modules:
  - `src/anti_drift.py`
  - `src/prompt_assembly.py`
  - `src/output_completion.py`
  - `src/corrigibility.py`
- invariants or doctrine surfaces:
  - `docs/contracts/SEAM_LAW.md`
  - `docs/contracts/seams/SEAM-VC-002-visible-scaffold-leakage.md`
- current implementation gaps:
  - remote-provider tokenizer precision is still approximate
- integration risk: `high`
- recommended priority: `P0 maintain`

### Direct Challenge And Relational Lane

- status: `live`
- primary purpose: severity-aware handling of personal, confrontational, or
  relational turns
- architectural layer: authority and cognition
- dependencies:
  - `src/direct_challenge_module.py`
  - `src/jarvis_reasoning_protocol.py`
  - `src/api.py`
- governed inputs and outputs:
  - input: direct challenge or relational wording
  - output: severity profile, lane guidance, stabilized reply behavior
- related files/modules:
  - `src/direct_challenge_module.py`
  - `src/jarvis_reasoning_protocol.py`
- invariants or doctrine surfaces:
  - `docs/contracts/DIRECT_CHALLENGE_MODULE.md`
- current implementation gaps:
  - detection remains heuristic and pattern-family based
- integration risk: `medium`
- recommended priority: `P1 extend carefully`

### OTEM Bounded Reasoning Lane

- status: `partial`
- primary purpose: explicit operator task framing, decomposition, and
  proposal-only reasoning
- architectural layer: authority and cognition
- dependencies:
  - `src/jarvis_reasoning_protocol.py`
  - `src/otem_runtime.py`
  - `src/jarvis_operator.py`
  - `src/api.py`
- governed inputs and outputs:
  - input: explicit OTEM invocation plus task clauses and signal clauses
  - output: bounded OTEM plan/proposal, OTEM metadata, no direct execution
- related files/modules:
  - `src/otem_runtime.py`
  - `src/jarvis_reasoning_protocol.py`
  - `src/jarvis_operator.py`
- invariants or doctrine surfaces:
  - `README.md`
  - `docs/spine/AAIS_MASTER_SPEC.md`
- current implementation gaps:
  - explicit ceiling remains `v5`
  - no durable execution layer
  - no autonomous workflow creation
- integration risk: `high`
- recommended priority: `P2 after infrastructure`

### Nova Companion Line

- status: `live`
- primary purpose: Tiny, Small, and guarded Super Nova companion surfaces under Jarvis authority
- architectural layer: authority and cognition
- dependencies:
  - `src/conversation_memory.py`
  - `src/api.py`
  - `frontend/src/pages/NovaLandingPage.jsx`
- governed inputs and outputs:
  - input: companion persona turn and continuity
  - output: bounded companion reply with filtered continuity and optional
    archive-as-document context
- related files/modules:
  - `src/conversation_memory.py`
  - `frontend/src/pages/NovaLandingPage.jsx`
- invariants or doctrine surfaces:
  - `docs/subsystems/nova/TINY_NOVA_CANONICAL.md`
  - `docs/spine/AAIS_MASTER_SPEC.md`
- current implementation gaps:
  - Small Nova still carries the default home-surface bridge role even though
    Super Nova is available as a guarded lane
  - Super Nova immune coupling is currently observe-only; broader
    predictor/invariant-driven immune automation remains blocked until the
    realtime event-cause predictor is installed in the live runtime path and
    the invariant engine is wired as a Nova runtime consumer
  - there is no separate ARIS service in this repo; the active ARIS-equivalent
    enforcement at the Super Nova boundary is the shared Project Infi
    final-truth admission seam
  - touch interaction is document-defined only; live Nova input remains keystroke-first today
- integration risk: `medium`
- recommended priority: `P3 keep bounded`

### Creative Runtimes V9 And V10

- status: `live`
- primary purpose: bounded creative/runtime cores for V9 and V10
- architectural layer: authority and cognition
- dependencies:
  - `src/creative_core_runtime.py`
  - `src/v9_runtime.py`
  - `src/v10_runtime.py`
  - `src/v9_core.py`
  - `src/v10_core.py`
  - `src/jarvis_operator.py`
- governed inputs and outputs:
  - input: creative or core prompt/tool request
  - output: bounded creative run state and result trace
- related files/modules:
  - `src/creative_core_runtime.py`
  - `src/v9_runtime.py`
  - `src/v10_runtime.py`
- invariants or doctrine surfaces:
  - `README.md`
  - `src/aais_blueprint.py`
- current implementation gaps:
  - these remain specialized lanes, not a generalized subsystem substrate
- integration risk: `medium`
- recommended priority: `P2 after core hardening`

### Dreamspace

- status: `dormant`
- primary purpose: optional reflective background cognition
- architectural layer: authority and cognition
- dependencies:
  - `src/dreamspace.py`
  - `src/api.py`
  - `src/v8_runtime.py`
  - `src/system_guard.py`
- governed inputs and outputs:
  - input: idle-safe context packet and manual or environment-triggered actions
  - output: guarded background reflections and mirrored event-log entries
- related files/modules:
  - `src/dreamspace.py`
  - `src/api.py`
- invariants or doctrine surfaces:
  - `src/aais_blueprint.py`
- current implementation gaps:
  - optional and off by default
  - not suitable to expand before memory and governance tighten further
- integration risk: `medium`
- recommended priority: `P3 dormant`

### Universal Language And Modular Preview

- status: `live`
- primary purpose: UL payload shaping and doctrine-aware modular context
  assembly on ordinary chat turns, forge contractors, and governed runtime surfaces
- architectural layer: authority and cognition
- dependencies:
  - `src/aais_ul.py`
  - `src/jarvis_modular.py`
  - `src/writers_3_rules.py`
  - `src/angels_and_wards.py`
  - `src/six_wards_guardrails.py`
- governed inputs and outputs:
  - input: modular context fragments and doctrine state
  - output: UL snapshots and doctrine-bearing payloads
- related files/modules:
  - `src/aais_ul.py`
  - `src/cisiv.py`
  - `src/chat_turn_governance.py`
  - `src/jarvis_modular.py`
  - `src/writers_3_rules.py`
  - `src/angels_and_wards.py`
  - `src/six_wards_guardrails.py`
- invariants or doctrine surfaces:
  - `docs/contracts/AAIS_UL_DOCTRINE.md`
- current implementation gaps:
  - full Project Infi cycle on every repo mutation path beyond patch apply remains partial
  - UL App Bridge and voice bind remain OS-level future work
- admission posture:
  - ordinary chat turns: Project Infi verification admission via `finalize_chat_turn_admission()`
  - forge/evolve contractors: governed runtime admission via `src/forge_repo_governance.py`
  - patch review lifecycle: create/decision/apply each carry Project Infi metadata
  - tool-result and Super-Nova turns: specialized admission paths remain separate
- integration risk: `medium`
- recommended priority: `P2 after infrastructure`

### Governed Direct Pipeline

- status: `partial`
- primary purpose: explicit fast-lane vs service-lane packet tracing
- architectural layer: authority and cognition
- dependencies:
  - `src/governed_direct_pipeline.py`
  - `src/api.py`
  - `src/immune_protocol.py`
- governed inputs and outputs:
  - input: turn context and tool-result context
  - output: packetized pipeline trace and lane metadata
- related files/modules:
  - `src/governed_direct_pipeline.py`
  - `src/api.py`
- invariants or doctrine surfaces:
  - `tests/test_governed_direct_pipeline.py`
  - `docs/contracts/SEAM_LAW.md`
  - `docs/contracts/SWARM_LAW.md`
- current implementation gaps:
  - integrated as trace and packet contract, not yet the full runtime transport
    substrate
  - swarm-originated doctrine is admitted, but the broader multi-agent field
    runtime remains partial rather than installed as a first-class subsystem
- integration risk: `medium`
- recommended priority: `P2 after infrastructure`

### Realtime Event-Cause Predictor

- status: `concept`
- primary purpose: compact fast-lane event and cause forecasting
- architectural layer: authority and cognition
- dependencies:
  - `src/realtime_event_cause_predictor.py`
  - `src/governed_direct_pipeline.py`
- governed inputs and outputs:
  - input: local realtime deltas
  - output: compact `rt` packets with event and cause forecasts
- related files/modules:
  - `src/realtime_event_cause_predictor.py`
- invariants or doctrine surfaces:
  - `docs/contracts/REALTIME_EVENT_CAUSE_PREDICTION_MODULE.md`
- current implementation gaps:
  - no live sensor or session producer is wired into the runtime
  - not yet sufficient as the installed event substrate for Nova immune coupling
- integration risk: `medium_high`
- recommended priority: `P2 blocked by feed infrastructure`

### Perception, Spatial, And Mystic Toolkit

- status: `partial`
- primary purpose: spatial reasoning, symbolic reading, and document or UI
  perception
- architectural layer: authority and cognition
- dependencies:
  - `src/Spatial_reasoning.py`
  - `src/mystic_engine.py`
  - `src/document_vision.py`
  - `src/ui_vision.py`
  - `src/jarvis_operator.py`
  - `src/api.py`
- governed inputs and outputs:
  - input: structured tool request or attached content
  - output: bounded tool result
- related files/modules:
  - `src/Spatial_reasoning.py`
  - `src/mystic_engine.py`
  - `src/document_vision.py`
  - `src/ui_vision.py`
- invariants or doctrine surfaces:
  - `src/aais_blueprint.py`
  - capability-bridge traces
- current implementation gaps:
  - mixed maturity
  - vision and perception paths are not yet universally routed through one
    capability boundary
- integration risk: `medium`
- recommended priority: `P1 unify`

### Project Infi Runtime

- status: `live`
- primary purpose: governed cycle for admission, wait, fracture, record, and
  truth guard
- architectural layer: governance, memory, and knowledge
- dependencies:
  - `src/project_infi_state_machine.py`
  - `src/project_infi_law.py`
  - `src/governance_layer.py`
  - `src/run_ledger.py`
- governed inputs and outputs:
  - input: proposed change, verification context, legitimacy context
  - output: lawful disposition, carryover state, judgment log, stage records
- related files/modules:
  - `src/project_infi_state_machine.py`
  - `src/project_infi_law.py`
  - `src/run_ledger.py`
- invariants or doctrine surfaces:
  - `docs/spine/AAIS_MASTER_SPEC.md`
  - `docs/spine/AAIS_AI_OPERATING_CONTRACT.md`
- current implementation gaps:
  - many neighboring lanes still bind into Project Infi unevenly
- integration risk: `very_high`
- recommended priority: `special_review_only`

### Governance, Security, And Immune Stack

- status: `live`
- primary purpose: policy, break-glass, security decisions, and immune
  monitoring and escalation
- architectural layer: governance, memory, and knowledge
- dependencies:
  - `src/governance_layer.py`
  - `src/security_protocol_core.py`
  - `src/immune_system.py`
  - `src/immune_protocol.py`
  - `src/system_guard.py`
- governed inputs and outputs:
  - input: incidents, policy requests, security decisions, pause or break-glass
    actions
  - output: posture snapshots, governance events, incidents, control decisions
- related files/modules:
  - `src/governance_layer.py`
  - `src/security_protocol_core.py`
  - `src/immune_system.py`
  - `src/immune_protocol.py`
  - `src/system_guard.py`
- invariants or doctrine surfaces:
  - `docs/contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md`
  - `docs/contracts/AAIS_IMMUNE_PROTOCOL.md`
  - `docs/contracts/SEAM_LAW.md`
- current implementation gaps:
  - cross-system incident choreography is still more code-local than
    subsystem-contract local
- integration risk: `very_high`
- recommended priority: `special_review_only`

### Module Governance And Phase Gate

- status: `partial`
- primary purpose: module admission, CISIV posture, and controlled activation
  contexts
- architectural layer: governance, memory, and knowledge
- dependencies:
  - `src/module_governance.py`
  - `src/phase_gate.py`
  - `src/cisiv.py`
  - `src/capability_service_bridge.py`
- governed inputs and outputs:
  - input: module or component registration, promotion, demotion, runtime
    context
  - output: allow or block decisions and auditable phase events
- related files/modules:
  - `src/module_governance.py`
  - `src/phase_gate.py`
  - `src/cisiv.py`
- invariants or doctrine surfaces:
  - `docs/contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md`
- current implementation gaps:
  - strongly live through the capability bridge, not yet universal across every
    subsystem
- integration risk: `high`
- recommended priority: `P1 expand`

### Memory Governance Stack

- status: `partial`
- primary purpose: memory board, curation, protected installs, and durable vs
  stale memory management
- architectural layer: governance, memory, and knowledge
- dependencies:
  - `src/jarvis_memory_board.py`
  - `src/conversation_memory.py`
  - `src/memory_smith.py`
  - `src/jarvis_operator.py`
  - `src/api.py`
- governed inputs and outputs:
  - input: memory candidates, slot operations, curation context
  - output: board snapshots, promotion or expiry decisions, scoped memory state
- related files/modules:
  - `src/jarvis_memory_board.py`
  - `src/memory_smith.py`
  - `src/conversation_memory.py`
  - `src/jarvis_operator.py`
- invariants or doctrine surfaces:
  - `docs/contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md`
  - `docs/contracts/JARVIS_PROTOCOL.md`
- current implementation gaps:
  - the board exists and is inspectable, but not all memory paths are yet
    board-governed
- integration risk: `high`
- recommended priority: `P1 best_next_activation`

### Mission Board

- status: `live`
- primary purpose: durable objective layer above a single turn
- architectural layer: governance, memory, and knowledge
- dependencies:
  - `src/mission_board.py`
  - `src/api.py`
  - `src/verification_gate.py`
  - frontend operator surfaces
- governed inputs and outputs:
  - input: mission creation, presets, critic reviews, verification results
  - output: mission state, verification gate state, activity history
- related files/modules:
  - `src/mission_board.py`
  - `src/api.py`
- invariants or doctrine surfaces:
  - `docs/spine/AAIS_MASTER_SPEC.md`
  - `docs/runtime/AAIS_RUNTIME_GUIDE.md`
- current implementation gaps:
  - not yet the universal mission authority for every execution lane
- integration risk: `medium`
- recommended priority: `P1 expand`

### Knowledge Authority, Live Research, And Document Intelligence

- status: `live`
- primary purpose: combine memory, workspace, doctrine, document, and research
  without flattening source truth
- architectural layer: governance, memory, and knowledge
- dependencies:
  - `src/knowledge_authority.py`
  - `src/live_research.py`
  - `src/document_rag.py`
  - `src/document_vision.py`
  - `src/api.py`
- governed inputs and outputs:
  - input: session state, authority preferences, optional research and document
    sources
  - output: authority snapshot with precedence and source-type separation
- related files/modules:
  - `src/knowledge_authority.py`
  - `src/live_research.py`
  - `src/document_rag.py`
  - `src/document_vision.py`
- invariants or doctrine surfaces:
  - `docs/runtime/AAIS_RUNTIME_GUIDE.md`
  - `docs/contracts/AAIS_DOC_PROTOCOL.md`
- current implementation gaps:
  - document ingestion and retrieval exist, but deeper authority-aware retrieval
    remains modest
- integration risk: `medium`
- recommended priority: `P1 build_now`

### Invariant Engine

- status: `concept`
- primary purpose: cross-domain invariant calculations for matrix, polynomial,
  topological, and statistical checks
- architectural layer: governance, memory, and knowledge
- dependencies:
  - `src/invariant_engine.py`
  - `src/invariants_calculator.py`
- governed inputs and outputs:
  - input: mathematical structures
  - output: invariant report
- related files/modules:
  - `src/invariant_engine.py`
  - `src/invariants_calculator.py`
- invariants or doctrine surfaces:
  - code and tests only
- current implementation gaps:
  - no clear canonical runtime consumer
  - not yet wired to Nova anchor and invariant comparison at runtime
- integration risk: `medium`
- recommended priority: `P3 dormant`

### Project Scorpion (OS Anomaly Extractor)

- status: `partial`
- primary purpose: governed OS-level anomaly extraction from behavioral invariant
  traces; fixture Sentinel in Stage 1, kernel Sentinel deferred to Stage 4
- architectural layer: execution lanes / OS forensics (isolated from `src/*`)
- dependencies:
  - `scorpion/scorpion.py`
  - `scorpion/invariants/os_invariants.v1.json`
  - `docs/subsystems/scorpion/SCORPION_BLUEPRINT.md`
- governed inputs and outputs:
  - input: normalized trace events (`scorpion.event.v1`)
  - output: drift scan, ledger claims, sandbox extraction, reconstruction plans,
    health drift index
- related files/modules:
  - `scorpion/`
  - `tests/test_scorpion.py`
  - `docs/proof/scorpion/`
- invariants or doctrine surfaces:
  - `docs/subsystems/scorpion/SCORPION_BLUEPRINT.md`
  - `docs/subsystems/scorpion/SCORPION_CLI_CONTRACT.md`
  - `META_ARCHITECT_LAWBOOK.md`
  - `REPO_PROOF_LAW.md`
- current implementation gaps:
  - no live kernel Sentinel (eBPF/auditd); `KernelSentinel` is stub only
  - Wolf CoG post-build ingest documented but inactive
  - no `src/scorpion_bridge.py` Jarvis handoff yet
- integration risk: `medium`
- recommended priority: `P2 after core hardening` (parallel sibling to Forgekeeper)

### Capability Module Layer And Service Bridge

- status: `partial`
- primary purpose: normalize external capability execution through one governed
  bridge
- architectural layer: execution lanes
- dependencies:
  - `src/capability_module.py`
  - `src/aais_capability_module.py`
  - `src/capability_service_bridge.py`
  - `src/jarvis_operator.py`
  - `src/api.py`
  - `src/phase_gate.py`
- governed inputs and outputs:
  - input: capability and action selection plus structured payload
  - output: deterministic module result with audit and phase-gate metadata
- related files/modules:
  - `src/capability_module.py`
  - `src/aais_capability_module.py`
  - `src/capability_service_bridge.py`
- invariants or doctrine surfaces:
  - `docs/contracts/AAIS_CAPABILITY_MODULE_SPEC.md`
  - `docs/contracts/CAPABILITY_SERVICE_BRIDGE.md`
- current implementation gaps:
  - the bridge is live for current tool families, but not yet universal for
    memory, workspace, action, or Forge paths
- integration risk: `medium_high`
- recommended priority: `P1 best_next_activation`

### Forge Contractor And Repo Manager

- status: `live`
- primary purpose: isolated contractor lane for review-first code and repo
  tasks
- architectural layer: execution lanes
- dependencies:
  - `src/forge_client.py`
  - `src/jarvis_operator.py`
  - `src/api.py`
  - external Forge service
- governed inputs and outputs:
  - input: bounded task plus workspace context
  - output: contractor result, law-enforcement metadata, UL snapshot
- related files/modules:
  - `src/forge_client.py`
  - `src/api.py`
  - `forge/service.py`
- invariants or doctrine surfaces:
  - `docs/contracts/FORGE_CONTRACTOR.md`
- current implementation gaps:
  - still bounded and not a free autonomous patch author
- integration risk: `high`
- recommended priority: `P1 harden`

### ForgeEval

- status: `live`
- primary purpose: isolated evaluator and scoring lane
- architectural layer: execution lanes
- dependencies:
  - `src/forge_eval_client.py`
  - `src/api.py`
  - external evaluator service
- governed inputs and outputs:
  - input: evaluation request
  - output: score, details, or error contract
- related files/modules:
  - `src/forge_eval_client.py`
  - `src/api.py`
- invariants or doctrine surfaces:
  - `docs/contracts/FORGEEVAL_CONTRACT.md`
- current implementation gaps:
  - depends on external service health
- integration risk: `medium`
- recommended priority: `P1 maintain`

### EvolveEngine

- status: `live`
- primary purpose: bounded mutation and search lane scored by ForgeEval and
  optionally handed off to Forge
- architectural layer: execution lanes
- dependencies:
  - `src/evolve_client.py`
  - `src/api.py`
  - `src/jarvis_operator.py`
  - external evolve service
- governed inputs and outputs:
  - input: evolve job and evaluation mode
  - output: generations, evaluations, halls, and optional Forge handoff
- related files/modules:
  - `src/evolve_client.py`
  - `src/api.py`
- invariants or doctrine surfaces:
  - `docs/contracts/EVOLVE_ENGINE_CONTRACT.md`
  - `docs/contracts/COLLECTIVE_PATTERN_LEDGER.md`
- current implementation gaps:
  - mutation governance remains bounded and no direct patch authority exists
  - Collective Pattern Ledger law is now admitted, but full repo-wide ledger
    coverage is still strongest in EvolveEngine hall traces rather than every
    AAIS lane
- integration risk: `high`
- recommended priority: `special_review_only`

### Coding Organs And Patch Verification Stack

- status: `partial`
- primary purpose: inspect, scope, propose, preview, verify, and remember repo
  work
- architectural layer: execution lanes
- dependencies:
  - `src/patchforge.py`
  - `src/change_scope.py`
  - `src/test_oracle.py`
  - `src/patch_apply_engine.py`
  - `src/patch_execution_preview.py`
  - `src/patch_review_store.py`
  - `src/evolving_workbench.py`
  - `src/run_ledger.py`
- governed inputs and outputs:
  - input: workspace problem or proposed patch context
  - output: proposal, review record, execution preview, apply gate inputs
- related files/modules:
  - `src/patchforge.py`
  - `src/change_scope.py`
  - `src/test_oracle.py`
  - `src/patch_apply_engine.py`
  - `src/patch_execution_preview.py`
  - `src/patch_review_store.py`
  - `src/evolving_workbench.py`
- invariants or doctrine surfaces:
  - `README.md`
  - `docs/spine/AAIS_MASTER_SPEC.md`
- current implementation gaps:
  - PatchForge remains proposal-only
  - the stack is modular but not yet one explicit subsystem contract
- integration risk: `high`
- recommended priority: `P1 build_now`

### Media And Processor Seeds

- status: `concept`
- primary purpose: future capability-style media and text processing surfaces
- architectural layer: execution lanes
- dependencies:
  - `src/audio_processor.py`
  - `src/image_processor.py`
  - `src/video_processor.py`
  - `src/batch_processor.py`
  - `src/text_classifier.py`
  - `src/speech.py`
- governed inputs and outputs:
  - input: media or text payload
  - output: processor-specific result
- related files/modules:
  - processor modules listed above
- invariants or doctrine surfaces:
  - the capability-module doctrine applies in principle
- current implementation gaps:
  - these exist as utilities, not yet as one integrated governed bridge family
- integration risk: `medium`
- recommended priority: `P3 wait`

### Workflow Shell

- status: `live`
- primary purpose: FastAPI workflow and onboarding shell, approvals, packaged
  app host, and legacy bridge
- architectural layer: product shell and operator surfaces
- dependencies:
  - `app/main.py`
  - `app/workflow_runtime.py`
  - `app/db.py`
  - `app/tasks.py`
  - `app/workflow_validation.py`
  - `src/cisiv.py`
- governed inputs and outputs:
  - input: workflow definitions, runs, approvals, onboarding actions
  - output: shell state, approvals, run history, packaged frontend hosting
- related files/modules:
  - `app/main.py`
  - `app/workflow_runtime.py`
  - `app/README.md`
- invariants or doctrine surfaces:
  - `docs/runtime/AAIS_RUNTIME_GUIDE.md`
  - `app/README.md`
- current implementation gaps:
  - still uses the legacy Flask bridge during transition
- integration risk: `medium_high`
- recommended priority: `P1 maintain_and_simplify`

### Launcher Package

- status: `live`
- primary purpose: cross-platform start, prepare, and doctor path for the
  packaged app
- architectural layer: product shell and operator surfaces
- dependencies:
  - `aais/__main__.py`
  - `aais/launcher.py`
  - `app/static/`
- governed inputs and outputs:
  - input: launcher commands and data-dir configuration
  - output: staged build, server startup, readiness checks
- related files/modules:
  - `aais/launcher.py`
  - `aais/README.md`
- invariants or doctrine surfaces:
  - `aais/README.md`
- current implementation gaps:
  - operationally live, but not a subsystem to activate further for runtime
    cognition
- integration risk: `low`
- recommended priority: `P0 maintain`

### Operator Surfaces

- status: `live`
- primary purpose: Jarvis Console, Workbench, Memory Bank, Dashboard, and Nova
  surface
- architectural layer: product shell and operator surfaces
- dependencies:
  - frontend page routes
  - `src/api.py`
  - `app/main.py`
- governed inputs and outputs:
  - input: operator actions and inspection requests
  - output: API calls, traces, mission, memory, governance, Forge, and evolve
    views
- related files/modules:
  - `frontend/src/pages/JarvisConsole.jsx`
  - `frontend/src/pages/Dashboard.jsx`
  - `frontend/src/pages/MemoryBank.jsx`
  - `frontend/src/pages/NovaLandingPage.jsx`
- invariants or doctrine surfaces:
  - `README.md`
  - `docs/runtime/AAIS_RUNTIME_GUIDE.md`
- current implementation gaps:
  - hidden or seeded subsystems do not all have first-class operator surfaces
- integration risk: `medium`
- recommended priority: `P1 keep_aligned`

### Story Forge

- status: `partial`
- primary purpose: governed narrative build plus movie-audio handoff stack
- architectural layer: execution lanes
- dependencies:
  - `src/capabilities/story_forge_audio.py`
  - `external/story_forge/src/story_forge/backend_full_build.py`
  - `external/story_forge/src/story_forge/movie_audio_pipeline.py`
  - `external/beatbox_speakers/src/`
- governed inputs and outputs:
  - input: `BackendBuildArtifact`, rendered video path, dialogue or narration
    metadata
  - output: bounded final movie artifact contract
- related files/modules:
  - `src/capabilities/story_forge_audio.py`
  - `external/story_forge/src/story_forge/contracts/`
  - `tests/test_story_forge_audio_capability.py`
- invariants or doctrine surfaces:
  - `docs/subsystems/storyforge/STORYFORGE_CANONICAL.md`
  - `docs/subsystems/storyforge/STORYFORGE_STAGE_SPEC.md`
- current implementation gaps:
  - the current admitted AAIS surface is the audio/movie capability path, not
    the full Story Forge front door
  - the standalone launcher, game lane, and text-to-3D lane are not yet
    admitted as first-class AAIS runtime surfaces
- integration risk: `medium_high`
- recommended priority: `P1 stabilize_and_expand`

### Beatbox

- status: `partial`
- primary purpose: downstream score lane between Story Forge build truth and
  Speakers mix truth
- architectural layer: execution lanes
- dependencies:
  - `external/beatbox_speakers/src/beatbox/`
  - `external/beatbox_speakers/src/audio_pipeline/`
  - `external/ai/beatbox/adapter.py`
  - `integrations/contracts/beatbox_contract.md`
- governed inputs and outputs:
  - input: Story Forge handoff timing and emotional score data
  - output: cue plan, score artifact, and audio pipeline handoff state
- related files/modules:
  - `external/beatbox_speakers/src/beatbox/contracts.py`
  - `external/beatbox_speakers/src/audio_pipeline/contracts.py`
- invariants or doctrine surfaces:
  - `docs/subsystems/beatbox/BEATBOX_CANONICAL.md`
  - `integrations/contracts/beatbox_contract.md`
- current implementation gaps:
  - currently admitted through the Story Forge audio path rather than as a
    separate operator-facing AAIS lane
- integration risk: `medium`
- recommended priority: `P1 harden_in_chain`

### Speakers

- status: `partial`
- primary purpose: downstream voice rendering, mix planning, and final movie
  audio assembly
- architectural layer: execution lanes
- dependencies:
  - `external/beatbox_speakers/src/speakers/`
  - `external/beatbox_speakers/src/assembler/`
  - `external/beatbox_speakers/src/audio_pipeline/`
- governed inputs and outputs:
  - input: Story Forge presented output plus Beatbox cue/timing state
  - output: voice stems, mix plan, final audio, and assembled movie package
- related files/modules:
  - `external/beatbox_speakers/src/speakers/contracts.py`
  - `external/beatbox_speakers/src/assembler/contracts.py`
- invariants or doctrine surfaces:
  - `docs/subsystems/speakers/SPEAKERS_CANONICAL.md`
- current implementation gaps:
  - currently admitted through the Story Forge audio path rather than as a
    separate operator-facing AAIS lane
- integration risk: `medium`
- recommended priority: `P1 harden_in_chain`

### ARIS

- status: `partial`
- primary purpose: embedded governed repo-intelligence boundary, external-admission hardening, and non-copy enforcement
- architectural layer: authority and cognition
- dependencies:
  - `src/aris_integration.py`
  - `src/cognitive_bridge.py`
  - `src/project_infi_law.py`
  - `docs/contracts/ARIS_RUNTIME_CONTRACT.md`
- governed inputs and outputs:
  - input: outside proposals, runtime ingress, pattern-sharing intent
  - output: admitted-form gating, non-copy enforcement, signature-only sharing posture
- related files/modules:
  - `src/aris_integration.py`
  - `src/cognitive_bridge.py`
  - `src/project_infi_law.py`
- invariants or doctrine surfaces:
  - `docs/contracts/ARIS_RUNTIME_CONTRACT.md`
  - `docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md`
  - `docs/contracts/COLLECTIVE_PATTERN_LEDGER.md`
- current implementation gaps:
  - active as an embedded profile, not a standalone ARIS service or desktop stack
  - the broader archive ARIS pipeline family is still lineage unless separately admitted
- integration risk: `medium`
- recommended priority: `P1 harden_embedded_profile`

### Legacy Experimental Modular Copy

- status: `deprecated`
- primary purpose: legacy modular experiment rather than runtime authority
- architectural layer: hidden or seeded subsystem primitive
- dependencies:
  - none canonical
- governed inputs and outputs:
  - input: not a canonical runtime path
  - output: not a canonical runtime path
- related files/modules:
  - `src/jarvis_modular2.py`
- invariants or doctrine surfaces:
  - `docs/audit/AAIS_STATUS_AUDIT.md`
- current implementation gaps:
  - not authoritative and should not be reactivated casually
- integration risk: `low`
- recommended priority: `leave_dormant`

### AAIS Capability Shim

- status: `deprecated`
- primary purpose: backward-compatible shim over the newer capability module
  base
- architectural layer: hidden or seeded subsystem primitive
- dependencies:
  - `src/capability_module.py`
- governed inputs and outputs:
  - input: legacy capability callers
  - output: normalized capability payloads
- related files/modules:
  - `src/aais_capability_module.py`
- invariants or doctrine surfaces:
  - `docs/contracts/AAIS_CAPABILITY_MODULE_SPEC.md`
- current implementation gaps:
  - compatibility-only path
- integration risk: `low`
- recommended priority: `retain_only_while_needed`

## 4. Activation Buckets

### Safe To Build Now

- Memory governance stack
- Capability module layer and service bridge
- Knowledge authority, live research, and document intelligence
- Mission Board
- Coding organs and patch verification stack
- Perception, spatial, and mystic toolkit through the capability bridge
- Workflow shell simplification and operator-surface alignment

### Blocked By Missing Infrastructure

- Realtime event-cause predictor
- Governed direct pipeline as a full runtime transport substrate
- OTEM beyond the current bounded ceiling
- Invariant engine as a runtime subsystem
- a distinct standalone ARIS service beyond the current embedded AAIS profile

### Should Remain Dormant Until Later

- Dreamspace expansion
- Super Nova expansion beyond the current guarded lane
- broad Story Forge front-door activation beyond the current audio capability path
- legacy experimental modular copies
- media processor seeds beyond bridge-safe use

### High-Risk / High-Power Systems Requiring Special Review

- Project Infi runtime
- governance, security, and immune stack
- Forge contractor if moved toward autonomous patching
- EvolveEngine
- OTEM if given execution authority
- capability bridge for any side-effecting or file-system modules
- System Guard and break-glass control paths

## 5. Gap Matrix

### Live

- Jarvis core runtime
- conversation and continuity substrate
- Jarvis protocol and reasoning fabric
- orchestration core
- AAIS-UL runtime substrate (adaptation + governed command layer)
- safety and response integrity stack
- direct challenge and relational lane
- Nova companion line
- creative runtimes V9 and V10
- Project Infi runtime
- governance, security, and immune stack
- Mission Board
- knowledge authority, live research, and document intelligence
- Forge contractor and repo manager
- ForgeEval
- EvolveEngine
- workflow shell
- launcher package
- operator surfaces

### Partial

- OTEM bounded reasoning lane
- embedded ARIS runtime profile
- governed direct pipeline
- perception, spatial, and mystic toolkit
- module governance and phase gate
- memory governance stack
- capability module layer and service bridge
- coding organs and patch verification stack
- Story Forge
- Beatbox
- Speakers

### Hidden Or Seeded

- realtime event-cause predictor
- invariant engine
- media and processor seeds

### Deprecated Or Dormant

- Dreamspace
- legacy experimental modular copy
- AAIS capability shim

## 6. Recommended Next Activation

If the goal is to activate the next subsystem safely, use this order:

1. memory governance stack
2. capability module layer and service bridge
3. knowledge authority and document intelligence
4. coding organs and patch verification stack
5. only then revisit OTEM or realtime predictive lanes

Why this order:

- memory governance reduces long-horizon instability
- the capability bridge reduces ad hoc execution growth
- knowledge authority improves source discipline before stronger automation
- coding organs can then become safer without bypassing the earlier law layers

## 7. Barebones Map

The strongest barebones or hidden subsystem seeds currently visible in code are:

- `src/capability_service_bridge.py`
  seeded execution-governance fabric
- `src/jarvis_memory_board.py`
  seeded memory-governance fabric
- `src/governed_direct_pipeline.py`
  seeded packet and lane fabric
- `src/realtime_event_cause_predictor.py`
  seeded predictive fast-lane adjunct
- `src/phase_gate.py`
  seeded activation-governance fabric
- `src/verification_gate.py`
  seeded mission and review gate fabric
- `src/invariant_engine.py`
  seeded mathematical verification fabric
- `src/capabilities/story_forge_audio.py`
  current partial Story Forge audio/movie capability seam backed by vendored
  Story Forge, Beatbox, and Speakers sources

These are the main hidden or barebones areas worth treating as a map of missing
or not-yet-activated subsystem families.

## 8. Subsystem Constitutional Layer (Governed)

The following ideas graduated from [../_future/ideas_pending/](../_future/ideas_pending/) to **governed** status:

| Idea | Status | Active doc | Proof |
|------|--------|------------|-------|
| CISIV Operator Lineage Console | governed | [UL_LINEAGE_CONSOLE.md](./UL_LINEAGE_CONSOLE.md) | [../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md](../proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md) |
| Forensic Triangulation Ledger | governed | [../subsystems/forensics/TRIANGULATION.md](../subsystems/forensics/TRIANGULATION.md) | [../proof/forensics/TRIANGULATION_V1_PROOF.md](../proof/forensics/TRIANGULATION_V1_PROOF.md) |
| Narrative Trust Pack | governed | [../subsystems/storyforge/NARRATIVE_TRUST_PACK.md](../subsystems/storyforge/NARRATIVE_TRUST_PACK.md) | [../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md](../proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md) |
| Recipe Module | governed | [../subsystems/platform/RECIPE_MODULE.md](../subsystems/platform/RECIPE_MODULE.md) | [../proof/platform/RECIPE_MODULE_V1_PROOF.md](../proof/platform/RECIPE_MODULE_V1_PROOF.md) |
| Imagine Generator | governed | [../subsystems/storyforge/IMAGINE_GENERATOR.md](../subsystems/storyforge/IMAGINE_GENERATOR.md) | [../proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md](../proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md) |
| Human Voice Extraction | governed | [../subsystems/speakers/HUMAN_VOICE_EXTRACTION.md](../subsystems/speakers/HUMAN_VOICE_EXTRACTION.md) | [../proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md](../proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md) |
| Safety Envelope Organ | governed | [../subsystems/platform/SAFETY_ENVELOPE_ORGAN.md](../subsystems/platform/SAFETY_ENVELOPE_ORGAN.md) | [../proof/platform/SAFETY_ENVELOPE_V1_PROOF.md](../proof/platform/SAFETY_ENVELOPE_V1_PROOF.md) |
| Operator Profile Organ | governed | [../subsystems/platform/OPERATOR_PROFILE_ORGAN.md](../subsystems/platform/OPERATOR_PROFILE_ORGAN.md) | [../proof/platform/OPERATOR_PROFILE_V1_PROOF.md](../proof/platform/OPERATOR_PROFILE_V1_PROOF.md) |
| Reflection Runtime Organ | governed | [../subsystems/nova/REFLECTION_RUNTIME_ORGAN.md](../subsystems/nova/REFLECTION_RUNTIME_ORGAN.md) | [../proof/cognitive_runtime/REFLECTION_RUNTIME_ORGAN_V1_PROOF.md](../proof/cognitive_runtime/REFLECTION_RUNTIME_ORGAN_V1_PROOF.md) |
| Memory Runtime Organ | governed | [../subsystems/nova/MEMORY_RUNTIME_ORGAN.md](../subsystems/nova/MEMORY_RUNTIME_ORGAN.md) | [../proof/cognitive_runtime/MEMORY_RUNTIME_ORGAN_V1_PROOF.md](../proof/cognitive_runtime/MEMORY_RUNTIME_ORGAN_V1_PROOF.md) |
| Capability Service Bridge | governed | [../subsystems/platform/CAPABILITY_SERVICE_BRIDGE.md](../subsystems/platform/CAPABILITY_SERVICE_BRIDGE.md) | [../proof/platform/CAPABILITY_SERVICE_BRIDGE_V1_PROOF.md](../proof/platform/CAPABILITY_SERVICE_BRIDGE_V1_PROOF.md) |
| Jarvis Memory Board | governed | [../subsystems/platform/JARVIS_MEMORY_BOARD.md](../subsystems/platform/JARVIS_MEMORY_BOARD.md) | [../proof/platform/JARVIS_MEMORY_BOARD_V1_PROOF.md](../proof/platform/JARVIS_MEMORY_BOARD_V1_PROOF.md) |
| Governed Direct Pipeline | governed | [GOVERNED_DIRECT_PIPELINE.md](./GOVERNED_DIRECT_PIPELINE.md) | [../proof/platform/GOVERNED_DIRECT_PIPELINE_V1_PROOF.md](../proof/platform/GOVERNED_DIRECT_PIPELINE_V1_PROOF.md) |

Gates: `make lineage-gate triangulation-gate narrative-gate alt3-gate alt5-gate barebones-gate`

## 9. Concept Pending (SSP)

Ideas at CISIV **concept** stage per [AAIS_SSP_PROTOCOL.md](../contracts/AAIS_SSP_PROTOCOL.md).
Nothing here is live until promoted per [ideas_pending/README.md](../_future/ideas_pending/README.md).

| Idea | Status | Concept spec | MVP plan | Genome |
|------|--------|--------------|----------|--------|
| *(none)* | — | — | — | — |

New admissions via SSP (Step 7) update this table. Graduated ideas move to §8. Genome contract: [AAIS_SUBSYSTEM_GENOME.md](../contracts/AAIS_SUBSYSTEM_GENOME.md).
