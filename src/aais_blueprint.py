"""Live canonical blueprint for AAIS.

This module turns the repo's older architecture sketches and the current
runtime into one explicit, UI-friendly system map. It explains what AAIS is,
what is live right now, and which earlier files became today's runtime pieces.
"""

from __future__ import annotations

from typing import Any

from src.continuity_profile import continuity_profile_store
from src.document_vision import document_vision
from src.dreamspace import dreamspace
from src.governance_layer import governance_layer
from src.immune_system import immune_system
from src.jarvis_protocol import protocol_spec
from src.mission_board import mission_board
from src.module_governance import module_governance
from src.provider_registry import provider_registry
from src.security_protocol_core import security_protocol_core
from src.specialist_registry import list_specialist_catalog, list_specialist_presets
from src.system_guard import system_guard
from src.ui_vision import ui_vision
from src.v10_runtime import v10_runtime
from src.v9_runtime import v9_runtime


BLUEPRINT_ID = "aais.blueprint"
BLUEPRINT_VERSION = "0.1"


def _file(path: str, label: str | None = None) -> dict[str, str]:
    return {
        "path": path,
        "label": label or path.replace("\\", "/").rsplit("/", 1)[-1],
    }


def _count_specialists(domains: list[dict[str, Any]]) -> int:
    return sum(len(domain.get("specialists") or []) for domain in domains)


def _enabled_provider_count(providers: list[dict[str, Any]]) -> int:
    return sum(1 for provider in providers if provider.get("available"))


def _provider_blueprint_entries(providers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(provider.get("id") or provider.get("name") or "provider"),
            "label": str(provider.get("label") or provider.get("display_name") or provider.get("name") or "Provider"),
            "available": bool(provider.get("available")),
            "is_default": bool(provider.get("is_default")),
            "kind": str(provider.get("kind") or "provider"),
            "summary": str(provider.get("summary") or "").strip(),
            "reason": str(provider.get("reason") or "").strip(),
            "model": str(provider.get("model") or "").strip(),
            "activation_hint": str(provider.get("activation_hint") or "").strip(),
            "supports_stream": bool(provider.get("supports_stream")),
        }
        for provider in providers
    ]


def _dreamspace_blueprint_status(status: str | None) -> str:
    normalized = str(status or "stopped").strip().lower()
    if normalized in {"dreaming", "idle"}:
        return "active"
    if normalized == "paused":
        return "guarded"
    if normalized == "error":
        return "degraded"
    return "optional"


def _provider_blueprint_status(
    *,
    enabled_provider_count: int,
    active_model_mode: str | None,
) -> str:
    if enabled_provider_count <= 0:
        return "degraded"
    if active_model_mode:
        return "active"
    return "live"


def _guard_blueprint_status(status: str | None) -> str:
    normalized = str(status or "nominal").strip().lower()
    if normalized == "nominal":
        return "active"
    if normalized == "paused":
        return "guarded"
    if normalized == "stopped":
        return "standby"
    return "degraded"


def _module_admission_entries() -> list[dict[str, Any]]:
    return [
        {
            "id": "phase_gate",
            "label": "Phase Gate",
            "normalized_status": "live",
            "summary": "Phase Gate now blocks unroutable or unexecutable components at real runtime boundaries.",
            "reason": (
                "Capability bridge execution and the memory governance gateway both call phase gate "
                "checks before live work proceeds."
            ),
            "live_files": [
                _file("src/phase_gate.py"),
                _file("src/capability_service_bridge.py"),
                _file("src/memory_board_enforcer.py"),
            ],
        },
        {
            "id": "continuity_witness",
            "label": "Continuity Witness",
            "normalized_status": "live",
            "summary": "Continuity Witness is admitted as an observation layer on governed turn traces.",
            "reason": (
                "The witness is built into governed pipeline inputs and exposed on trace surfaces "
                "without gaining execution authority."
            ),
            "live_files": [
                _file("src/continuity_witness.py"),
                _file("src/governed_direct_pipeline.py"),
                _file("src/api.py"),
            ],
        },
        {
            "id": "realtime_event_cause_predictor",
            "label": "Realtime Event Cause Predictor",
            "normalized_status": "live",
            "summary": "Realtime event interpretation is admitted as a bounded classifier over the governed signal feed.",
            "reason": (
                "The governed direct pipeline now emits realtime signal feed data and runs the predictor "
                "as a structured trace component."
            ),
            "live_files": [
                _file("src/realtime_event_cause_predictor.py"),
                _file("src/governed_direct_pipeline.py"),
            ],
        },
        {
            "id": "operator_health_sentinel",
            "label": "Operator Health Sentinel",
            "normalized_status": "live",
            "summary": "Operator Health Sentinel is admitted in advisory-only mode on governed traces.",
            "reason": (
                "The sentinel observes runtime burden through structured signals and emits bounded "
                "recommendations without direct execution authority."
            ),
            "live_files": [
                _file("src/operator_health_sentinel.py"),
                _file("src/governed_direct_pipeline.py"),
            ],
        },
        {
            "id": "invariant_engine",
            "label": "Invariant Engine",
            "normalized_status": "admitted",
            "summary": "Invariant engine is live on the Cognitive Bridge deliberation and generation path.",
            "reason": (
                "Bridge packets of type deliberation_request and generation_request pass through "
                "InvariantEngine.validate_bridge_packet before ARIS enforcement and governed LLM routing."
            ),
            "live_files": [
                _file("src/invariant_engine.py"),
                _file("src/cognitive_bridge.py"),
                _file("tests/test_invariant_engine.py"),
            ],
        },
        {
            "id": "ugr_runtime",
            "label": "Unified Governed Runtime (UGR)",
            "normalized_status": "admitted",
            "summary": "UGR orchestrates governed multi-lane deliberation behind the Cognitive Bridge.",
            "reason": (
                "Phase 2 lifts UGR to a decomposed HTTP mesh (policy, ledger, lanes, convergence, "
                "orchestrator) with Forge pipeline ugr-cloud-cluster and make ugr-cloud-gate."
            ),
            "live_files": [
                _file("src/ugr/unified_runtime.py"),
                _file("src/ugr/cloud/distributed_runtime.py"),
                _file("src/ugr/cloud/services.py"),
                _file("deploy/ugr/mesh.local.json"),
                _file("docs/contracts/UGR_CLOUD_MESH_CONTRACT.md"),
            ],
        },
        {
            "id": "v10_action_engine",
            "label": "V10 Action Engine",
            "normalized_status": "prototype only",
            "summary": "The standalone V10 action engine remains a placeholder and is not part of the admitted runtime chain.",
            "reason": (
                "The file exists, but the live V10 runtime runs elsewhere and there is no bounded admitted "
                "caller using this placeholder engine."
            ),
            "live_files": [
                _file("src/v10_action_engine.py"),
                _file("src/v10_runtime.py"),
            ],
        },
    ]


def _module_admission_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        status = str(entry.get("normalized_status") or "unknown").strip() or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts


def build_aais_blueprint(
    *,
    requested_model_mode: str | None,
    active_model_mode: str | None,
    ai_status: str | None,
) -> dict[str, Any]:
    """Build a live AAIS system map for the Jarvis console and API."""
    provider_registry.refresh()
    providers = provider_registry.list_status()
    specialist_domains = list_specialist_catalog()
    specialist_presets = list_specialist_presets()
    protocol = protocol_spec()
    guard = system_guard.snapshot(limit_events=3)
    dream = dreamspace.snapshot(limit_dreams=2)
    missions = mission_board.snapshot(limit=12)
    governance = governance_layer.snapshot(limit_events=3, limit_requests=3)
    immune = immune_system.snapshot(limit_events=3, limit_incidents=2)
    module_protocol = module_governance.snapshot(limit_events=3, limit_modules=3)
    security = security_protocol_core.snapshot(limit_events=3)
    continuity = continuity_profile_store.get_profile().to_dict()
    v9 = v9_runtime.snapshot(limit=2)
    v10 = v10_runtime.snapshot(limit=2)
    document_enabled = document_vision.is_enabled()
    ui_enabled = ui_vision.is_enabled()

    specialist_count = _count_specialists(specialist_domains)
    enabled_provider_count = _enabled_provider_count(providers)
    provider_entries = _provider_blueprint_entries(providers)
    module_admission_entries = _module_admission_entries()
    module_admission_counts = _module_admission_counts(module_admission_entries)

    subsystems = [
        {
            "id": "jarvis_shell",
            "label": "Jarvis Shell",
            "status": "live",
            "summary": (
                "Jarvis is the authority shell where chat, memory, browser verify, safety, "
                "Dreamspace, and tools meet in one organismic command deck."
            ),
            "detail": (
                "This is the center of gravity for AAIS now. Companion surfaces can front the "
                "experience, but Jarvis keeps routing, state, and safety authority."
            ),
            "live_files": [
                _file("src/api.py"),
                _file("frontend/src/pages/JarvisConsole.jsx"),
                _file("frontend/src/lib/jarvis.js"),
            ],
            "source_files": [
                _file("archive/legacy_root/god_dashboard.py"),
                _file("document/law/REPO_LAWBOOK.md"),
            ],
        },
        {
            "id": "orchestration_core",
            "label": "God Brain + Council",
            "status": "active" if active_model_mode else "standby",
            "summary": (
                "The God Brain, V8 runtime, specialist registry, and model routing decide how a "
                "turn is handled before the model answers, while keeping surface lanes separate "
                "from control authority."
            ),
            "detail": (
                f"{specialist_count} specialists across {len(specialist_domains)} domains and "
                f"{len(specialist_presets)} preset packs are available to the council."
            ),
            "live_files": [
                _file("src/god_brain.py"),
                _file("src/v8_runtime.py"),
                _file("src/specialist_registry.py"),
                _file("src/model_routing.py"),
            ],
            "source_files": [
                _file("archive/legacy_root/core.py"),
                _file("archive/legacy_root/angels.py"),
                _file("src/specialist_registry.py"),
            ],
        },
        {
            "id": "protocol_provider_fabric",
            "label": "Protocol + Providers",
            "status": _provider_blueprint_status(
                enabled_provider_count=enabled_provider_count,
                active_model_mode=active_model_mode,
            ),
            "summary": (
                "Jarvis Protocol is the shared language across turns, tools, specialists, and "
                "provider adapters."
            ),
            "detail": (
                f"Protocol {protocol['version']} exposes {len(protocol['channels'])} channels, and "
                f"{enabled_provider_count} of {len(providers)} providers are currently available."
            ),
            "live_files": [
                _file("src/jarvis_protocol.py"),
                _file("src/provider_registry.py"),
                _file("src/providers/local_provider.py"),
                _file("src/providers/claude_provider.py"),
            ],
            "source_files": [
                _file("docs/contracts/JARVIS_PROTOCOL.md"),
                _file("src/providers/provider_registry.py"),
                _file("README.md"),
            ],
        },
        {
            "id": "universal_language",
            "label": "AAIS-UL + Doctrine",
            "status": "active",
            "summary": (
                "AAIS Universal Language adapts modular context into one shared payload shape, "
                "while doctrine layers keep Jarvis inspectable and stable as it grows."
            ),
            "detail": (
                "The provider-facing modular pipeline now emits UL payloads plus Writers 3 Rules, "
                "Angels and Wards, and Six Wards doctrine traces."
            ),
            "live_files": [
                _file("src/aais_ul.py"),
                _file("src/aais_ul_substrate.py"),
                _file("tools/ul/probe.py"),
                _file("tools/ul/scan.py"),
                _file("tools/ul/drift.py"),
                _file("tools/ul/smoke.py"),
                _file("src/patchforge.py"),
                _file("src/patch_review_store.py"),
                _file("src/v9_core.py"),
                _file("src/v10_core.py"),
                _file("src/v9_runtime.py"),
                _file("src/v10_runtime.py"),
                _file("src/mystic_engine.py"),
                _file("src/ugr/cloud_forge_bridge.py"),
                _file("src/forge_client.py"),
                _file("src/forge_eval_client.py"),
                _file("src/evolve_client.py"),
                _file("src/cloud_forge/integration.py"),
                _file("src/capability_service_bridge.py"),
                _file("src/capability_module.py"),
                _file("src/ugr/operator_console/snapshot.py"),
                _file("src/ugr/operator_console/forge_platform.py"),
                _file("src/ugr/operator_console/trace_viewer.py"),
                _file("src/Spatial_reasoning.py"),
                _file("src/corrigibility.py"),
                _file("src/operator_health_sentinel.py"),
                _file("src/run_ledger.py"),
                _file("src/memory_smith.py"),
                _file("src/knowledge_authority.py"),
                _file("src/specialist_registry.py"),
                _file("src/realtime_event_cause_predictor.py"),
                _file("src/invariant_engine.py"),
                _file("src/reasoning_exchange_protocol.py"),
                _file("src/jarvis_reasoning_protocol.py"),
                _file("src/jarvis_detachment_guard.py"),
                _file("src/governed_event_chain.py"),
                _file("src/otem_runtime.py"),
                _file("src/evolving_workbench.py"),
                _file("src/conversation_memory.py"),
                _file("src/ugr/cloud/services.py"),
                _file("src/jarvis_modular.py"),
                _file("src/writers_3_rules.py"),
                _file("src/angels_and_wards.py"),
                _file("src/six_wards_guardrails.py"),
            ],
            "source_files": [
                _file("docs/contracts/AAIS_UL_DOCTRINE.md"),
                _file("docs/contracts/JARVIS_REASONING_PROTOCOL.md"),
                _file("document/law/REPO_LAWBOOK.md"),
            ],
        },
        {
            "id": "safety_corrigibility",
            "label": "Safety + Corrigibility",
            "status": _guard_blueprint_status(guard.get("status")),
            "summary": (
                "System Guard, corrigibility, and policy posture keep AAIS interruptible, honest, "
                "and local-first."
            ),
            "detail": (
                f"System Guard is {guard.get('status', 'nominal')}, and Dreamspace is "
                f"{dream.get('status', 'stopped')}."
            ),
            "live_files": [
                _file("src/system_guard.py"),
                _file("src/corrigibility.py"),
                _file("src/conversation_memory.py"),
            ],
            "source_files": [
                _file("tools/ops/emergency_stop.py"),
                _file("tools/ops/hooks.py"),
                _file("tools/ops/killswitch_init.py"),
                _file("tools/ops/killswitch_gui.py"),
                _file("document/law/REPO_LAWBOOK.md"),
            ],
        },
        {
            "id": "security_immune_governance",
            "label": "Security + Immune + Governance",
            "status": "active",
            "summary": (
                "The April 7 constitutional layer is now live as one shared policy brain, one immune posture, "
                "and one governance approval surface for operator overrides and break-glass."
            ),
            "detail": (
                f"Security has {security.get('event_count', 0)} recorded decisions, immune mode is "
                f"{immune.get('system_mode', 'normal')}, and governance is tracking "
                f"{len(governance.get('open_policy_requests', []))} open policy requests."
            ),
            "live_files": [
                _file("src/security_protocol_core.py"),
                _file("src/immune_system.py"),
                _file("src/governance_layer.py"),
                _file("src/api.py"),
            ],
            "source_files": [
                _file("Secuirty, guardrails and protocol.docx"),
                _file("Jarvis Immune system.docx"),
                _file("Goverance layer.docx"),
                _file("Jarvis Master Spec.docx"),
            ],
        },
        {
            "id": "module_governance_protocol",
            "label": "Module Governance Protocol",
            "status": "active",
            "summary": (
                "AAIS now admits modules through a privacy-first governance gate and treats runtime "
                "violations as hostile until corrected, disabled, or blacklisted."
            ),
            "detail": (
                f"{module_protocol.get('module_counts', {}).get('admitted', 0)} admitted modules, "
                f"{module_protocol.get('module_counts', {}).get('quarantined', 0)} quarantined modules, and "
                f"{module_protocol.get('blacklist_count', 0)} blacklisted modules are tracked by the live protocol."
            ),
            "live_files": [
                _file("src/module_governance.py"),
                _file("src/immune_system.py"),
                _file("src/governance_layer.py"),
                _file("src/api.py"),
            ],
            "source_files": [
                _file("docs/contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md"),
                _file("document/law/REPO_LAWBOOK.md"),
            ],
        },
        {
            "id": "continuity_layer",
            "label": "Continuity Layer",
            "status": "active",
            "summary": (
                "Jarvis continuity now lives outside the model in a persistent profile that survives provider swaps, "
                "fallback, and routing changes."
            ),
            "detail": (
                f"Current tone is {continuity.get('tone', 'concise')}, with "
                f"{len(continuity.get('known_projects', []))} known project anchors and "
                f"{len(continuity.get('preferred_tools', []))} preferred tool hints."
            ),
            "live_files": [
                _file("src/continuity_profile.py"),
                _file("src/conversation_memory.py"),
                _file("src/api.py"),
            ],
            "source_files": [
                _file("os.docx"),
                _file("Jarvis Master Spec.docx"),
            ],
        },
        {
            "id": "creative_runtimes",
            "label": "Creative Runtimes",
            "status": "active",
            "summary": (
                "V9 and V10 now run through inspectable Jarvis runtimes instead of raw direct-engine calls."
            ),
            "detail": (
                f"V9 is {v9.get('status', 'idle')} with {v9.get('run_count', 0)} recorded runs, "
                f"and V10 is {v10.get('status', 'idle')} with {v10.get('run_count', 0)} recorded runs."
            ),
            "live_files": [
                _file("src/creative_core_runtime.py"),
                _file("src/v9_runtime.py"),
                _file("src/v10_runtime.py"),
                _file("src/jarvis_operator.py"),
            ],
            "source_files": [
                _file("src/v9_core.py"),
                _file("src/v10_core.py"),
                _file("os.docx"),
            ],
        },
        {
            "id": "perception_tools",
            "label": "Perception + Tools",
            "status": "live",
            "summary": (
                "AAIS can reason over workspace files, browser state, spatial graphs, live "
                "research, and opt-in vision layers."
            ),
            "detail": (
                "Document vision is "
                f"{'enabled' if document_enabled else 'disabled'}, UI understanding is "
                f"{'enabled' if ui_enabled else 'disabled'}, and spatial reasoning is ready."
            ),
            "live_files": [
                _file("src/jarvis_operator.py"),
                _file("src/Spatial_reasoning.py"),
                _file("src/document_vision.py"),
                _file("src/ui_vision.py"),
            ],
            "source_files": [
                _file("document/law/REPO_LAWBOOK.md"),
                _file("README.md"),
            ],
        },
        {
            "id": "mission_board",
            "label": "Mission Board",
            "status": "active" if missions.get("mission_count") else "optional",
            "summary": (
                "Mission Board gives Jarvis a durable objective layer that survives beyond a single turn."
            ),
            "detail": missions.get("summary"),
            "live_files": [
                _file("src/mission_board.py"),
                _file("src/api.py"),
                _file("frontend/src/pages/JarvisConsole.jsx"),
            ],
            "source_files": [
                _file("document/law/REPO_LAWBOOK.md"),
            ],
        },
        {
            "id": "evolve_engine",
            "label": "Evolve Engine",
            "status": "active",
            "summary": (
                "EvolveEngine is the bounded search lane: Jarvis authorizes jobs, EvolveEngine mutates candidates, "
                "ForgeEval scores them, and the mutation halls keep success and failure visible."
            ),
            "detail": (
                "This lane stays isolated from direct patch authority. Hall of Fame records successful mutations, "
                "Hall of Shame records failed mutations, and the trace store keeps each job inspectable."
            ),
            "live_files": [
                _file("src/evolve_client.py"),
                _file("evolve_engine/service.py"),
                _file("evolve_engine/trace_store.py"),
                _file("src/api.py"),
            ],
            "source_files": [
                _file("docs/contracts/EVOLVE_ENGINE_CONTRACT.md"),
                _file("document/law/REPO_LAWBOOK.md"),
            ],
        },
        {
            "id": "ugr_runtime",
            "label": "Unified Governed Runtime",
            "status": "active",
            "summary": (
                "UGR is the governed multi-lane cognitive orchestrator: bridge-first ingress, "
                "parallel lanes, deterministic convergence, and unified pattern ledger v0.5."
            ),
            "detail": (
                "Phase 3 adds governed ingestion: curated arXiv/GitHub/RSS sources, sanitize/extract "
                "pipeline, invariant gate, and ledger proposals without model I/O."
            ),
            "live_files": [
                _file("src/ugr/ingestion/pipeline.py"),
                _file("deploy/ugr/ingestion.sources.json"),
                _file("src/ugr/cloud/services.py"),
                _file("src/api.py"),
            ],
            "source_files": [
                _file("docs/programs/UGR_CLOUD_PROGRAM.md"),
                _file("docs/contracts/UGR_RUNTIME_CONTRACT.md"),
                _file("docs/contracts/UGR_CLOUD_MESH_CONTRACT.md"),
                _file("wolf-cog-os/forge/pipelines/ugr-cloud-cluster.yaml"),
            ],
        },
        {
            "id": "coding_organs",
            "label": "Coding Organs",
            "status": "active",
            "summary": (
                "PatchForge, RunLedger, ChangeScope, TestOracle, MemorySmith, and ProviderMind "
                "turn Jarvis repo work into a safer inspect -> plan -> verify -> remember loop."
            ),
            "detail": (
                "These blueprint organs stay modular: patch proposals remain review-first, "
                "run history stays durable, stale blocker cleanup stays curated, and high-level "
                "engine routing remains visible without becoming a second brain."
            ),
            "live_files": [
                _file("src/patchforge.py"),
                _file("src/run_ledger.py"),
                _file("src/change_scope.py"),
                _file("src/test_oracle.py"),
                _file("src/memory_smith.py"),
                _file("src/provider_mind.py"),
            ],
            "source_files": [
                _file("The key rule for all 6_.docx"),
                _file("docs/contracts/AAIS_DOC_PROTOCOL.md"),
            ],
        },
        {
            "id": "dreamspace",
            "label": "Dreamspace",
            "status": _dreamspace_blueprint_status(dream.get("status")),
            "summary": (
                "Dreamspace is the optional reflective layer that can generate guarded background "
                "reflections without replacing the main Jarvis stack."
            ),
            "detail": dream.get("summary")
            or "Dreamspace state is available through the local runtime snapshot.",
            "live_files": [
                _file("src/dreamspace.py"),
                _file("src/api.py"),
            ],
            "source_files": [
                _file("document/law/REPO_LAWBOOK.md"),
            ],
        },
    ]

    lineage = [
        {
            "id": "dashboard_lineage",
            "label": "Command Deck Lineage",
            "summary": "Older dashboard thinking now lives inside the Jarvis console instead of a separate side app.",
            "sources": [_file("archive/legacy_root/god_dashboard.py")],
            "targets": [_file("frontend/src/pages/JarvisConsole.jsx")],
        },
        {
            "id": "council_lineage",
            "label": "Council Lineage",
            "summary": "The early multi-mind sketches became the God Brain, specialist registry, and routing council.",
            "sources": [_file("archive/legacy_root/core.py"), _file("archive/legacy_root/angels.py")],
            "targets": [_file("src/god_brain.py"), _file("src/specialist_registry.py")],
        },
        {
            "id": "guard_lineage",
            "label": "Interruptibility Lineage",
            "summary": "The older kill-switch ideas were refined into a safer local-first System Guard and corrigibility layer.",
            "sources": [
                _file("tools/ops/emergency_stop.py"),
                _file("tools/ops/hooks.py"),
                _file("tools/ops/killswitch_init.py"),
                _file("tools/ops/killswitch_gui.py"),
            ],
            "targets": [_file("src/system_guard.py"), _file("src/corrigibility.py")],
        },
        {
            "id": "protocol_lineage",
            "label": "Universal Language Lineage",
            "summary": "The shared message contract is now explicit as Jarvis Protocol and the provider registry.",
            "sources": [_file("docs/contracts/JARVIS_PROTOCOL.md"), _file("README.md")],
            "targets": [_file("src/jarvis_protocol.py"), _file("src/provider_registry.py")],
        },
        {
            "id": "doctrine_lineage",
            "label": "Doctrine Lineage",
            "summary": (
                "The UL doctrine, Angels and Wards, and Six Wards packs now live inside the "
                "provider-facing modular preview instead of separate zip-only sketches."
            ),
            "sources": [
                _file("docs/contracts/AAIS_UL_DOCTRINE.md"),
                _file("docs/contracts/JARVIS_REASONING_PROTOCOL.md"),
                _file("document/law/REPO_LAWBOOK.md"),
            ],
            "targets": [
                _file("src/aais_ul.py"),
                _file("src/angels_and_wards.py"),
                _file("src/six_wards_guardrails.py"),
                _file("src/jarvis_modular.py"),
            ],
        },
    ]

    return {
        "id": BLUEPRINT_ID,
        "version": BLUEPRINT_VERSION,
        "title": "AAIS Blueprint",
        "summary": (
            "AAIS is a local-first organismic Jarvis operating layer: layered, role-specialized, "
            "self-protective, and adaptive without surrendering identity."
        ),
        "principles": [
            "AAIS is an organismic system: layered, role-specialized, self-protective, and adaptive without surrendering identity.",
            "Jarvis is the orchestration core and authority lane.",
            "Surface priority does not replace authority; companion surfaces may front the experience while Jarvis keeps routing, memory, and safety control.",
            "Few real models can support many logical specialists.",
            "Local safety, corrigibility, and operator approval come before autonomy.",
            "Optional layers like Dreamspace and vision stay modular instead of replacing the shell.",
            "Every active lane must stay documented, bounded, and visible in the live blueprint.",
            "Modules must pass governance law before admission and lose the right to exist if they violate the user.",
        ],
        "metrics": {
            "requested_model_mode": requested_model_mode or "unknown",
            "active_model_mode": active_model_mode or "unloaded",
            "ai_status": ai_status or "not_initialized",
            "system_guard_status": guard.get("status", "nominal"),
            "dreamspace_status": dream.get("status", "stopped"),
            "provider_count": len(providers),
            "provider_enabled_count": enabled_provider_count,
            "mission_count": missions.get("mission_count", 0),
            "specialist_count": specialist_count,
            "specialist_domain_count": len(specialist_domains),
            "protocol_channel_count": len(protocol.get("channels") or []),
            "documented_lane_count": len(subsystems),
            "normalized_module_count": len(module_admission_entries),
            "non_live_module_count": sum(
                count
                for status, count in module_admission_counts.items()
                if status != "live"
            ),
        },
        "providers": provider_entries,
        "subsystems": subsystems,
        "module_admission": {
            "summary": (
                "This section keeps the repo honest about module maturity so presence on disk does not "
                "look like live admission."
            ),
            "status_model": [
                "live",
                "broken",
                "present but not admitted",
                "prototype only",
                "deprecated",
            ],
            "counts": module_admission_counts,
            "entries": module_admission_entries,
        },
        "lineage": lineage,
    }
