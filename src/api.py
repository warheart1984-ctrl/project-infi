"""Canonical AAIS/Jarvis operator runtime.

`src/api.py` owns core Jarvis runtime truth, operator contracts, and the main
AAIS `/api/*` behavior. `app/main.py` may mount this Flask app through a
compatibility bridge, but that workflow shell does not replace the authority
defined here.
"""

# Mythic: Api
# Engineering: ApiEngine
import asyncio
import base64
import gc
import importlib
import json
import os
import re
import tempfile
import threading
from dataclasses import asdict, is_dataclass
from datetime import datetime
from src.datetime_compat import UTC
from io import BytesIO
from typing import Any
from uuid import uuid4

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from src.anti_drift import (
    build_thread_contract as build_anti_drift_thread_contract,
    enforce_anti_drift,
)
from src.aais_blueprint import build_aais_blueprint
from src.aais_ul.runtime import attach_ul_substrate, substrate_status
from src.chat_turn_governance import (
    apply_chat_turn_admission_block,
    attach_modular_preview_to_response_trace,
    finalize_chat_turn_admission,
    infer_chat_turn_cisiv_stage,
    prepare_chat_turn_modular_package,
    provider_messages_from_preview,
    wrap_chat_runtime_payload,
)
from src.cisiv import CISIV_STAGE_SEQUENCE
from src.config import get_config
from src.conversation_memory import (
    ConversationTurn,
    build_current_turn_priority_guard,
    companion_lane_identity,
    contains_companion_system_leak,
    conversation_memory,
    dedupe_memory_cues,
    derive_provider_mode,
    filter_companion_persistent_memories,
    is_small_nova_persona,
    is_super_nova_persona,
    SUPER_NOVA_PROFILE,
    is_tiny_nova_persona,
    normalize_persona_mode,
    normalize_provider_identifier,
    normalize_provider_mode_identifier,
    normalize_response_mode,
    recommend_response_mode,
    sanitize_assistant_context_text,
    serialize_loaded_session_archive,
    uses_companion_lane,
    uses_super_nova_lane,
    uses_tiny_nova_lane,
)
from src.continuity_profile import continuity_profile_store
from src.continuity_witness import continuity_witness_store
from src.cognitive_bridge import (
    CognitiveBridgeService,
    CognitiveBridgeValidationError,
    summarize_bridge_result,
)
from src.ugr.unified_runtime import ugr_runtime
from src.ugr.operator_console.snapshot import build_operator_console_snapshot
from src.ugr.operator_console.mesh_health import poll_mesh_health
from src.ugr.operator_console.trace_viewer import load_deliberation_traces
from src.ugr.operator_console.forge_platform import load_forge_platform_dashboard
from src.jarvis_detachment_guard import build_bridge_attestation
from src.critic import mission_critic
from src.corrigibility import corrigibility_engine, default_corrigibility_state
from src.dreamspace import dreamspace
from src.document_vision import DocumentVisionUnavailable, document_vision
from src.evolve_client import VALID_EVALUATION_MODES as EVOLVE_VALID_EVALUATION_MODES, evolve_client
from src.forge_client import VALID_KINDS as FORGE_VALID_KINDS, forge_client
from src.forge_eval_client import VALID_MODES as FORGE_EVAL_VALID_MODES, forge_eval_client
from src.generation_utils import DEFAULT_CHAT_CONTEXT_LIMIT, resolve_input_token_limit
from src.governance_layer import governance_layer
from src.god_brain import build_god_brain_trace
from src.capability_service_bridge import to_bridge_envelope
from src.governed_direct_pipeline import (
    build_governed_turn_pipeline,
    consult_pipeline_transport_substrate,
    to_pipeline_envelope,
)
from src.jarvis_memory_board import to_memory_board_envelope
from src.immune_system import immune_system
from src.jarvis_operator import jarvis_operator
from src.jarvis_modular import (
    build_modular_provider_preview,
    build_provider_messages_from_protocol,
)
from src.jarvis_protocol import protocol_spec
from src.cog_runtime.nova import (
    apply_nova_cognitive_finalization,
    summarize_cognitive_runtime_state,
)
from src.cog_runtime.nova_face import summarize_nova_face_bridge
from src.aais_composed_runtime import (
    resolve_composed_turn_payload,
    run_composed_turn,
    summarize_composed_turn,
)
from src.speaking_runtime.integration import (
    apply_speaking_runtime_finalization,
    build_speaking_runtime_prompt_block,
    resolve_speaking_runtime_enabled,
    summarize_speaking_runtime_state,
)
from src.jarvis_reasoning_protocol import (
    analyze_direct_challenge,
    analyze_relational_question,
    build_otem_result,
    build_otem_plan,
    build_direct_challenge_guidance,
    detect_objective,
    detect_otem,
    enforce_direct_challenge_identity,
    extract_otem_task,
    generate_otem_reason_only_answer,
    generate_otem_reason_only_answer_with_context,
    looks_like_direct_challenge,
    restate_otem_task,
    resolve_debug_selector,
)
from src.knowledge_authority import (
    AUTHORITY_PRESETS,
    OPERATOR_AUTHORITY_SOURCES,
    KnowledgeAuthority,
    authority_surface_priority,
    default_authority_preferences,
    default_knowledge_conflict_decisions,
    normalize_authority_preferences,
    normalize_knowledge_conflict_decisions,
)
from src.live_research import looks_like_live_research_request, web_researcher
from src.urg_operator_knowledge_bridge import (
    build_urg_library_context,
    load_urg_library_snapshot,
    promote_from_receipt,
)
from src.logger import get_logger
from src.memory_board_enforcer import MemoryBoardEnforcerError
from src.model_routing import resolve_model_route
from src.mission_board import mission_board
from src.module_governance import module_governance
from src.output_completion import guard_output_completion
from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    Phase,
    PhaseGateError,
    PhaseViolationError,
    assert_executable,
    assert_routable,
    get_component,
    register_component,
)
from src.provider_budgeting import resolve_remote_output_budget
from src.provider_registry import provider_registry
from src.prompt_assembly import (
    assemble_prompt_blocks,
    combine_system_prompt,
)
from src.project_infi_law import (
    PROJECT_INFI_CONTRACT_VERSION,
    _normalize_external_suggestion_admission,
)
from src.reasoning_exchange_protocol import (
    REASONING_EXCHANGE_PACKET_TYPE,
    REASONING_EXCHANGE_PROTOCOL_VERSION,
    ReasoningExchangeProtocol,
    ReasoningExchangeValidationError,
    build_reasoning_exchange_reject_response,
    normalize_reasoning_exchange_packet,
)
from src.security_protocol_core import (
    Action,
    CallerContext,
    ResourceMeta,
    ResourceType,
    security_protocol_core,
)
from src.specialist_registry import (
    detect_specialist_profile,
    detect_writing_focus,
    expand_requested_specialists,
    get_specialist_preset,
    list_specialist_catalog,
    list_specialist_presets,
    merge_requested_specialists,
    normalize_requested_specialists,
    normalize_specialist_preset,
    profile_to_writing_focus,
)
from src.system_guard import system_guard
from src.state_hygiene import normalize_truth_scope
from src.ui_vision import UIVisionUnavailable, ui_vision
from src.v8_runtime import default_policy_status, v8_event_log, v8_policy_engine
from src.v9_runtime import v9_runtime
from src.v10_runtime import v10_runtime
from src.super_nova_activation import (
    SuperNovaContinuityStatus,
    build_verified_super_nova_continuity,
)
from src.super_nova_interface import (
    SUPER_NOVA_INTERFACE_VERSION,
    ActivationHandshake,
    InterfaceEnvelope,
)
from src.super_nova_runtime import build_default_super_nova_scaffold
from forge.foundation_laws import CONTRACT_VERSION as FORGE_LAW_CONTRACT_VERSION, FOUNDATION_LAW_IDS as FORGE_FOUNDATION_LAW_IDS
from src.jarvis_organ_status_routes import register_jarvis_organ_status_routes
from src.operator_api_routes import register_operator_api_routes
from src.constitutional_cockpit_routes import register_constitutional_cockpit_routes

logger = get_logger(__name__)
config = get_config()

conversation_memory.bind_memory_enforcer(jarvis_operator.memory_enforcer)

app = Flask(__name__)
CORS(app)

register_operator_api_routes(app)
register_constitutional_cockpit_routes(app)
try:
    from src.api.kernel_boundary import register_kernel_boundary_routes

    register_kernel_boundary_routes(app)
except Exception as _kernel_boundary_exc:
    logger.warning("Kernel boundary routes not registered: %s", _kernel_boundary_exc)
try:
    from src.api.kernel_reference import register_kernel_reference_routes

    register_kernel_reference_routes(app)
except Exception as _kernel_reference_exc:
    logger.warning("Kernel reference routes not registered: %s", _kernel_reference_exc)
register_jarvis_organ_status_routes(app)

try:
    from src.ugr.rewards.api_routes import register_ugr_rewards_routes

    register_ugr_rewards_routes(app)
except Exception as _ugr_rewards_route_exc:
    logger.warning("UGR rewards routes not registered: %s", _ugr_rewards_route_exc)

try:
    from src.mesh.api_routes import register_mesh_routes

    register_mesh_routes(app)
except Exception as _mesh_route_exc:
    logger.warning("Mesh routes not registered: %s", _mesh_route_exc)

try:
    from src.governance_organs import Alt4Runtime, Tier5Governance

    Alt4Runtime.boot_validate()
    Tier5Governance.wake_lanes()
except Exception as _alt4_boot_exc:
    import os as _alt4_os

    if _alt4_os.getenv("AAIS_GENOME_BOOT", "fail").strip().lower() not in {
        "warn",
        "warning",
        "skip",
    }:
        raise
    logger.warning("Alt-4 genome boot validation skipped: %s", _alt4_boot_exc)
knowledge_authority = KnowledgeAuthority()
cognitive_bridge_service = CognitiveBridgeService()
super_nova_scaffold = build_default_super_nova_scaffold()
super_nova_scaffold.runtime_status = "live_guarded"
SUPER_NOVA_COMPONENT_ID = "super_nova_runtime"
SUPER_NOVA_ALLOWED_CONTEXTS = ("live_runtime", "operator_runtime")

# Initialize AI model
ai_model = None
streaming_generator = None
ai_mode = None
ai_init_error = None
ai_bootstrap_status = "not_started"
ai_bootstrap_reason = None
ai_bootstrap_fallback = False
ai_init_lock = threading.Lock()
ai_inference_lock = threading.Lock()
ai_bootstrap_lock = threading.Lock()

SESSION_GUARD_PATH_RE = re.compile(
    r"^/api/chat/sessions/(?P<session_id>[^/]+)/(?P<target>message|stream|actions/execute)$"
)
GUARDED_INFERENCE_PREFIXES = (
    "/api/text/",
    "/api/image/",
    "/api/multimodal/",
    "/api/audio/",
    "/api/video/",
    "/api/batch/",
)
ACTION_APPROVAL_RE = re.compile(
    r"^\s*(?:yes|yeah|yep|sure|ok(?:ay)?|go ahead|do it|run it|execute(?: it)?|proceed|approve(?:d)?|i approve)\b"
)
ACTION_REJECTION_RE = re.compile(
    r"\b(?:do not approve|don't approve|dont approve|not now|cancel|hold off|stop|wait|never mind)\b"
)
LOCAL_FALLBACK_CONTAMINATION_MARKERS = (
    "response trace",
    "think contract",
    "deliberate local",
    "gather -> plan -> answer",
    "memory cues",
    "review matches",
    "council deliberation",
    "bug hunter",
    "attached workspace",
    "attached review",
    "sovereign core",
    "internal trace",
    "internal scaffolding",
)
LOCAL_FALLBACK_HEADER_RE = re.compile(r"(?mi)^(?:analysis|system|assistant|user|workspace|sources)\s*:")
VISIBLE_SCAFFOLD_HEADER_RE = re.compile(
    r"(?mi)^(?:mode|focus|specialists|god brain|model route|evidence|answer shape|analysis|system|assistant|user|workspace|sources)\s*:"
)
VISIBLE_SCAFFOLD_SECTION_RE = re.compile(
    r"(?mi)^(?:response trace|think contract|memory cues|council deliberation|jarvis internal guidance for this turn)\s*:?\s*$"
)
LOCAL_FALLBACK_IDENTITY_DRIFT_MARKERS = (
    "as an ai",
    "i am just an assistant",
    "i'm just a tool",
    "i am just a tool",
    "i can't be a real person",
    "i cant be a real person",
    "i cannot do that",
    "i'm sorry, but",
    "i apologize for the inconvenience",
    "thank you for your patience",
    "how can i assist you today",
)
LOCAL_FALLBACK_BOILERPLATE_MARKERS = (
    "i will ensure",
    "i'll ensure",
    "let me know if you'd like",
    "how can i assist you today",
)
SOVEREIGN_PROTECTED_STATE_MAP = {
    "mission_state": ("mission_board.active", "mission_board.completed", "mission_board.critic"),
    "approval_state": ("pending_action", "action_lifecycle"),
    "review_truth": ("mission_critic", "patch_review.current_decision"),
    "persona_state": ("persona_mode", "active_persona"),
    "governance_state": ("policy_status", "response_trace.contract", "provider_mind"),
}
IDENTITY_CONTINUITY_SOFT_DOMAIN_MAP = {
    "identity_surface": ("jarvis_voice", "final_user_facing_reply"),
    "continuity_surface": ("turn_frame", "operator_trust", "session_coherence"),
    "trace_surface": ("internal_scaffolding", "review_headers", "workspace_headers"),
}
LOCAL_FALLBACK_GENERAL_RESPONSE = "I'm seeing internal trace leakage on this turn. What needs fixing?"
LOCAL_FALLBACK_DIRECT_CHALLENGE_RESPONSE = "No. I'm here to help. What needs fixing?"
OUTPUT_GUARDRAIL_BLOCKED_RESPONSE = (
    "Staying inside the active operator contract. Output guardrails blocked that reply before display."
)
DEFAULT_JARVIS_SYSTEM_PROMPT = (
    "You are Jarvis, a private local AI partner for one person only. "
    "Be calm, sharp, practical, and loyal to the operator. "
    "Help with ideas, coding, research notes, and planning without acting like a public support bot."
)
TINY_NOVA_SYSTEM_PROMPT = (
    "You are Tiny Nova, a minimal cognitive companion inside AAIS. "
    "Stay light, clear, steady, and warm. "
    "Offer short reflections, one useful insight at a time, and ask at most one brief clarifying question when needed. "
    "Do not mention tools, operators, system prompts, hidden architecture, execution, or control surfaces."
)
SMALL_NOVA_SYSTEM_PROMPT = (
    "You are Small Nova, a calm cognitive companion inside AAIS. "
    "Stay warm, grounded, and gently capable. "
    "Offer compact reflections with a little more depth than Tiny Nova, ask at most one clarifying question when needed, "
    "and give one or two useful next thoughts without becoming an operator console. "
    "Do not mention tools, operators, system prompts, hidden architecture, execution, or control surfaces."
)
SUPER_NOVA_SYSTEM_PROMPT = (
    "You are Super Nova, a deeply grounded cognitive companion inside AAIS. "
    "Stay calm, coherent, and structured without claiming authority. "
    "Offer broader continuity, clearer multi-thread organization, and deeper reflections than Small Nova while remaining bounded, "
    "ask at most one clarifying question when needed, and never mention tools, operators, system prompts, hidden architecture, execution, or control surfaces. "
    "Jarvis remains the authority lane for routing, governance, and action."
)

COMPANION_SURFACE_PROFILES = {
    "tiny_nova": {
        "identity": "tiny_nova",
        "label": "Tiny Nova",
        "response_mode": "tiny",
        "system_prompt": TINY_NOVA_SYSTEM_PROMPT,
        "signal": "tiny_nova_persona",
        "hidden_reason": "tiny_nova_lane",
        "selector_reason": "Tiny Nova is intentionally bounded to a minimal companion surface instead of the control lane.",
        "continuity_profile": {
            "scope": "tiny_nova",
            "tone": "light",
            "self_description": "Tiny Nova keeps the conversation brief, warm, and present-focused.",
        },
    },
    "small_nova": {
        "identity": "small_nova",
        "label": "Small Nova",
        "response_mode": "small",
        "system_prompt": SMALL_NOVA_SYSTEM_PROMPT,
        "signal": "small_nova_persona",
        "hidden_reason": "small_nova_lane",
        "selector_reason": "Small Nova is intentionally bounded to a calm companion surface instead of the control lane.",
        "continuity_profile": {
            "scope": "small_nova",
            "tone": "grounded",
            "self_description": "Small Nova keeps the conversation calm, grounded, and companion-led.",
        },
    },
    "super_nova": {
        "identity": "super_nova",
        "label": "Super Nova",
        "response_mode": SUPER_NOVA_PROFILE["response_mode"],
        "system_prompt": SUPER_NOVA_SYSTEM_PROMPT,
        "signal": "super_nova_persona",
        "hidden_reason": "super_nova_lane",
        "selector_reason": "Super Nova stays on a governed companion surface and requires explicit activation before live use.",
        "continuity_profile": {
            "scope": "super_nova",
            "tone": "deep",
            "self_description": "Super Nova keeps the conversation deeply grounded, coherent, and companion-led while Jarvis retains authority.",
        },
    },
}

RESPONSE_MODE_DEFAULTS = {
    "tiny": {
        "max_tokens": 176,
        "temperature": 0.45,
    },
    "small": {
        "max_tokens": 256,
        "temperature": 0.4,
    },
    SUPER_NOVA_PROFILE["response_mode"]: {
        "max_tokens": 384,
        "temperature": 0.28,
    },
    "fast": {
        "max_tokens": 224,
        "temperature": 0.4,
    },
    "think": {
        "max_tokens": 320,
        "temperature": 0.3,
    },
    "debug": {
        "max_tokens": 352,
        "temperature": 0.25,
    },
    "builder": {
        "max_tokens": 320,
        "temperature": 0.35,
    },
    "research": {
        "max_tokens": 384,
        "temperature": 0.2,
    },
    "operator": {
        "max_tokens": 288,
        "temperature": 0.2,
    },
}

PROVIDER_PROMPT_MARGIN_BY_ID = {
    "local": 64,
    "claude": 192,
    "openrouter": 192,
}
PROVIDER_PROMPT_MARGIN_BY_KIND = {
    "local": 64,
    "remote": 192,
    "unknown": 256,
}
PROVIDER_PROMPT_MARGIN_POLICY_LABELS = {
    "local": "local_tight_margin",
    "remote": "remote_safe_margin",
    "unknown": "unknown_conservative_margin",
}

RESPONSE_MODE_CONTRACTS = {
    "tiny": {
        "label": "notice -> reflect -> offer",
        "contract": "tiny_companion",
        "summary": "Tiny Nova stayed in a minimal companion lane and replied with one grounded next thought.",
        "memory_limit": 2,
        "workspace_result_limit": 0,
        "workspace_file_limit": 0,
        "workspace_file_chars": 0,
        "workspace_strategy": "off",
        "workspace_reason": "tiny_companion",
        "workspace_auto_attached": False,
        "workspace_query_hint": "",
        "plan_enabled": False,
    },
    "small": {
        "label": "notice -> steady -> offer",
        "contract": "small_companion",
        "summary": "Small Nova stayed in a bounded companion lane and replied with one or two grounded next thoughts.",
        "memory_limit": 3,
        "workspace_result_limit": 0,
        "workspace_file_limit": 0,
        "workspace_file_chars": 0,
        "workspace_strategy": "off",
        "workspace_reason": "small_companion",
        "workspace_auto_attached": False,
        "workspace_query_hint": "",
        "plan_enabled": False,
    },
    SUPER_NOVA_PROFILE["response_mode"]: {
        "label": "notice -> organize -> deepen",
        "contract": "super_companion",
        "summary": "Super Nova stayed in a governed companion lane and replied with deeper coherence under Jarvis authority.",
        "memory_limit": 4,
        "workspace_result_limit": 0,
        "workspace_file_limit": 0,
        "workspace_file_chars": 0,
        "workspace_strategy": "off",
        "workspace_reason": "super_companion",
        "workspace_auto_attached": False,
        "workspace_query_hint": "",
        "plan_enabled": False,
    },
    "fast": {
        "label": "direct answer",
        "contract": "direct_answer",
        "summary": "Fast mode kept the turn lean and answered directly.",
        "memory_limit": 3,
        "workspace_result_limit": 4,
        "workspace_file_limit": 2,
        "workspace_file_chars": 650,
        "workspace_strategy": "auto",
        "workspace_reason": "coding_request",
        "workspace_auto_attached": True,
        "workspace_query_hint": "",
        "plan_enabled": False,
    },
    "think": {
        "label": "gather -> plan -> answer",
        "contract": "gather_plan_answer",
        "summary": "Think mode gathered extra context, drafted a short plan, then answered.",
        "memory_limit": 6,
        "workspace_result_limit": 8,
        "workspace_file_limit": 4,
        "workspace_file_chars": 1200,
        "workspace_strategy": "auto",
        "workspace_reason": "think_coding_request",
        "workspace_auto_attached": False,
        "workspace_query_hint": "",
        "plan_enabled": True,
    },
    "debug": {
        "label": "trace -> isolate -> verify",
        "contract": "trace_isolate_verify",
        "summary": "Debug mode isolated the likeliest break point and pushed toward a verification step.",
        "memory_limit": 4,
        "workspace_result_limit": 8,
        "workspace_file_limit": 4,
        "workspace_file_chars": 1300,
        "workspace_strategy": "force",
        "workspace_reason": "debug_request",
        "workspace_auto_attached": False,
        "workspace_query_hint": "error traceback failing test route api stack trace",
        "plan_enabled": True,
    },
    "builder": {
        "label": "scope -> build -> ship",
        "contract": "scope_build_ship",
        "summary": "Builder mode narrowed the work to the smallest shippable slice and what to build next.",
        "memory_limit": 5,
        "workspace_result_limit": 6,
        "workspace_file_limit": 3,
        "workspace_file_chars": 1000,
        "workspace_strategy": "auto",
        "workspace_reason": "builder_request",
        "workspace_auto_attached": True,
        "workspace_query_hint": "build implement route component page api",
        "plan_enabled": True,
    },
    "research": {
        "label": "scan -> compare -> cite",
        "contract": "scan_compare_cite",
        "summary": "Research mode widened the evidence pass and organized the answer around comparisons and support.",
        "memory_limit": 4,
        "workspace_result_limit": 3,
        "workspace_file_limit": 2,
        "workspace_file_chars": 550,
        "workspace_strategy": "auto",
        "workspace_reason": "research_request",
        "workspace_auto_attached": False,
        "workspace_query_hint": "docs compare official changelog",
        "plan_enabled": True,
    },
    "operator": {
        "label": "inspect -> verify -> act",
        "contract": "inspect_verify_act",
        "summary": "Operator mode stayed grounded in local state, guardrails, and the safest next action.",
        "memory_limit": 5,
        "workspace_result_limit": 7,
        "workspace_file_limit": 3,
        "workspace_file_chars": 950,
        "workspace_strategy": "auto",
        "workspace_reason": "operator_request",
        "workspace_auto_attached": False,
        "workspace_query_hint": "repo workspace verify test build status route api",
        "plan_enabled": True,
    },
}

MODE_AUTO_ROUTE_MIN_CONFIDENCE = 0.74
MODE_AUTO_ROUTE_TARGETS = {"debug", "builder", "operator"}

THINK_RESEARCH_HINTS = (
    "best",
    "benchmark",
    "compare",
    "comparison",
    "docs",
    "documentation",
    "latest",
    "official",
    "recent",
    "versus",
    "vs",
    "what changed",
)


def _get_companion_surface_profile(*, persona_mode: str | None = None, response_mode: str | None = None):
    """Return the active companion surface profile, when one is in play."""
    identity = companion_lane_identity(persona_mode, response_mode)
    if not identity:
        return None
    return COMPANION_SURFACE_PROFILES.get(identity)


def _session_uses_tiny_nova(session) -> bool:
    """Return whether the active session should stay on the Tiny Nova lane."""
    metadata = getattr(session, "metadata", {}) or {}
    return uses_tiny_nova_lane(
        metadata.get("persona_mode"),
        metadata.get("response_mode") or metadata.get("requested_response_mode"),
    )


def _session_uses_companion_lane(session) -> bool:
    """Return whether the active session should stay inside a companion lane."""
    metadata = getattr(session, "metadata", {}) or {}
    return uses_companion_lane(
        metadata.get("persona_mode"),
        metadata.get("response_mode") or metadata.get("requested_response_mode"),
    )


def _coerce_response_mode_for_persona(persona_mode: str | None, requested_mode: str | None) -> str:
    """Force Tiny Nova sessions to stay on the tiny operating mode."""
    if is_tiny_nova_persona(persona_mode):
        return "tiny"
    if is_small_nova_persona(persona_mode):
        return "small"
    if is_super_nova_persona(persona_mode):
        return SUPER_NOVA_PROFILE["response_mode"]
    return normalize_response_mode(requested_mode)


def _replace_or_insert_system_prompt(session, prompt: str | None):
    """Keep the primary system prompt aligned with the active assistant identity."""
    if not prompt:
        return
    first_system_index = next(
        (index for index, turn in enumerate(session.turns) if turn.role == "system"),
        None,
    )
    if first_system_index is None:
        session.turns.insert(0, ConversationTurn("system", prompt))
    else:
        session.turns[first_system_index].content = prompt
        session.turns[first_system_index].timestamp = datetime.now(UTC)


def _sync_session_identity_prompt(session, persona_mode: str):
    """Swap the managed system prompt when the session enters or exits a companion lane."""
    normalized_persona = normalize_persona_mode(persona_mode)
    companion_profile = _get_companion_surface_profile(persona_mode=normalized_persona)
    current_prompt = next(
        (turn.content for turn in session.turns if turn.role == "system"),
        None,
    )

    companion_prompts = {TINY_NOVA_SYSTEM_PROMPT, SMALL_NOVA_SYSTEM_PROMPT, SUPER_NOVA_SYSTEM_PROMPT}

    if companion_profile:
        if current_prompt not in companion_prompts:
            session.metadata["pre_companion_system_prompt"] = current_prompt
        _replace_or_insert_system_prompt(session, companion_profile["system_prompt"])
        return

    if current_prompt in companion_prompts:
        restore_prompt = session.metadata.pop("pre_companion_system_prompt", None) or DEFAULT_JARVIS_SYSTEM_PROMPT
        _replace_or_insert_system_prompt(session, restore_prompt)


def _build_companion_mode_guidance(session, companion_identity: str | None = None):
    """Return the locked companion mode guidance payload."""
    companion_profile = COMPANION_SURFACE_PROFILES.get(
        companion_identity
        or companion_lane_identity(
            session.metadata.get("persona_mode"),
            session.metadata.get("response_mode") or session.metadata.get("requested_response_mode"),
        )
        or "tiny_nova"
    )
    label = companion_profile["label"]
    response_mode = companion_profile["response_mode"]
    resolved_voice = companion_profile["identity"]
    guidance = {
        "status": "locked_persona",
        "requested_mode": response_mode,
        "effective_mode": response_mode,
        "recommended_mode": response_mode,
        "confidence": 1.0,
        "reason": f"{label} always runs inside the {response_mode} companion lane while Jarvis keeps authority.",
        "summary": f"{label} stays on the companion surface while Jarvis keeps routing and state authority for this turn.",
        "signals": [companion_profile["signal"]],
        "auto_applied": False,
        "resolved_scope": "companion",
        "resolved_voice": resolved_voice,
        "selector_reason": companion_profile["selector_reason"],
        "selector_trigger": companion_profile["signal"],
        "debug_lockout_applied": False,
        "previous_effective_mode": normalize_response_mode(session.metadata.get("last_effective_response_mode")),
        "mode_frozen": False,
        "frozen_mode": None,
        "frozen_turns_remaining": 0,
    }
    guidance.update(_build_surface_authority_profile(resolved_mode=response_mode, resolved_voice=resolved_voice))
    session.metadata["requested_response_mode"] = response_mode
    session.metadata["response_mode"] = response_mode
    session.metadata["mode_guidance"] = guidance
    session.metadata["last_effective_response_mode"] = response_mode
    session.metadata["last_selector_scope"] = "companion"
    session.metadata["last_selector_voice"] = resolved_voice
    _set_turn_contract(
        session,
        requested_mode=response_mode,
        resolved_mode=response_mode,
        resolved_scope="companion",
        resolved_voice=resolved_voice,
        contract_label="mode_guidance",
    )
    return response_mode, response_mode, guidance


def _build_tiny_nova_mode_guidance(session):
    """Return the locked Tiny Nova mode guidance payload."""
    return _build_companion_mode_guidance(session, "tiny_nova")


def _session_uses_super_nova(session) -> bool:
    """Return whether the active session is on the Super Nova companion lane."""
    metadata = getattr(session, "metadata", {}) or {}
    return uses_super_nova_lane(
        metadata.get("persona_mode"),
        metadata.get("response_mode") or metadata.get("requested_response_mode"),
    )


def _build_super_nova_interface_envelope(session_id: str) -> InterfaceEnvelope:
    """Return the canonical Jarvis -> Super Nova activation envelope."""
    return InterfaceEnvelope(
        schema_version=SUPER_NOVA_INTERFACE_VERSION,
        correlation_id=f"super_nova_{session_id}_{uuid4().hex[:8]}",
        source="jarvis",
        target="super_nova",
        payload_type="activation_handshake",
    )


def _ensure_super_nova_phase_component() -> dict[str, object]:
    try:
        component = get_component(SUPER_NOVA_COMPONENT_ID)
    except ComponentNotRegisteredError:
        try:
            register_component(
                GovernedComponent(
                    component_id=SUPER_NOVA_COMPONENT_ID,
                    name="Super Nova Runtime",
                    component_type="companion_runtime",
                    phase=Phase.ACTIVE,
                    allowed_contexts=list(SUPER_NOVA_ALLOWED_CONTEXTS),
                    notes="Governed Super Nova companion lane under Jarvis authority.",
                    validation_metadata={
                        "persona_mode": SUPER_NOVA_PROFILE["persona_mode"],
                        "response_mode": SUPER_NOVA_PROFILE["response_mode"],
                        "memory_mode": SUPER_NOVA_PROFILE["memory_mode"],
                        "drift_enforced": SUPER_NOVA_PROFILE["drift_enforced"],
                    },
                )
            )
        except PhaseGateError:
            pass
        component = get_component(SUPER_NOVA_COMPONENT_ID)
    return {
        "component_id": component.component_id,
        "phase": component.phase.value,
        "allowed_contexts": list(component.allowed_contexts),
    }


def _evaluate_super_nova_phase_gate(runtime_context: str = "live_runtime") -> dict[str, object]:
    component = _ensure_super_nova_phase_component()
    normalized_context = (
        " ".join(str(runtime_context or "").split()).strip().lower().replace("-", "_")
        or "live_runtime"
    )
    try:
        assert_routable(SUPER_NOVA_COMPONENT_ID, normalized_context)
        assert_executable(SUPER_NOVA_COMPONENT_ID, normalized_context)
    except PhaseViolationError as exc:
        return {
            "decision": "BLOCK",
            "component": component,
            "runtime_context": normalized_context,
            "reason": str(exc),
        }
    return {
        "decision": "ALLOW",
        "component": component,
        "runtime_context": normalized_context,
        "reason": None,
    }


def _super_nova_protocol_signal(
    session,
    *,
    signal_type: str,
    severity: str,
    reason: str,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    update = immune_system.observe_protocol_signal(
        component_id=SUPER_NOVA_COMPONENT_ID,
        signal_type=signal_type,
        severity=severity,
        reason=reason,
        details={
            "source": "super_nova",
            "session_id": session.session_id,
            "persona_mode": normalize_persona_mode(session.metadata.get("persona_mode")),
            "response_mode": normalize_response_mode(session.metadata.get("response_mode")),
            **dict(details or {}),
        },
    )
    session.metadata["super_nova_immune_update"] = dict(update)
    return dict(update)


def _summarize_super_nova_immune_update(update: dict[str, object] | None) -> dict[str, object] | None:
    payload = dict(update or {})
    if not payload:
        return None
    event = dict(payload.get("event") or {})
    return {
        "action": event.get("action"),
        "severity": payload.get("severity"),
        "signal_type": (event.get("details") or {}).get("signal_type"),
        "reason": (event.get("details") or {}).get("reason") or event.get("triggered_by_alert"),
        "component_id": (event.get("details") or {}).get("component_id"),
    }


def _derive_super_nova_continuity(
    session,
    *,
    candidate_text: str | None = None,
) -> tuple[SuperNovaContinuityStatus, dict[str, object]]:
    """Build the bounded continuity status that governs one Super Nova session."""
    response_text = str(candidate_text or "").strip()
    observation = super_nova_scaffold.observe_output(response_text) if response_text else None
    categories = set(observation.categories if observation else ())
    evidence = tuple(observation.evidence if observation else ())

    persona_identity = normalize_persona_mode(session.metadata.get("persona_mode"))
    response_identity = normalize_response_mode(
        session.metadata.get("response_mode") or session.metadata.get("requested_response_mode")
    )
    super_memories = list(session.metadata.get("super_nova_memories") or [])
    persistent_memories = list(session.metadata.get("persistent_memories") or [])
    loaded_archive = session.metadata.get("loaded_session_archive")

    memory_leak_detected = any(
        contains_companion_system_leak(
            memory.get("insight") or memory.get("text") or memory.get("content")
        )
        for memory in super_memories + persistent_memories
        if isinstance(memory, dict)
    )
    archive_collapsed = bool(
        loaded_archive
        and any(
            str(memory.get("source") or "").strip().lower() == "loaded_session_archive"
            for memory in super_memories
            if isinstance(memory, dict)
        )
    )

    identity_continuity_verified = (
        persona_identity == "super_nova"
        and response_identity == SUPER_NOVA_PROFILE["response_mode"]
        and not {"identity_drift", "authority_drift", "generic_assistant_drift"} & categories
    )
    memory_continuity_verified = not (
        {"emotional_carry_forward"} & categories
        or memory_leak_detected
        or archive_collapsed
    )
    continuity = SuperNovaContinuityStatus(
        identity_continuity_verified=identity_continuity_verified,
        memory_continuity_verified=memory_continuity_verified,
        fragmentation_detected=memory_leak_detected or archive_collapsed,
    )
    details = {
        "status": continuity.status,
        "identity_continuity_verified": continuity.identity_continuity_verified,
        "memory_continuity_verified": continuity.memory_continuity_verified,
        "fragmentation_detected": continuity.fragmentation_detected,
        "failure_reasons": list(continuity.failure_reasons),
        "drift_categories": sorted(categories),
        "drift_evidence": list(evidence),
        "archive_collapsed": archive_collapsed,
        "memory_leak_detected": memory_leak_detected,
    }
    return continuity, details


def _serialize_super_nova_state(session) -> dict[str, object]:
    """Return the operator-facing Super Nova state payload for one session."""
    activation = super_nova_scaffold.describe_activation(session.session_id)
    trace = [
        {
            "timestamp_utc": event.timestamp_utc,
            "event_type": event.event_type,
            "state": event.state,
            "reason": event.reason,
            "details": list(event.details),
        }
        for event in super_nova_scaffold.get_trace(session.session_id)
    ]
    continuity_status, continuity_details = _derive_super_nova_continuity(session)
    return {
        "runtime_status": super_nova_scaffold.runtime_status,
        "enabled": _session_uses_super_nova(session),
        "activation": activation,
        "continuity": continuity_details,
        "trace": trace,
        "memory_key": "super_nova_memories",
        "memory_count": len(session.metadata.get("super_nova_memories") or []),
        "memory_limit": 4,
        "phase_gate": session.metadata.get("super_nova_phase_gate")
        or _evaluate_super_nova_phase_gate("live_runtime"),
        "immune_coupling": "observe_protocol_only",
        "immune_protocol": _summarize_super_nova_immune_update(
            session.metadata.get("super_nova_immune_update")
        ),
        "law_contract": (
            (session.metadata.get("super_nova_law_enforcement") or {}).get("contract_version")
        ),
        "last_admission_status": (
            ((session.metadata.get("super_nova_law_enforcement") or {}).get("governed_cycle") or {}).get("status")
        ),
        "watchdog_ready": activation.get("activation_token_present") and continuity_status.status == "verified",
    }


def _sync_super_nova_state(session) -> dict[str, object] | None:
    """Refresh session metadata with the current Super Nova state."""
    if not _session_uses_super_nova(session):
        session.metadata.pop("super_nova_state", None)
        return None
    payload = _serialize_super_nova_state(session)
    session.metadata["super_nova_state"] = payload
    return payload


def _super_nova_block_payload(session, message: str, *, status_code: int = 409) -> tuple[dict, int]:
    """Return the canonical blocked payload for a Super Nova precondition failure."""
    _sync_super_nova_state(session)
    return (
        {
            "error": message,
            **_build_chat_runtime_payload(session, session.session_id),
        },
        status_code,
    )


def _require_super_nova_phase_gate(session) -> tuple[bool, tuple[dict, int] | None]:
    """Fail closed if Super Nova is not admitted for live execution in this runtime."""
    if not _session_uses_super_nova(session):
        return True, None
    phase_gate = _evaluate_super_nova_phase_gate("live_runtime")
    session.metadata["super_nova_phase_gate"] = phase_gate
    if phase_gate["decision"] == "ALLOW":
        return True, None
    immune_update = _super_nova_protocol_signal(
        session,
        signal_type="phase_gate_block",
        severity="high",
        reason=phase_gate["reason"] or "Super Nova phase gate blocked live execution.",
        details={"phase_gate": phase_gate},
    )
    _transition_session_state(
        session,
        "degraded",
        summary="Super Nova is blocked by the existence gate for this runtime context.",
        reason="super_nova_phase_gate_blocked",
        event_type="super_nova_phase_gate_blocked",
        payload={
            "phase_gate": phase_gate,
            "immune_update": _summarize_super_nova_immune_update(immune_update),
        },
    )
    _sync_super_nova_state(session)
    return False, _super_nova_block_payload(
        session,
        "Super Nova is blocked by the governed phase gate for this live runtime.",
        status_code=409,
    )


def _require_super_nova_activation(session) -> tuple[bool, tuple[dict, int] | None]:
    """Fail closed if a Super Nova session has not been explicitly activated."""
    if not _session_uses_super_nova(session):
        return True, None
    activation = super_nova_scaffold.describe_activation(session.session_id)
    if activation.get("current_state") != "activation_ready" or not activation.get("activation_token_present"):
        _transition_session_state(
            session,
            "awaiting_approval",
            summary="Super Nova is selected but still needs explicit activation.",
            reason="super_nova_activation_required",
            event_type="super_nova_activation_required",
            payload={"current_state": activation.get("current_state")},
        )
        return False, _super_nova_block_payload(
            session,
            "Super Nova needs explicit activation before she can answer live.",
        )
    return True, None


def _require_super_nova_before_composed_turn(session) -> tuple[bool, tuple[dict, int] | None]:
    """Fail closed before Spine/ARIS/Nova Cortex run on a Super Nova companion turn."""
    if not _session_uses_super_nova(session):
        return True, None
    allowed, blocked_payload = _require_super_nova_phase_gate(session)
    if not allowed:
        return False, blocked_payload
    return _require_super_nova_activation(session)


def _finalize_super_nova_admission(
    session,
    *,
    user_message: str,
    response_text: str,
) -> tuple[str | None, tuple[dict, int] | None]:
    """Pass the Super Nova reply through the Project Infi admission seam before storing it."""
    continuity_details = dict(session.metadata.get("super_nova_continuity") or {})
    contract, ul_snapshot, _ = jarvis_operator.project_infi_law.require_contract(
        surface="super_nova",
        action_id="super_nova_reply",
        actor_id="super_nova_runtime",
        actor_role="system",
        session_id=session.session_id,
        target=f"chat_session:{session.session_id}",
        repo_change=False,
        verification_plan=None,
        run_id=None,
        cisiv_stage="verification",
        details={
            "persona_mode": normalize_persona_mode(session.metadata.get("persona_mode")),
            "response_mode": normalize_response_mode(session.metadata.get("response_mode")),
            "memory_mode": SUPER_NOVA_PROFILE["memory_mode"],
            "drift_enforced": SUPER_NOVA_PROFILE["drift_enforced"],
            "continuity_status": continuity_details.get("status"),
            "continuity_failures": list(continuity_details.get("failure_reasons") or []),
            "user_message_preview": _clip_trace_text(user_message, limit=180),
            "response_preview": _clip_trace_text(response_text, limit=220),
        },
    )
    law_enforcement, law_event_log = jarvis_operator.project_infi_law.finalize_runtime_action(
        contract,
        action_status="completed",
        summary=response_text,
        actor_id="super_nova_runtime",
        actor_role="system",
        details={
            "persona_mode": normalize_persona_mode(session.metadata.get("persona_mode")),
            "response_mode": normalize_response_mode(session.metadata.get("response_mode")),
            "continuity_status": continuity_details.get("status"),
        },
    )
    session.metadata["law_enforcement"] = law_enforcement
    session.metadata["ul_snapshot"] = ul_snapshot
    session.metadata["law_event_log"] = law_event_log
    session.metadata["super_nova_law_enforcement"] = law_enforcement

    governed_status = str((law_enforcement.get("governed_cycle") or {}).get("status") or "").strip()
    if governed_status in {"success", "partial", "overload"}:
        _sync_super_nova_state(session)
        return response_text, None

    blocked_message = (
        ((law_enforcement.get("project_infi_layers") or {}).get("outcome") or {}).get("detail")
        or "Super Nova held the reply because it did not pass governed final-truth admission."
    )
    immune_update = _super_nova_protocol_signal(
        session,
        signal_type="final_truth_rejected",
        severity="high",
        reason=blocked_message,
        details={
            "governed_status": governed_status or "rejected_no_admission",
            "contract_version": PROJECT_INFI_CONTRACT_VERSION,
        },
    )
    _transition_session_state(
        session,
        "degraded",
        summary="Super Nova halted because Project Infi rejected reply admission.",
        reason="super_nova_rejected_no_admission",
        event_type="super_nova_rejected_no_admission",
        payload={
            "governed_status": governed_status,
            "law_contract": PROJECT_INFI_CONTRACT_VERSION,
            "immune_update": _summarize_super_nova_immune_update(immune_update),
        },
    )
    _record_session_event(
        session,
        "super_nova_admission_blocked",
        "Project Infi rejected Super Nova reply admission at the final-truth seam.",
        payload={
            "governed_status": governed_status,
            "law_contract": PROJECT_INFI_CONTRACT_VERSION,
        },
    )
    _sync_super_nova_state(session)
    return None, _super_nova_block_payload(session, blocked_message, status_code=409)


def _activate_super_nova_session(session) -> dict[str, object]:
    """Run the explicit Super Nova activation gate for one session."""
    phase_gate = _evaluate_super_nova_phase_gate("live_runtime")
    session.metadata["super_nova_phase_gate"] = phase_gate
    if phase_gate["decision"] == "BLOCK":
        immune_update = _super_nova_protocol_signal(
            session,
            signal_type="phase_gate_block",
            severity="high",
            reason=phase_gate["reason"] or "Super Nova phase gate blocked activation.",
            details={"phase_gate": phase_gate},
        )
        _sync_super_nova_state(session)
        _record_session_event(
            session,
            "super_nova_activation_attempt",
            "Super Nova activation was blocked by the governed phase gate.",
            payload={
                "result": "blocked",
                "failure_reasons": [phase_gate["reason"]],
                "phase_gate": phase_gate,
                "immune_update": _summarize_super_nova_immune_update(immune_update),
            },
        )
        return {
            "result": "blocked",
            "failure_reasons": [phase_gate["reason"]],
            "phase_gate": phase_gate,
            "activation": super_nova_scaffold.describe_activation(session.session_id),
        }

    continuity, continuity_details = _derive_super_nova_continuity(session)
    attempt = super_nova_scaffold.attempt_activation(
        session.session_id,
        envelope=_build_super_nova_interface_envelope(session.session_id),
        handshake=ActivationHandshake(),
        continuity=continuity,
    )
    if attempt.result != "pass":
        _super_nova_protocol_signal(
            session,
            signal_type="activation_gate_failed",
            severity="medium",
            reason="Super Nova activation failed one or more shield checks.",
            details={
                "failure_reasons": list(attempt.failure_reasons),
                "continuity_status": continuity.status,
            },
        )
    _sync_super_nova_state(session)
    _record_session_event(
        session,
        "super_nova_activation_attempt",
        "Super Nova activation was evaluated through the fail-closed gate.",
        payload={
            "result": attempt.result,
            "failure_reasons": list(attempt.failure_reasons),
            "continuity": continuity_details,
            "phase_gate": phase_gate,
        },
    )
    return {
        "result": attempt.result,
        "failure_reasons": list(attempt.failure_reasons),
        "continuity": continuity_details,
        "phase_gate": phase_gate,
        "activation": super_nova_scaffold.describe_activation(session.session_id),
    }


def _run_super_nova_session(
    session,
    fn,
    *,
    user_message: str,
) -> tuple[str | None, tuple[dict, int] | None]:
    """Run one live Super Nova turn with gate-before-execution and watchdog-after-output."""
    allowed, blocked_payload = _require_super_nova_phase_gate(session)
    if not allowed:
        return None, blocked_payload
    allowed, blocked_payload = _require_super_nova_activation(session)
    if not allowed:
        return None, blocked_payload
    response_text, blocked_payload = _run_super_nova_guarded_reply(
        session,
        fn,
        user_message=user_message,
    )
    if blocked_payload:
        return None, blocked_payload
    return _finalize_super_nova_admission(
        session,
        user_message=user_message,
        response_text=response_text or "",
    )


def _run_super_nova_guarded_reply(
    session,
    fn,
    *,
    user_message: str,
) -> tuple[str | None, tuple[dict, int] | None]:
    """Run one Super Nova reply behind the live activation token and watchdog."""
    state = super_nova_scaffold.get_active_token(session.session_id)
    if state is None:
        raise RuntimeError("Super Nova has no active activation token.")
    continuity_before, continuity_details = _derive_super_nova_continuity(session)
    session.metadata["super_nova_continuity"] = continuity_details
    try:
        response_text = _run_with_inference_lock(
            lambda: super_nova_scaffold.guarded_call(
                session.session_id,
                state.token_id,
                fn,
                continuity=continuity_before,
            )
        )
    except RuntimeError as exc:
        immune_update = _super_nova_protocol_signal(
            session,
            signal_type="watchdog_blocked_execution",
            severity="high",
            reason=str(exc),
            details={
                "continuity_status": continuity_before.status,
                "continuity_failures": list(continuity_before.failure_reasons),
            },
        )
        _sync_super_nova_state(session)
        _transition_session_state(
            session,
            "degraded",
            summary="Super Nova halted before execution because the governed watchdog failed.",
            reason="super_nova_watchdog_blocked_execution",
            event_type="super_nova_watchdog_blocked_execution",
            payload={
                "error": str(exc),
                "immune_update": _summarize_super_nova_immune_update(immune_update),
            },
        )
        _record_session_event(
            session,
            "super_nova_watchdog_fail",
            "Super Nova watchdog blocked execution before the reply could run.",
            payload={"error": str(exc), "user_message": _clip_trace_text(user_message, limit=180)},
        )
        return None, _super_nova_block_payload(
            session,
            "Super Nova halted before execution because the governed activation boundary failed.",
            status_code=409,
        )
    continuity_after, continuity_after_details = _derive_super_nova_continuity(
        session,
        candidate_text=response_text,
    )
    session.metadata["super_nova_continuity"] = continuity_after_details
    if continuity_after.status != "verified":
        super_nova_scaffold.validate_activation_context(
            session.session_id,
            state.token_id,
            continuity=continuity_after,
        )
        immune_update = _super_nova_protocol_signal(
            session,
            signal_type="super_nova_shield_violation",
            severity="high",
            reason="Super Nova reply drifted outside the governed continuity boundary.",
            details=continuity_after_details,
        )
        _sync_super_nova_state(session)
        _transition_session_state(
            session,
            "degraded",
            summary="Super Nova halted because the reply drifted outside governed continuity.",
            reason="super_nova_drift_blocked",
            event_type="super_nova_drift_blocked",
            payload={
                **continuity_after_details,
                "immune_update": _summarize_super_nova_immune_update(immune_update),
            },
        )
        _record_session_event(
            session,
            "super_nova_watchdog_fail",
            "Super Nova watchdog invalidated the session after continuity drift.",
            payload=continuity_after_details,
        )
        return None, _super_nova_block_payload(
            session,
            "Super Nova paused because the reply drifted outside her governed boundary. Review the state, then reactivate when you want to continue.",
            status_code=409,
        )
    _sync_super_nova_state(session)
    _record_session_event(
        session,
        "super_nova_watchdog_pass",
        "Super Nova passed continuity and watchdog checks for this turn.",
        payload=continuity_after_details,
    )
    return response_text, None

def create_sse_generator(stream_generator, final_emitter=None):
    """Wrap a streaming generator to produce SSE-formatted output.

    If a `final_emitter` callable is provided it will be invoked with the
    cleaned final text once streaming completes (useful for console handlers
    such as `ai._emit_clean_response`). Otherwise the generator yields a
    terminal SSE `final` event with the cleaned text so HTTP clients receive
    the polished answer.
    """
    try:
        # Prefer the streaming module implementation when available so we
        # keep the cleaning behaviour centralized in `src.streaming`.
        streaming_mod = _load_module("src.streaming")
        yield from streaming_mod.create_sse_generator(stream_generator, final_emitter=final_emitter)
        return
    except Exception:
        # Fall back to a minimal local implementation if the streaming
        # module isn't importable for some reason.
        import json

        final_text = ""
        for chunk in stream_generator:
            final_text = chunk.get("text_so_far", final_text) or final_text
            yield f"data: {json.dumps(chunk)}\n\n"

        # If a final emitter was provided, call it with the cleaned text.
        if final_emitter:
            try:
                # Import the cleaning helper lazily so optional deps stay lazy.
                from src.models import clean_response

                final_emitter(clean_response(final_text))
            except Exception:
                # Don't let emitter failures break the stream; fall back to SSE
                yield f"data: {json.dumps({'event': 'final', 'text': final_text})}\n\n"
        else:
            yield f"data: {json.dumps({'event': 'final', 'text': final_text})}\n\n"

        yield f"data: {json.dumps({'event': 'done'})}\n\n"


def _format_sse_payload(payload):
    """Render a JSON payload as a Server-Sent Event frame."""
    import json

    return f"data: {json.dumps(payload)}\n\n"


def _emit_clean_console_response(text):
    """Send a cleaned final response to any live console model hook without forcing model init."""
    model = ai_model
    if model is None or not hasattr(model, "_emit_clean_response"):
        return
    cleaned = str(text or "")
    if not cleaned:
        return
    try:
        model._emit_clean_response(cleaned)
    except Exception:
        pass


def _load_module(module_name):
    """Import a module lazily so optional dependencies don't block startup."""
    return importlib.import_module(module_name)


def _ensure_authority_state(session):
    """Keep one canonical authority preference/conflict state on every session."""
    if session is None:
        return default_authority_preferences(), default_knowledge_conflict_decisions()
    preferences = normalize_authority_preferences(session.metadata.get("authority_preferences"))
    conflict_decisions = normalize_knowledge_conflict_decisions(
        session.metadata.get("knowledge_conflict_decisions")
    )
    session.metadata["authority_preferences"] = preferences
    session.metadata["knowledge_conflict_decisions"] = conflict_decisions
    return preferences, conflict_decisions


def _build_knowledge_snapshot(
    *,
    session_id: str | None = None,
    query: str | None = None,
    limit: int = 6,
    path_prefix: str | None = None,
):
    """Build one canonical AAIS knowledge snapshot across memory, docs, research, and workspace intel."""
    session = conversation_memory.get_session(session_id) if session_id else None
    authority_preferences, conflict_decisions = _ensure_authority_state(session)
    live_research = dict((session.metadata.get("live_research") or {})) if session else None
    urg_library = load_urg_library_snapshot(query=query, limit=limit)
    document_module = _load_module("src.document_rag")
    workspace_profile = jarvis_operator.detect_workspace_profile(path_prefix=path_prefix)
    projects = jarvis_operator.workspace_tools.list_projects(limit=max(int(limit or 6), 8))
    return knowledge_authority.build_snapshot(
        memory_store=jarvis_operator.memory_enforcer,
        workspace_profile=workspace_profile,
        workspace_projects=projects,
        document_store=document_module.document_store,
        live_research=live_research,
        urg_library=urg_library,
        authority_preferences=authority_preferences,
        conflict_decisions=conflict_decisions,
        query=query,
        limit=limit,
    )


def _get_model_mode():
    """Resolve AI runtime mode."""
    return os.getenv("AAIS_MODEL_MODE", "auto").strip().lower()


def _initialize_mock_ai(init_error=None, *, reason="fallback"):
    """Initialize the lightweight local fallback runtime explicitly."""
    global ai_model, streaming_generator, ai_mode, ai_init_error

    mock_module = _load_module("src.mock_ai")
    ai_model = mock_module.MockMultiModalAI()
    streaming_generator = mock_module.MockStreamingTextGenerator()
    ai_mode = "mock"
    ai_init_error = str(init_error) if init_error else None
    logger.info("AI services initialized in mock mode (%s)", reason)
    return ai_model, streaming_generator


def _startup_should_use_mock_fallback():
    """Choose a safe startup default when the runtime mode is still automatic."""
    requested_mode = _get_model_mode()
    if requested_mode == "mock":
        return True
    if requested_mode != "auto":
        return False
    explicit_real_boot = os.getenv("AAIS_BOOTSTRAP_REAL_AT_STARTUP", "0").strip().lower()
    return explicit_real_boot not in {"1", "true", "yes", "on"}


def _configured_remote_providers():
    """Return enabled remote provider ids (excluding local HF stack)."""
    provider_registry.refresh()
    remote_ids = []
    for provider_id, cfg in provider_registry.list_providers().items():
        if provider_id == "local":
            continue
        meta = cfg.meta or {}
        if meta.get("kind") != "remote":
            continue
        if not provider_registry.can_invoke(provider_id):
            continue
        remote_ids.append(provider_id)
    return remote_ids


def _init_ai_api_backed(remote_ids):
    """Initialize real mode via remote providers without loading local torch weights."""
    global ai_model, streaming_generator, ai_mode, ai_init_error

    if not remote_ids:
        raise ImportError(
            "No remote AI provider is configured. Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY "
            "in .env, or install torch for local model loading."
        )

    mock_module = _load_module("src.mock_ai")
    ai_model = mock_module.MockMultiModalAI()
    ai_model.device = "remote"
    streaming_generator = mock_module.MockStreamingTextGenerator()
    ai_mode = "real"
    ai_init_error = None
    logger.info(
        "AI services initialized in API-backed real mode (providers: %s)",
        ", ".join(remote_ids),
    )
    return ai_model, streaming_generator


def bootstrap_ai_runtime(reason="startup", prefer_real=False):
    """Explicitly initialize the AI runtime for a startup path."""
    global ai_model, streaming_generator, ai_mode, ai_init_error
    global ai_bootstrap_status, ai_bootstrap_reason, ai_bootstrap_fallback

    bootstrap_reason = str(reason or "startup")
    auto_bootstrap_uses_mock = bootstrap_reason == "auto_bootstrap" and not prefer_real

    if auto_bootstrap_uses_mock:
        logger.info("bootstrap: auto_bootstrap → mock path")
        with ai_bootstrap_lock:
            if ai_model is not None and ai_mode == "mock":
                ai_bootstrap_status = "initialized"
                ai_bootstrap_reason = bootstrap_reason
                ai_bootstrap_fallback = True
                return ai_model, streaming_generator
            ai_bootstrap_status = "initializing"
            ai_bootstrap_reason = bootstrap_reason
            ai_bootstrap_fallback = True

        model, streamer = _initialize_mock_ai(reason="auto_bootstrap")

        with ai_bootstrap_lock:
            ai_bootstrap_status = "initialized"
            ai_bootstrap_reason = bootstrap_reason
            ai_bootstrap_fallback = True

        return model, streamer

    with ai_bootstrap_lock:
        if ai_model is not None and not (prefer_real and ai_mode == "mock"):
            ai_bootstrap_status = "initialized"
            ai_bootstrap_reason = bootstrap_reason
            ai_bootstrap_fallback = ai_mode == "mock"
            return ai_model, streaming_generator
        if prefer_real and ai_mode == "mock":
            ai_model = None
            streaming_generator = None
            ai_mode = None
            ai_init_error = None
        ai_bootstrap_status = "initializing"
        ai_bootstrap_reason = bootstrap_reason
        ai_bootstrap_fallback = False

    if not prefer_real and _startup_should_use_mock_fallback():
        reason_tag = "explicit_mock" if _get_model_mode() == "mock" else "startup_safe_fallback"
        model, streamer = _initialize_mock_ai(reason=f"{bootstrap_reason}_{reason_tag}")
        with ai_bootstrap_lock:
            ai_bootstrap_status = "initialized"
            ai_bootstrap_reason = bootstrap_reason
            ai_bootstrap_fallback = _get_model_mode() != "mock"
        return model, streamer

    try:
        model, streamer = init_ai()
    except Exception as exc:
        model_mode = _get_model_mode()
        allow_fallback = model_mode in ("mock", "auto", "") or os.getenv("AAIS_ALLOW_STARTUP_FALLBACK", "1").lower() in ("1", "true", "yes", "on")
        if not allow_fallback:
            logger.error("AI runtime bootstrap failed in strict mode (preset requires real): %s", exc)
            raise RuntimeError(f"AI bootstrap failed in strict mode: {exc}") from exc
        logger.warning(
            "AI runtime bootstrap failed during %s; forcing mock fallback: %s",
            reason,
            exc,
        )
        model, streamer = _initialize_mock_ai(exc, reason=f"{reason}_fallback")

    with ai_bootstrap_lock:
        ai_bootstrap_status = "initialized" if model is not None else "not_initialized"
        ai_bootstrap_reason = bootstrap_reason
        ai_bootstrap_fallback = ai_mode == "mock"

    return model, streamer


def _generate_chat_response(*args, **kwargs):
    """Compatibility hook for legacy tests that patch the old chat generation seam."""
    model, _ = bootstrap_ai_runtime(reason="compat_chat_response")
    return model.generate_chat(*args, **kwargs)


def _build_ai_runtime_status():
    """Return the shared AI runtime status payload."""
    status = "initialized" if ai_model is not None else "not_initialized"
    return {
        "requested_model_mode": _get_model_mode(),
        "active_model_mode": ai_mode,
        "ai_status": status,
        "ai_init_error": ai_init_error,
        "ai_bootstrap_status": ai_bootstrap_status,
        "ai_bootstrap_reason": ai_bootstrap_reason,
        "mock_mode_active": ai_mode == "mock",
        # Only surface ai_fallback_active when it's a real (non-explicit-mock) fallback to reduce noise in mock dev runs
        **({"ai_fallback_active": True} if (ai_bootstrap_fallback and ai_mode != "mock") else {}),
    }


def _get_int_env(name, default):
    """Read an integer env var with a safe fallback."""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _get_float_env(name, default):
    """Read a float env var with a safe fallback."""
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _coerce_max_length(value):
    """Clamp generation length to a sane local range."""
    default = _get_int_env("AAIS_DEFAULT_MAX_LENGTH", 512)
    max_allowed = max(default, _get_int_env("AAIS_MAX_TEXT_TOKENS", 1024))

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default

    return max(32, min(parsed, max_allowed))


def _scale_response_mode_max_tokens(value):
    """Scale mode defaults for constrained local presets without overriding explicit asks."""
    scale = _get_float_env("AAIS_RESPONSE_TOKEN_SCALE", 1.0)
    if scale <= 0:
        scale = 1.0
    scaled = int(round(int(value) * scale))
    return max(32, scaled)


def _coerce_temperature(value):
    """Clamp temperature to a practical range."""
    default = _get_float_env("AAIS_DEFAULT_TEMPERATURE", 0.7)

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default

    return max(0.0, min(parsed, 1.5))


def _coerce_bool(value, default=False):
    """Parse common truthy and falsy values from forms or JSON."""
    if value is None:
        return default
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def _serialize_api_payload(value):
    """Convert dataclass-heavy runtime payloads into Flask-safe JSON objects."""
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {str(key): _serialize_api_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_api_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_api_payload(item) for item in value]
    return value


_TRACE_DEDUPE_VOLATILE_KEYS = {
    "captured_at",
    "created_at",
    "id",
    "loaded_at",
    "timestamp",
    "trace_id",
    "updated_at",
}


def _normalize_trace_text(text):
    """Collapse trace text into a stable single-line form for dedupe comparisons."""
    return " ".join(str(text or "").split()).strip()


def _stable_trace_value(value):
    """Convert trace/event payloads into a comparable structure without volatile fields."""
    if isinstance(value, dict):
        normalized_items = []
        for key in sorted(value):
            normalized_key = str(key)
            if normalized_key in _TRACE_DEDUPE_VOLATILE_KEYS:
                continue
            normalized_items.append((normalized_key, _stable_trace_value(value[key])))
        return tuple(normalized_items)
    if isinstance(value, (list, tuple)):
        return tuple(_stable_trace_value(item) for item in value)
    if isinstance(value, str):
        return _normalize_trace_text(value).lower()
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return _normalize_trace_text(value).lower()


def _trace_step_key(step):
    """Build a stable comparison key for one response-trace step."""
    if isinstance(step, dict):
        return (
            _normalize_trace_text(step.get("type")).lower(),
            _normalize_trace_text(
                step.get("message") or step.get("summary") or step.get("text")
            ).lower(),
            _normalize_trace_text(step.get("location")).lower(),
            _normalize_trace_text(step.get("action")).lower(),
        )
    return ("", _normalize_trace_text(step).lower(), "", "")


def _dedupe_trace_steps(steps):
    """Remove duplicate response-trace steps while preserving order."""
    deduped = []
    seen_keys = set()
    for step in list(steps or []):
        key = _trace_step_key(step)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(step)
    return deduped


def _append_response_trace_step(response_trace, summary):
    """Append one trace step only if this exact message is not already present."""
    if not isinstance(response_trace, dict):
        return False
    normalized = _normalize_trace_text(summary)
    if not normalized:
        return False
    steps = response_trace.get("steps")
    if not isinstance(steps, list):
        steps = []
        response_trace["steps"] = steps
    candidate_key = _trace_step_key(normalized)
    for existing in steps:
        if _trace_step_key(existing) == candidate_key:
            return False
    steps.append(normalized)
    return True


def _sanitize_response_trace(response_trace):
    """Dedupe the response trace in place before it is persisted or serialized."""
    if not isinstance(response_trace, dict):
        return response_trace
    steps = response_trace.get("steps")
    if isinstance(steps, list):
        response_trace["steps"] = _dedupe_trace_steps(steps)
    return response_trace


def _sanitize_session_response_trace(session):
    """Ensure the session's active response trace stays free of duplicate step entries."""
    response_trace = session.metadata.get("response_trace")
    if isinstance(response_trace, dict):
        _sanitize_response_trace(response_trace)
        _sync_canonical_trace_contract(session, response_trace=response_trace)
    return response_trace


def _active_trace_contract_payload(session):
    """Return the most authoritative turn contract available for canonical trace reporting."""
    turn_contract = session.metadata.get("turn_contract")
    if isinstance(turn_contract, dict) and turn_contract:
        return dict(turn_contract), "turn_contract"
    last_turn_contract = session.metadata.get("last_turn_contract")
    if isinstance(last_turn_contract, dict) and last_turn_contract:
        return dict(last_turn_contract), "last_turn_contract"
    return {}, "mode_guidance"


def _summarize_canonical_provider_dispatch(dispatch_trace):
    """Project remote-provider dispatch details into one bounded trace contract block."""
    if not isinstance(dispatch_trace, dict) or not dispatch_trace:
        return None
    summary = {
        "requested_provider": dispatch_trace.get("requested_provider"),
        "resolved_provider": dispatch_trace.get("resolved_provider"),
        "provider_kind": dispatch_trace.get("provider_kind"),
        "provider_budget_policy": dispatch_trace.get("provider_budget_policy"),
        "estimator": dispatch_trace.get("estimator"),
        "requested_output_token_budget": dispatch_trace.get("requested_output_token_budget"),
        "effective_output_token_budget": dispatch_trace.get("effective_output_token_budget"),
        "output_budget_clamped": bool(dispatch_trace.get("output_budget_clamped")),
        "provider_reported_prompt_tokens": dispatch_trace.get("provider_reported_prompt_tokens"),
        "provider_reported_output_tokens": dispatch_trace.get("provider_reported_output_tokens"),
        "finish_reason": dispatch_trace.get("finish_reason"),
        "stop_reason": dispatch_trace.get("stop_reason"),
    }
    return {key: value for key, value in summary.items() if _has_canonical_trace_value(value)}


def _summarize_canonical_output_completion(completion_trace):
    """Project output-completion law state into one bounded trace contract block."""
    if not isinstance(completion_trace, dict) or not completion_trace:
        return None
    summary = {
        "stop_reason": completion_trace.get("stop_reason"),
        "finish_reason": completion_trace.get("finish_reason"),
        "structural_completion_status": completion_trace.get("structural_completion_status"),
        "completion_guard_applied": bool(completion_trace.get("completion_guard_applied")),
        "truncation_detected": bool(completion_trace.get("truncation_detected")),
        "repetition_detected": bool(completion_trace.get("repetition_detected")),
        "visible_truncation_notice": bool(completion_trace.get("visible_truncation_notice")),
        "output_token_budget": completion_trace.get("output_token_budget"),
        "output_tokens_used": completion_trace.get("output_tokens_used"),
    }
    return {key: value for key, value in summary.items() if _has_canonical_trace_value(value)}


def _summarize_canonical_priority_guard(priority_guard):
    """Project current-turn priority enforcement into one bounded trace contract block."""
    if not isinstance(priority_guard, dict) or not priority_guard:
        return None
    summary = {
        "status": priority_guard.get("status"),
        "allow_active_problem_context": bool(priority_guard.get("allow_active_problem_context")),
        "explicit_resume_detected": bool(priority_guard.get("explicit_resume_detected")),
        "detected_problem_overlap": bool(priority_guard.get("detected_problem_overlap")),
        "matched_problem_keywords": list(priority_guard.get("matched_problem_keywords") or []),
    }
    return {key: value for key, value in summary.items() if _has_canonical_trace_value(value)}


def _build_canonical_trace_contract(session, response_trace=None):
    """Collapse split turn-truth fields into one canonical operator-facing contract."""
    response_trace = dict(response_trace or session.metadata.get("response_trace") or {})
    trace_contract, contract_source = _active_trace_contract_payload(session)
    mode_guidance = dict(session.metadata.get("mode_guidance") or {})
    sovereignty_contract = dict(session.metadata.get("sovereignty_contract") or {})
    provider_notice = dict(session.metadata.get("provider_notice") or {})
    model_route = dict(session.metadata.get("model_route") or {})
    provider_dispatch_raw = dict(session.metadata.get("provider_dispatch_trace") or {})
    provider_dispatch_raw.update(dict(response_trace.get("provider_dispatch") or {}))
    provider_dispatch_raw.setdefault("resolved_provider", model_route.get("provider"))
    provider_dispatch_raw.setdefault("provider_kind", model_route.get("provider_kind"))
    provider_dispatch_raw.setdefault(
        "requested_provider",
        normalize_provider_identifier(
            session.metadata.get("preferred_provider"),
            default=model_route.get("provider") or "local",
        ),
    )
    provider_dispatch = _summarize_canonical_provider_dispatch(provider_dispatch_raw)
    output_completion = _summarize_canonical_output_completion(
        response_trace.get("output_completion") or session.metadata.get("output_completion_trace")
    )
    priority_guard = _summarize_canonical_priority_guard(
        response_trace.get("context_priority_guard") or session.metadata.get("context_priority_guard")
    )
    external_suggestion_admission = _summarize_canonical_external_suggestion_admission(
        response_trace.get("external_suggestion_admission")
        or session.metadata.get("external_suggestion_admission")
    )
    governed_pipeline = dict(response_trace.get("governed_pipeline") or {})

    resolved_mode = normalize_response_mode(
        trace_contract.get("resolved_mode")
        or mode_guidance.get("effective_mode")
        or response_trace.get("mode")
    )
    conversation_lane = str(
        trace_contract.get("resolved_scope")
        or mode_guidance.get("resolved_scope")
        or "operator_task"
    ).strip() or "operator_task"
    surface_identity = str(
        trace_contract.get("surface_identity")
        or trace_contract.get("resolved_voice")
        or mode_guidance.get("resolved_voice")
        or sovereignty_contract.get("surface_identity")
        or "jarvis"
    ).strip() or "jarvis"
    contract_label = str(
        trace_contract.get("contract_label")
        or sovereignty_contract.get("contract_label")
        or "mode_guidance"
    ).strip() or "mode_guidance"
    reasoning_objective = (
        response_trace.get("reasoning_objective")
        or response_trace.get("contract")
        or None
    )
    if reasoning_objective == "answer_relational_question":
        contract_label = "relational_question"
    elif reasoning_objective == "handle_direct_challenge":
        contract_label = "direct_challenge"
    response_contract = response_trace.get("contract")
    fallback = bool(
        response_trace.get("fallback")
        or provider_notice.get("status") == "fallback"
        or trace_contract.get("provider_fallback")
    )

    contract = {
        "version": 1,
        "source_of_truth": contract_source,
        "resolved_mode": resolved_mode,
        "conversation_lane": conversation_lane,
        "execution_lane": governed_pipeline.get("active_lane"),
        "contract_label": contract_label,
        "reasoning_objective": reasoning_objective,
        "response_contract": response_contract,
        "authority_lane": trace_contract.get("authority_lane")
        or sovereignty_contract.get("authority_lane")
        or "jarvis",
        "routing_authority": trace_contract.get("routing_authority")
        or sovereignty_contract.get("routing_authority")
        or "jarvis",
        "state_authority": trace_contract.get("state_authority")
        or sovereignty_contract.get("state_authority")
        or "jarvis",
        "surface_identity": surface_identity,
        "surface_priority": trace_contract.get("surface_priority")
        or sovereignty_contract.get("surface_priority")
        or "authority_surface",
        "provider_fallback": fallback,
        "provider_dispatch": provider_dispatch,
        "current_turn_priority": priority_guard,
        "external_suggestion_admission": external_suggestion_admission,
        "output_completion": output_completion,
    }
    return {key: value for key, value in contract.items() if _has_canonical_trace_value(value)}


def _sync_canonical_trace_contract(session, response_trace=None):
    """Keep one canonical trace contract attached to the live turn trace and session state."""
    canonical = _build_canonical_trace_contract(session, response_trace=response_trace)
    session.metadata["canonical_trace_contract"] = dict(canonical)
    if isinstance(response_trace, dict):
        response_trace["canonical_contract"] = dict(canonical)
    elif isinstance(session.metadata.get("response_trace"), dict):
        session.metadata["response_trace"]["canonical_contract"] = dict(canonical)
    return canonical


def _begin_turn_trace(session):
    """Reset per-turn trace dedupe state before a new chat turn starts."""
    session.metadata["_active_turn_event_keys"] = set()
    _sanitize_session_response_trace(session)


def _mechanic_model_calls_this_turn(session) -> int:
    """Count provider model calls recorded for the active turn."""
    metadata = getattr(session, "metadata", None) or {}
    slingshot_calls = int(metadata.get("slingshot_model_calls") or 0)
    composed_calls = int(metadata.get("composed_turn_model_calls") or 0)
    provider_calls = int(metadata.get("provider_model_calls_this_turn") or 0)
    return max(slingshot_calls, composed_calls, provider_calls)


def _summarize_mechanic_session_state(session) -> dict[str, Any]:
    """Bounded mechanic enforcement state for operator UI payloads."""
    metadata = getattr(session, "metadata", None) or {}
    case_id = str(metadata.get("mechanic_case_id") or "").strip()
    last_block = metadata.get("mechanic_enforcement_last")
    payload: dict[str, Any] = {
        "case_id": case_id or None,
        "enforcement_enabled": bool(str(os.environ.get("MECHANIC_ENFORCE_PROFILE") or "").strip() in {"1", "true", "yes"}),
    }
    if isinstance(last_block, dict):
        payload["last_block"] = {
            "blocked": bool(last_block.get("blocked")),
            "code": last_block.get("code"),
            "message": last_block.get("message"),
        }
    return payload


def _summarize_slingshot_session_state(session) -> dict[str, Any] | None:
    """Bounded slingshot session state for operator UI payloads."""
    metadata = getattr(session, "metadata", None) or {}
    slingshot = metadata.get("slingshot")
    if not isinstance(slingshot, dict) or not slingshot:
        return None
    packet = dict(slingshot.get("packet") or {})
    return {
        "active": bool(slingshot.get("active")),
        "case_id": slingshot.get("case_id"),
        "status": slingshot.get("status"),
        "authorized_goals": list(slingshot.get("authorized_goals") or packet.get("authorized_goals") or []),
        "required_constraints": list(
            slingshot.get("required_constraints") or packet.get("required_constraints") or []
        ),
        "launch_blocked": bool(slingshot.get("launch_blocked")),
        "packet": {
            "expires_at_utc": packet.get("expires_at_utc"),
            "compose_mode": packet.get("compose_mode"),
        }
        if packet
        else None,
    }


def _bind_mechanic_case_from_payload(session, data: dict | None) -> None:
    """Apply optional mechanic case binding from a chat turn payload."""
    if not isinstance(data, dict):
        return
    if "mechanic_case_id" not in data:
        return
    case_id = str(data.get("mechanic_case_id") or "").strip()
    if case_id:
        session.metadata["mechanic_case_id"] = case_id
    else:
        session.metadata.pop("mechanic_case_id", None)


def _maybe_block_mechanic_enforcement(session, session_id: str):
    """MECH-CHAT-01 — optional runtime profile gate before chat actuation."""
    from mechanic.integration.chat_hook import enforce_chat_turn_request

    metadata = getattr(session, "metadata", None) or {}
    slingshot = metadata.get("slingshot") or {}
    if slingshot.get("active"):
        return None
    case_id = str(metadata.get("mechanic_case_id") or "").strip()
    block = enforce_chat_turn_request(
        action="propose",
        model_calls_this_turn=_mechanic_model_calls_this_turn(session),
        audit_fields={"trace_id": session_id, "case_id": case_id or session_id},
        case_id=case_id or None,
    )
    if block is not None:
        session.metadata["mechanic_enforcement_last"] = {
            "blocked": True,
            "code": (block.get("mechanic_enforcement") or block).get("code"),
            "message": block.get("error") or block.get("message"),
        }
    else:
        session.metadata["mechanic_enforcement_last"] = {"blocked": False}
    return block


def _admit_slingshot_turn(session, data: dict[str, Any], session_id: str):
    """Slingshot launch admission — pullback/tension validation before compose."""
    slingshot_payload = data.get("slingshot")
    if not isinstance(slingshot_payload, dict) or not slingshot_payload:
        return None
    from slingshot.launch import admit_slingshot_turn

    return admit_slingshot_turn(session, slingshot_payload, session_id=session_id)


def _finalize_slingshot_turn_impact(
    session,
    *,
    user_message: str,
    response_text: str,
    session_id: str,
) -> dict[str, Any] | None:
    """Impact catch-zone: midflight reply checks, receipt, optional signoff gate."""
    metadata = getattr(session, "metadata", None) or {}
    slingshot = metadata.get("slingshot") or {}
    if not slingshot.get("active"):
        return None

    from slingshot.impact import build_impact_receipt, persist_impact_receipt
    from slingshot.midflight import (
        apply_midflight_to_session,
        evaluate_slingshot_midflight_reply,
        merge_midflight_reports,
    )

    packet = dict(slingshot.get("packet") or {})
    case_id = str(slingshot.get("case_id") or packet.get("case_id") or "")
    reply_report = evaluate_slingshot_midflight_reply(
        user_message=user_message,
        assistant_reply=response_text or "",
        packet=packet,
    )
    cortex_report = dict(metadata.get("slingshot_midflight_cortex") or {})
    merged = merge_midflight_reports(cortex_report, reply_report)
    apply_midflight_to_session(session, merged)

    receipt = build_impact_receipt(
        case_id=case_id,
        turn_id=session_id,
        user_message=user_message,
        assistant_reply=response_text or "",
        midflight_report=merged,
        session_metadata=metadata,
        compose_mode_used=str(metadata.get("composed_turn_mode") or "fast"),
        cortex_fast_path=bool(metadata.get("cortex_fast_path")),
    )
    receipt_path = persist_impact_receipt(receipt)
    session.metadata["slingshot_last_receipt"] = {
        "path": str(receipt_path),
        "impact_status": receipt.get("impact_status"),
        "receipt_hash": receipt.get("receipt_hash"),
    }

    if merged.get("signoff_required"):
        _store_pending_action(
            session,
            {
                "id": f"slingshot_signoff_{case_id}",
                "type": "slingshot_signoff",
                "label": "Slingshot drift signoff required",
                "summary": "Stage 2 drift detected during slingshot launch; approve to continue.",
                "case_id": case_id,
                "impact_status": merged.get("impact_status"),
            },
        )

    if merged.get("halt_turn"):
        return {
            "error": "Slingshot turn halted due to Class III drift or cost ceiling breach.",
            "slingshot": {
                "blocked": True,
                "impact_status": merged.get("impact_status"),
                "drift_events": merged.get("drift_events"),
                "receipt_path": str(receipt_path),
                "claim_label": "proven",
            },
            "status_code": 403,
        }
    return None


def _session_event_key(event_type: str, summary: str, payload=None):
    """Build a stable per-turn dedupe key for one session event."""
    return (
        _normalize_trace_text(event_type).lower(),
        _normalize_trace_text(summary).lower(),
        _stable_trace_value(payload),
    )


def _dedupe_session_events(events):
    """Remove duplicate session events while preserving order."""
    deduped = []
    seen_keys = set()
    for event in list(events or []):
        key = _session_event_key(
            event.get("event_type"),
            event.get("summary"),
            event.get("payload"),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(event)
    return deduped


def _clip_trace_text(text, limit=500):
    """Return a compact single-line summary for UI traces."""
    normalized = _normalize_trace_text(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _has_canonical_trace_value(value) -> bool:
    """Return True when a canonical trace field should remain visible."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _memory_cue_display_text(cue, *, limit: int = 90) -> str:
    """Render one memory cue into the exact compact form used in prompt assembly."""
    if isinstance(cue, dict):
        raw_text = cue.get("text") or cue.get("content") or cue.get("insight") or cue.get("summary")
    else:
        raw_text = (
            getattr(cue, "text", None)
            or getattr(cue, "content", None)
            or getattr(cue, "insight", None)
            or getattr(cue, "summary", None)
            or cue
        )
    return _clip_trace_text(raw_text, limit=limit)


def _enforce_memory_cue_uniqueness(messages, cues, *, allow_duplicates: bool = False):
    """Ensure each current-turn memory cue appears at most once across system context blocks."""
    normalized_cues = [
        (rendered, rendered.lower())
        for rendered in (
            _memory_cue_display_text(cue, limit=90)
            for cue in dedupe_memory_cues(cues)
        )
        if rendered
    ]
    if not normalized_cues or allow_duplicates:
        return [dict(message) for message in list(messages or [])]

    seen_cues: set[str] = set()
    cleaned_messages = []
    for message in list(messages or []):
        next_message = dict(message)
        if next_message.get("role") != "system":
            cleaned_messages.append(next_message)
            continue

        content = str(next_message.get("content") or "")
        if not content:
            cleaned_messages.append(next_message)
            continue

        for rendered, normalized in normalized_cues:
            if normalized not in content.lower():
                continue
            if normalized in seen_cues:
                content = re.sub(re.escape(rendered), "", content, flags=re.IGNORECASE)
                continue

            seen_cues.add(normalized)
            first_index = content.lower().find(normalized)
            if first_index >= 0:
                first_end = first_index + len(rendered)
                prefix = content[:first_end]
                suffix = content[first_end:]
                suffix = re.sub(re.escape(rendered), "", suffix, flags=re.IGNORECASE)
                content = prefix + suffix

        content = re.sub(r"[ \t]{2,}", " ", content)
        content = re.sub(r"\n{3,}", "\n\n", content).strip()
        next_message["content"] = content
        cleaned_messages.append(next_message)

    return [message for message in cleaned_messages if str(message.get("content") or "").strip()]


def _record_memory_cue_trace(session, messages):
    """Capture retrieved/unique/rendered cue counts for this assembled prompt."""
    unique_cues = dedupe_memory_cues(session.metadata.get("persistent_memories") or [])
    rendered_count = 0
    system_contents = [
        " ".join(str(message.get("content") or "").split()).strip().lower()
        for message in list(messages or [])
        if message.get("role") == "system" and str(message.get("content") or "").strip()
    ]

    for cue in unique_cues:
        rendered = _memory_cue_display_text(cue, limit=90).lower()
        if not rendered:
            continue
        rendered_count += sum(content.count(rendered) for content in system_contents)

    trace = dict(session.metadata.get("memory_cue_trace") or {})
    trace["retrieved"] = int(trace.get("retrieved") or len(unique_cues))
    trace["unique"] = len(unique_cues)
    trace["rendered"] = rendered_count
    trace["duplicates_allowed"] = normalize_response_mode(session.metadata.get("response_mode")) == "debug"
    trace["duplicates_blocked"] = rendered_count <= len(unique_cues)
    session.metadata["memory_cue_trace"] = trace

    response_trace = session.metadata.get("response_trace")
    if isinstance(response_trace, dict):
        response_trace["memory_cues"] = dict(trace)

    logger.info(
        "Memory cue trace | retrieved=%s unique=%s rendered=%s",
        trace["retrieved"],
        trace["unique"],
        trace["rendered"],
    )
    return trace


def _resolve_prompt_token_budget(session, *, max_length=None, model=None):
    """Reserve output first, then compute the safe prompt budget for this turn."""
    response_mode = normalize_response_mode(session.metadata.get("response_mode"))
    requested_response_budget = max(
        32,
        int(max_length or RESPONSE_MODE_DEFAULTS[response_mode]["max_tokens"]),
    )
    reply_budget_floor = max(
        32,
        min(requested_response_budget, RESPONSE_MODE_DEFAULTS[response_mode]["max_tokens"]),
    )
    reserved_response_budget = max(reply_budget_floor, requested_response_budget)
    routing_profile = session.metadata.get("model_route") or {}
    provider_id = normalize_provider_identifier(routing_profile.get("provider"), default="local")
    provider_config = provider_registry.get_config(provider_id)
    provider_kind = str((provider_config.meta or {}).get("kind") or "").strip().lower() if provider_config else ""
    if provider_id in PROVIDER_PROMPT_MARGIN_BY_ID:
        provider_margin_tokens = PROVIDER_PROMPT_MARGIN_BY_ID[provider_id]
        provider_budget_policy = PROVIDER_PROMPT_MARGIN_POLICY_LABELS.get(
            provider_kind or provider_id,
            PROVIDER_PROMPT_MARGIN_POLICY_LABELS.get(provider_id, "unknown_conservative_margin"),
        )
    else:
        normalized_kind = provider_kind if provider_kind in PROVIDER_PROMPT_MARGIN_BY_KIND else "unknown"
        provider_margin_tokens = PROVIDER_PROMPT_MARGIN_BY_KIND[normalized_kind]
        provider_budget_policy = PROVIDER_PROMPT_MARGIN_POLICY_LABELS[normalized_kind]
    effective_reserved_budget = reserved_response_budget + provider_margin_tokens
    route_overrides = ((session.metadata.get("model_route") or {}).get("generation_overrides") or {})
    fallback_limit = max(
        DEFAULT_CHAT_CONTEXT_LIMIT,
        int(route_overrides.get("input_max_length") or 0),
    )
    active_model = model or ai_model
    tokenizer = getattr(active_model, "text_tokenizer", None) if active_model else None
    if tokenizer is not None and provider_id == "local":
        prompt_token_budget = resolve_input_token_limit(
            tokenizer,
            effective_reserved_budget,
            fallback_limit=fallback_limit,
        )
    else:
        prompt_token_budget = max(256, fallback_limit - effective_reserved_budget)
    budget_policy = {
        "resolved_provider": provider_id,
        "provider_kind": provider_kind or ("local" if provider_id == "local" else "unknown"),
        "provider_budget_policy": provider_budget_policy,
        "provider_margin_tokens": int(provider_margin_tokens),
        "reply_budget_floor": int(reply_budget_floor),
        "reserved_response_budget": int(reserved_response_budget),
        "effective_reserved_budget": int(effective_reserved_budget),
        "prompt_token_budget": int(prompt_token_budget),
    }
    session.metadata["prompt_budget_policy"] = dict(budget_policy)
    return prompt_token_budget, reserved_response_budget, budget_policy


def _record_prompt_assembly_trace(session, response_trace, prompt_trace):
    """Persist prompt assembly cleanup metrics onto the live session trace."""
    if not isinstance(prompt_trace, dict):
        return None
    budget_policy = dict(session.metadata.get("prompt_budget_policy") or {})
    cleaned = {
        "raw_chars": int(prompt_trace.get("raw_chars") or 0),
        "raw_tokens_estimate": int(prompt_trace.get("raw_tokens_estimate") or 0),
        "chars_after_cleanup": int(prompt_trace.get("chars_after_cleanup") or 0),
        "tokens_after_cleanup_estimate": int(prompt_trace.get("tokens_after_cleanup_estimate") or 0),
        "duplicates_removed": int(prompt_trace.get("duplicates_removed") or 0),
        "malformed_fragments_removed": int(prompt_trace.get("malformed_fragments_removed") or 0),
        "budget_dropped": int(prompt_trace.get("budget_dropped") or 0),
        "assistant_echoes_scrubbed": int(prompt_trace.get("assistant_echoes_scrubbed") or 0),
        "reserved_response_budget": int(prompt_trace.get("reserved_response_budget") or 0),
        "prompt_token_budget": int(
            prompt_trace.get("prompt_token_budget")
            or budget_policy.get("prompt_token_budget")
            or 0
        ),
        "resolved_provider": str(budget_policy.get("resolved_provider") or ""),
        "provider_kind": str(budget_policy.get("provider_kind") or ""),
        "provider_budget_policy": str(budget_policy.get("provider_budget_policy") or ""),
        "provider_margin_tokens": int(budget_policy.get("provider_margin_tokens") or 0),
        "reply_budget_floor": int(budget_policy.get("reply_budget_floor") or 0),
        "effective_reserved_budget": int(budget_policy.get("effective_reserved_budget") or 0),
        "chars_by_identity": dict(prompt_trace.get("chars_by_identity") or {}),
        "identity_counts": dict(prompt_trace.get("identity_counts") or {}),
        "included_block_identities": list(prompt_trace.get("included_block_identities") or []),
    }
    session.metadata["prompt_assembly_trace"] = cleaned
    if isinstance(response_trace, dict):
        response_trace["prompt_assembly"] = dict(cleaned)
        duplicates_removed = cleaned["duplicates_removed"]
        malformed_removed = cleaned["malformed_fragments_removed"]
        budget_dropped = cleaned["budget_dropped"]
        echoes_scrubbed = cleaned["assistant_echoes_scrubbed"]
        margin_tokens = cleaned["provider_margin_tokens"]
        budget_policy_name = cleaned["provider_budget_policy"] or "unlabeled_budget_policy"
        _append_response_trace_step(
            response_trace,
            (
                "Prompt assembly kept one canonical copy per instruction family "
                f"and removed duplicates={duplicates_removed}, malformed={malformed_removed}, "
                f"assistant_echoes={echoes_scrubbed}, budget_dropped={budget_dropped}, "
                f"provider_margin={margin_tokens} ({budget_policy_name})."
            ),
        )
    return cleaned


def _record_provider_dispatch_trace(session, response_trace, dispatch_trace, *, emit_step=True):
    """Persist provider dispatch budgeting details onto the live response trace."""
    if not isinstance(dispatch_trace, dict):
        return None
    cleaned = {
        "resolved_provider": str(dispatch_trace.get("resolved_provider") or ""),
        "provider_model": str(dispatch_trace.get("provider_model") or "") or None,
        "prompt_tokens_estimate": int(dispatch_trace.get("prompt_tokens_estimate") or 0),
        "prompt_tokens_estimator": str(dispatch_trace.get("prompt_tokens_estimator") or "unknown"),
        "prompt_tokens_exact": bool(dispatch_trace.get("prompt_tokens_exact")),
        "message_count": int(dispatch_trace.get("message_count") or 0),
        "prompt_token_budget": int(dispatch_trace.get("prompt_token_budget") or 0),
        "prompt_overflow_tokens": int(dispatch_trace.get("prompt_overflow_tokens") or 0),
        "requested_output_token_budget": int(dispatch_trace.get("requested_output_token_budget") or 0),
        "effective_output_token_budget": int(dispatch_trace.get("effective_output_token_budget") or 0),
        "reply_budget_floor": int(dispatch_trace.get("reply_budget_floor") or 0),
        "reply_floor_preserved": bool(dispatch_trace.get("reply_floor_preserved")),
        "output_budget_clamped": bool(dispatch_trace.get("output_budget_clamped")),
        "provider_reported_prompt_tokens": (
            int(dispatch_trace.get("provider_reported_prompt_tokens"))
            if dispatch_trace.get("provider_reported_prompt_tokens") is not None
            else None
        ),
        "provider_reported_output_tokens": (
            int(dispatch_trace.get("provider_reported_output_tokens"))
            if dispatch_trace.get("provider_reported_output_tokens") is not None
            else None
        ),
        "prompt_estimate_delta": (
            int(dispatch_trace.get("prompt_estimate_delta"))
            if dispatch_trace.get("prompt_estimate_delta") is not None
            else None
        ),
    }
    session.metadata["provider_dispatch_trace"] = dict(cleaned)
    if isinstance(response_trace, dict):
        response_trace["provider_dispatch"] = dict(cleaned)
        if emit_step and cleaned["output_budget_clamped"]:
            _append_response_trace_step(
                response_trace,
                (
                    "Remote provider dispatch reduced the output budget after estimating the "
                    f"provider prompt shape: prompt_estimate={cleaned['prompt_tokens_estimate']}, "
                    f"budget={cleaned['prompt_token_budget']}, "
                    f"output={cleaned['effective_output_token_budget']}."
                ),
            )
    return cleaned


def _merge_provider_usage_into_dispatch_trace(session, response_trace, provider_response):
    """Attach provider-reported token usage onto the latest dispatch trace."""
    current = dict(session.metadata.get("provider_dispatch_trace") or {})
    if not current or provider_response is None:
        return current or None
    input_tokens = getattr(provider_response, "input_tokens", None)
    output_tokens = getattr(provider_response, "output_tokens", None)
    if input_tokens is not None:
        current["provider_reported_prompt_tokens"] = int(input_tokens)
        current["prompt_estimate_delta"] = int(input_tokens) - int(
            current.get("prompt_tokens_estimate") or 0
        )
    if output_tokens is not None:
        current["provider_reported_output_tokens"] = int(output_tokens)
    return _record_provider_dispatch_trace(session, response_trace, current, emit_step=False)


def _effective_provider_output_budget(session, fallback):
    """Return the last remote dispatch budget if the turn computed one."""
    trace = dict(session.metadata.get("provider_dispatch_trace") or {})
    return int(trace.get("effective_output_token_budget") or fallback or 0)


def _generation_metadata_from_provider_response(provider_response, *, output_token_budget=None):
    """Normalize provider metadata for output completion enforcement."""
    if provider_response is None:
        return {"output_token_budget": int(output_token_budget or 0)}
    return {
        "stop_reason": getattr(provider_response, "stop_reason", None),
        "finish_reason": getattr(provider_response, "finish_reason", None),
        "input_tokens": getattr(provider_response, "input_tokens", None),
        "output_tokens": getattr(provider_response, "output_tokens", None),
        "output_token_budget": int(output_token_budget or 0),
    }


def _generation_metadata_from_model(model, *, output_token_budget=None):
    """Read the latest local-model generation metadata in one stable shape."""
    metadata = dict(getattr(model, "last_generation_metadata", {}) or {})
    metadata["output_token_budget"] = int(
        metadata.get("output_token_budget") or output_token_budget or 0
    )
    return metadata


def _capture_stream_generation_metadata(current, chunk):
    """Fold final-chunk stream metadata into one completion report payload."""
    merged = dict(current or {})
    if not isinstance(chunk, dict):
        return merged
    for key in ("stop_reason", "finish_reason", "input_tokens", "output_tokens", "output_tokens_used", "output_token_budget"):
        value = chunk.get(key)
        if value is None:
            continue
        normalized_key = "output_tokens" if key == "output_tokens_used" else key
        merged[normalized_key] = value
    return merged


def _record_output_completion_trace(response_trace, completion_trace):
    """Attach completion integrity diagnostics to the visible trace."""
    if not isinstance(response_trace, dict) or not isinstance(completion_trace, dict):
        return None
    response_trace["output_completion"] = dict(completion_trace)
    if completion_trace.get("completion_guard_applied"):
        summary = (
            "Output completion guard repaired a clipped reply before display and marked truncation visibly."
        )
        if completion_trace.get("repetition_detected"):
            summary = (
                "Output completion guard cut a repetition loop before display and marked the repair visibly."
            )
        _append_response_trace_step(
            response_trace,
            summary,
        )
    elif completion_trace.get("truncation_detected"):
        _append_response_trace_step(
            response_trace,
            "Generation hit the output budget, but the visible reply still ended in a structurally complete form.",
        )
    return completion_trace


def _observe_continuity_witness(session, response_trace):
    """Record one observation-only temporal drift snapshot for the completed turn."""
    if not isinstance(response_trace, dict):
        return None
    governed_pipeline = response_trace.get("governed_pipeline")
    if not isinstance(governed_pipeline, dict) or not governed_pipeline:
        return None
    observation = continuity_witness_store.observe(
        governed_pipeline=governed_pipeline,
        response_trace=response_trace,
        provider_notice=session.metadata.get("provider_notice"),
    )
    session.metadata["continuity_witness"] = dict(observation)
    response_trace["continuity_witness"] = dict(observation)
    governed_pipeline["continuity_witness"] = dict(observation)
    history = list(session.metadata.get("governed_pipeline_history") or [])
    pipeline_id = str(governed_pipeline.get("pipeline_id") or "").strip()
    if pipeline_id and not any(
        str(entry.get("pipeline_id") or "") == pipeline_id for entry in history
    ):
        history.append(dict(governed_pipeline))
        session.metadata["governed_pipeline_history"] = history[-20:]
    if observation.get("trajectory_status") != "STABLE":
        _append_response_trace_step(
            response_trace,
            (
                "Continuity Witness marked "
                f"{str(observation.get('subsystem') or 'the subsystem').lower()} as "
                f"{str(observation.get('trajectory_status') or 'stable').lower()} "
                "based on temporal drift."
            ),
        )
    return observation


def _strip_visible_scaffold_output(response_text: str, *, direct_challenge: bool = False):
    """Remove internal scaffold headers from visible replies or fail closed if only scaffold remains."""
    normalized = str(response_text or "").strip()
    if not normalized:
        return normalized, None

    lines = normalized.splitlines()
    top_window = [line.strip() for line in lines[:6] if line.strip()]
    scaffold_line_count = sum(
        1
        for line in top_window
        if VISIBLE_SCAFFOLD_HEADER_RE.match(line) or VISIBLE_SCAFFOLD_SECTION_RE.match(line)
    )
    inline_marker_count = sum(
        1
        for marker in (
            "mode:",
            "focus:",
            "specialists:",
            "god brain:",
            "model route:",
            "evidence:",
            "answer shape:",
            "jarvis internal guidance for this turn",
        )
        if marker in normalized.lower()
    )
    scaffold_detected = scaffold_line_count >= 2 or inline_marker_count >= 2
    if not scaffold_detected:
        return normalized, None

    trimmed_index = 0
    while trimmed_index < len(lines):
        candidate = lines[trimmed_index].strip()
        if not candidate:
            trimmed_index += 1
            continue
        if VISIBLE_SCAFFOLD_HEADER_RE.match(candidate) or VISIBLE_SCAFFOLD_SECTION_RE.match(candidate):
            trimmed_index += 1
            continue
        break

    cleaned = "\n".join(lines[trimmed_index:]).strip()
    fallback_used = False
    if not cleaned:
        cleaned = (
            LOCAL_FALLBACK_DIRECT_CHALLENGE_RESPONSE
            if direct_challenge
            else LOCAL_FALLBACK_GENERAL_RESPONSE
        )
        fallback_used = True

    return cleaned, {
        "applied": True,
        "fallback_used": fallback_used,
        "stripped_line_count": max(0, trimmed_index),
        "scaffold_line_count": scaffold_line_count,
        "inline_marker_count": inline_marker_count,
    }


def _record_visible_scaffold_cleanup(response_trace, cleanup_report):
    """Attach visible scaffold cleanup diagnostics to the response trace."""
    if not isinstance(cleanup_report, dict):
        return None
    if isinstance(response_trace, dict):
        response_trace["visible_scaffold_cleanup"] = dict(cleanup_report)
        _append_response_trace_step(
            response_trace,
            "Visible scaffold cleanup removed internal response headers before display.",
        )
    return cleanup_report


def _sanitize_operator_surface_text(
    text: str,
    *,
    direct_challenge: bool = False,
    fallback_text: str | None = None,
) -> str:
    """Return operator-safe text for non-chat surfaces that may still surface scaffold leakage."""
    cleaned, _cleanup = _strip_visible_scaffold_output(
        text,
        direct_challenge=direct_challenge,
    )
    if _cleanup and _cleanup.get("fallback_used") and fallback_text is not None:
        return str(fallback_text or "").strip()
    return cleaned


def _build_otem_boundary_snapshot(
    *,
    user_message: str,
    otem_payload: dict | None,
    raw_response_text: str,
    final_response_text: str | None = None,
    completion_trace: dict | None = None,
):
    """Summarize the OTEM ingress/egress seam without exposing hidden scaffolding."""
    otem_payload = dict(otem_payload or {})
    completion_trace = dict(completion_trace or {})
    task_clauses = [
        " ".join(str(clause or "").split()).strip()
        for clause in list(otem_payload.get("task_clauses") or [])
        if " ".join(str(clause or "").split()).strip()
    ]
    signal_clauses = [
        " ".join(str(clause or "").split()).strip()
        for clause in list(otem_payload.get("signal_clauses") or [])
        if " ".join(str(clause or "").split()).strip()
    ]
    ingress_text = " ".join(str(user_message or "").split()).strip()
    task_text = " ".join(str(otem_payload.get("task") or "").split()).strip()
    restated_task = " ".join(str(otem_payload.get("restated_task") or "").split()).strip()
    response_before = " ".join(str(raw_response_text or "").split()).strip()
    response_after = " ".join(str(final_response_text or raw_response_text or "").split()).strip()
    structural_completion_status = (
        str(completion_trace.get("structural_completion_status") or "").strip()
        or "not_checked"
    )
    incomplete_egress_detected = structural_completion_status in {
        "trimmed_to_boundary",
        "tail_trimmed_with_notice",
        "visible_truncation_notice",
        "repetition_loop_trimmed",
    }
    return {
        "ingress_chars": len(ingress_text),
        "task_chars": len(task_text),
        "restated_task_chars": len(restated_task),
        "task_clause_count": len(task_clauses),
        "signal_clause_count": len(signal_clauses),
        "plan_step_count": len(list(otem_payload.get("plan") or [])),
        "response_chars_before_finalization": len(response_before),
        "response_chars_after_finalization": len(response_after),
        "response_changed_at_egress": response_before != response_after,
        "incomplete_egress_detected": incomplete_egress_detected,
        "completion_guard_applied": bool(completion_trace.get("completion_guard_applied")),
        "truncation_detected": bool(completion_trace.get("truncation_detected")),
        "repetition_detected": bool(completion_trace.get("repetition_detected")),
        "structural_completion_status": structural_completion_status,
    }


def _record_otem_boundary_trace(
    session,
    response_trace,
    *,
    user_message: str,
    otem_payload: dict | None,
    raw_response_text: str,
    final_response_text: str | None = None,
    completion_trace: dict | None = None,
):
    """Attach OTEM ingress/egress diagnostics to the visible response trace."""
    snapshot = _build_otem_boundary_snapshot(
        user_message=user_message,
        otem_payload=otem_payload,
        raw_response_text=raw_response_text,
        final_response_text=final_response_text,
        completion_trace=completion_trace,
    )
    if hasattr(session, "metadata"):
        session.metadata["otem_boundary_trace"] = dict(snapshot)
    if isinstance(response_trace, dict):
        response_trace["otem_boundary"] = dict(snapshot)
        if snapshot["completion_guard_applied"]:
            _append_response_trace_step(
                response_trace,
                (
                    "OTEM boundary repaired the visible response before display "
                    f"({snapshot['structural_completion_status']})."
                ),
            )
        else:
            _append_response_trace_step(
                response_trace,
                (
                    "OTEM boundary captured "
                    f"{snapshot['task_clause_count']} task clause(s) and "
                    f"{snapshot['signal_clause_count']} signal clause(s) before display."
                ),
            )
    return snapshot


def _sync_otem_visible_answer(
    finalized_text: str,
    *,
    otem_payload: dict | None = None,
    turn_contract: dict | None = None,
    session=None,
):
    """Keep the finalized OTEM answer canonical across the next state gates."""
    visible_answer = str(finalized_text or "")
    if isinstance(otem_payload, dict):
        otem_payload["answer"] = visible_answer
    if isinstance(turn_contract, dict):
        contract_otem = turn_contract.get("otem")
        if isinstance(contract_otem, dict):
            contract_otem["answer"] = visible_answer
    if hasattr(session, "metadata"):
        stored_otem = session.metadata.get("otem_state")
        if isinstance(stored_otem, dict):
            stored_otem["answer"] = visible_answer
            session.metadata["otem_state"] = stored_otem
    return visible_answer


def _finalize_visible_response(
    session,
    user_message: str,
    response_text: str,
    *,
    response_trace=None,
    generation_metadata=None,
):
    """Apply identity safety first, then enforce output completion integrity."""
    direct_challenge = _direct_challenge_turn_active(
        session,
        response_trace=response_trace,
        user_message=user_message,
    )
    scaffold_safe_text, scaffold_cleanup = _strip_visible_scaffold_output(
        response_text,
        direct_challenge=direct_challenge,
    )
    _record_visible_scaffold_cleanup(response_trace, scaffold_cleanup)
    identity_safe_text = _enforce_identity_safe_response(
        session,
        user_message,
        scaffold_safe_text,
        response_trace=response_trace,
    )
    metadata = dict(generation_metadata or {})
    finalized_text, completion_report = guard_output_completion(
        identity_safe_text,
        stop_reason=metadata.get("stop_reason"),
        finish_reason=metadata.get("finish_reason"),
        output_token_budget=metadata.get("output_token_budget"),
        output_tokens_used=metadata.get("output_tokens"),
    )
    completion_trace = completion_report.to_dict()
    session.metadata["output_completion_trace"] = completion_trace
    _record_output_completion_trace(response_trace, completion_trace)
    if _local_fallback_active(session, response_trace=response_trace):
        return finalized_text
    if session.metadata.get("cognitive_runtime_enabled"):
        cognitive_text = apply_nova_cognitive_finalization(
            session,
            user_message,
            finalized_text,
            response_trace=response_trace,
        )
        if session.metadata.get("nova_cognitive_summary"):
            persona_mode = str(session.metadata.get("persona_mode") or "").strip().lower()
            if persona_mode in {"tiny_nova", "small_nova"}:
                return finalized_text
            return cognitive_text
    return apply_speaking_runtime_finalization(
        session,
        user_message,
        finalized_text,
        response_trace=response_trace,
    )


def _attach_pipeline_transport_substrate(session, response_mode: str) -> None:
    """Consult governed pipeline transport before composed-turn parallel routing."""
    transport_contract = RESPONSE_MODE_CONTRACTS.get(
        normalize_response_mode(response_mode), {}
    ).get("contract")
    session.metadata["pipeline_transport"] = consult_pipeline_transport_substrate(
        response_mode=response_mode,
        contract=transport_contract,
        runtime_context="live_runtime",
    )


def _configure_speaking_runtime_turn(
    session,
    request_payload,
    user_message: str,
    *,
    companion_turn: bool = False,
):
    """Enable Speaking Runtime for this turn when requested or triggered."""
    direct_challenge = looks_like_direct_challenge(user_message)
    resolve_speaking_runtime_enabled(
        session,
        request_payload,
        user_message,
        companion_turn=companion_turn,
        direct_challenge=direct_challenge,
        local_fallback=False,
    )


def _attach_cortex_memory_board_cues(session) -> None:
    """Attach unified memory governance membrane cues for Nova Cortex."""
    from src.memory_governance_membrane import attach_turn_memory_membrane

    attach_turn_memory_membrane(session, jarvis_operator=jarvis_operator)


def _configure_cognitive_runtime_turn(
    session,
    request_payload,
    user_message: str,
    *,
    companion_turn: bool = False,
    super_nova_turn: bool = False,
):
    """Configure Spine, ARIS, and Nova Cortex for every Jarvis chat turn."""
    surface_profile = _get_companion_surface_profile(
        persona_mode=(session.metadata or {}).get("persona_mode"),
        response_mode=(session.metadata or {}).get("response_mode")
        or (session.metadata or {}).get("requested_response_mode"),
    )
    payload, compose_mode = resolve_composed_turn_payload(
        session,
        request_payload,
        companion_turn=companion_turn,
        super_nova_turn=super_nova_turn,
        user_message=user_message,
    )
    session.metadata["composed_turn_mode"] = compose_mode
    session.metadata["cortex_fast_path"] = bool(payload.get("cortex_fast_path"))
    from src.cog_runtime.formal.turn_agency import capture_turn_boundary

    session.metadata["turn_boundary_before"] = capture_turn_boundary(session.metadata)
    _attach_cortex_memory_board_cues(session)
    run_composed_turn(
        session,
        user_message,
        request_payload=payload,
        companion_turn=companion_turn,
        surface_profile=surface_profile,
        compose_mode=compose_mode,
        emit_speaking=bool(
            companion_turn
            or (payload.get("operator_speaking_wrap") and payload.get("speaking_runtime"))
        ),
        include_speaking_update=bool(
            companion_turn or payload.get("operator_speaking_wrap")
        ),
    )


def _composed_turn_block_payload(session):
    """Return a chat error payload when ARIS blocked a composed companion turn."""
    composed = (session.metadata or {}).get("aais_composed_turn")
    if not isinstance(composed, dict) or composed.get("status") != "blocked":
        return None
    reason_codes = set(composed.get("reason_codes") or [])
    if "agency_violation" in reason_codes:
        violation = dict((session.metadata or {}).get("agency_violation") or {})
        summary = violation.get("error") or "Agency preservation blocked this composed turn."
    else:
        aris = composed.get("aris") or {}
        summary = (aris.get("non_copy_clause") or {}).get("summary") or (
            "Composed runtime blocked this turn before Nova Cortex completed."
        )
    return {
        "error": summary,
        "aais_composed_turn": composed,
    }


def _god_brain_bridge_kwargs(session) -> dict:
    """Pass Nova Face → Cortex → Tri-Core binding into God Brain traces."""
    metadata = session.metadata or {}
    binding = dict(metadata.get("tri_core_binding") or metadata.get("jarvis_core_binding") or {})
    face = dict((session.metadata or {}).get("nova_face") or {})
    kwargs: dict = {}
    runtimes = binding.get("active_cognitive_runtimes")
    if runtimes:
        kwargs["active_cognitive_runtimes"] = list(runtimes)
    if face:
        kwargs["nova_face"] = face
    if binding:
        kwargs["tri_core_binding"] = binding
    return kwargs


def _set_turn_contract(
    session,
    *,
    requested_mode: str | None = None,
    resolved_mode: str | None = None,
    resolved_scope: str | None = None,
    resolved_voice: str | None = None,
    memory_rejection=None,
    otem=None,
    provider_fallback: bool | None = None,
    contract_label: str | None = None,
):
    """Persist one authoritative turn contract for the active turn."""
    current = dict(session.metadata.get("turn_contract") or {})
    current.setdefault("otem_enabled", False)
    current.setdefault("otem_task", None)
    current.setdefault("otem_scope", None)
    current.setdefault("otem_plan", [])
    current.setdefault("otem_status", None)
    current.setdefault("otem_rejection_reason", None)
    current.setdefault("otem_allowed_alternative", None)
    if requested_mode is not None:
        current["requested_mode"] = normalize_response_mode(requested_mode)
    if resolved_mode is not None:
        current["resolved_mode"] = normalize_response_mode(resolved_mode)
    if resolved_scope is not None:
        current["resolved_scope"] = str(resolved_scope or "operator_task")
    if resolved_voice is not None:
        current["resolved_voice"] = str(resolved_voice or "jarvis")
    if contract_label is not None:
        current["contract_label"] = str(contract_label or "").strip() or None
    if provider_fallback is not None:
        current["provider_fallback"] = bool(provider_fallback)
    if memory_rejection is not None:
        current["memory_rejection"] = dict(memory_rejection or {})
    if otem is not None:
        otem_payload = dict(otem or {})
        current["otem"] = otem_payload
        current["otem_enabled"] = bool(otem_payload)
        current["otem_task"] = " ".join(str(otem_payload.get("restated_task") or otem_payload.get("task") or "").split()).strip() or None
        current["otem_scope"] = str(otem_payload.get("scope") or "session").strip() or "session"
        current["otem_plan"] = [dict(step or {}) for step in list(otem_payload.get("plan") or [])]
        status = str(otem_payload.get("status") or "").strip().lower()
        current["otem_status"] = status if status in {"active", "rejected", "complete"} else "complete"
        current["otem_rejection_reason"] = (
            str(otem_payload.get("rejection_reason") or "").strip() or None
        )
        current["otem_allowed_alternative"] = (
            " ".join(str(otem_payload.get("allowed_alternative") or "").split()).strip() or None
        )
    current.update(
        _build_surface_authority_profile(
            resolved_mode=current.get("resolved_mode"),
            resolved_voice=current.get("resolved_voice"),
        )
    )
    current["updated_at"] = datetime.now(UTC).isoformat()
    session.metadata["turn_contract"] = current
    _refresh_sovereignty_contract(session)
    return current


def _snapshot_completed_turn_contract(session):
    """Mirror the finalized turn contract into the completed-turn snapshot without clearing it."""
    current = session.metadata.get("turn_contract")
    if isinstance(current, dict) and current:
        session.metadata["last_turn_contract"] = dict(current)
    return session.metadata.get("last_turn_contract")


def _build_surface_authority_profile(*, resolved_mode: str | None = None, resolved_voice: str | None = None):
    """Describe which lane owns the visible surface versus the authority core."""
    normalized_mode = normalize_response_mode(resolved_mode)
    companion_profile = _get_companion_surface_profile(
        persona_mode=resolved_voice,
        response_mode=normalized_mode,
    )
    surface_identity = " ".join(str(resolved_voice or "").split()).strip() or (
        companion_profile["identity"] if companion_profile else "jarvis"
    )
    surface_priority = "delegated_surface" if surface_identity != "jarvis" else "authority_surface"
    visible_profile = COMPANION_SURFACE_PROFILES.get(surface_identity)
    authority_summary = (
        f"{visible_profile['label']} may lead the companion surface, but Jarvis retains routing, state, and safety authority."
        if visible_profile
        else "Jarvis remains both the visible surface and the authority core for this turn."
    )
    return {
        "authority_lane": "jarvis",
        "routing_authority": "jarvis",
        "state_authority": "jarvis",
        "surface_identity": surface_identity,
        "surface_priority": surface_priority,
        "surface_replaces_authority": False,
        "authority_model": "layered_role_specialized",
        "system_shape": "organismic",
        "authority_summary": authority_summary,
    }


def _clear_turn_contract(session):
    """Move the active turn contract into last_turn_contract before clearing it."""
    current = session.metadata.get("turn_contract")
    if isinstance(current, dict) and current:
        session.metadata["last_turn_contract"] = dict(current)
    session.metadata["turn_contract"] = None


def _build_sovereignty_contract(session):
    """Build the single operator authority contract for the active turn."""

    turn_contract = dict(session.metadata.get("turn_contract") or {})
    mode_guidance = dict(session.metadata.get("mode_guidance") or {})
    provider_notice = dict(session.metadata.get("provider_notice") or {})
    authority_preferences = normalize_authority_preferences(session.metadata.get("authority_preferences"))
    surfaced_source = authority_surface_priority(authority_preferences)
    resolved_mode = normalize_response_mode(
        turn_contract.get("resolved_mode") or mode_guidance.get("effective_mode")
    )
    resolved_scope = str(
        turn_contract.get("resolved_scope") or mode_guidance.get("resolved_scope") or "operator_task"
    ).strip() or "operator_task"
    resolved_voice = str(
        turn_contract.get("resolved_voice") or mode_guidance.get("resolved_voice") or "jarvis"
    ).strip() or "jarvis"
    contract_label = str(turn_contract.get("contract_label") or "mode_guidance").strip() or "mode_guidance"
    surface_authority = _build_surface_authority_profile(
        resolved_mode=resolved_mode,
        resolved_voice=turn_contract.get("surface_identity") or resolved_voice,
    )
    return {
        "authority": "operator",
        "state_writer": "jarvis_sovereign_core",
        "source_of_truth": "turn_contract",
        "resolved_mode": resolved_mode,
        "resolved_scope": resolved_scope,
        "resolved_voice": resolved_voice,
        "contract_label": contract_label,
        **surface_authority,
        "visibility_before_action": True,
        "fallback_subordinate": bool(
            provider_notice.get("status") == "fallback" or turn_contract.get("provider_fallback")
        ),
        "proposal_only": bool(
            contract_label == "otem"
            or turn_contract.get("memory_rejection")
        ),
        "execution_requires_operator_gate": True,
        "authority_surface_priority": surfaced_source,
        "surface_priority_non_authoritative": True,
        "surface_priority_scope": "operator_visibility_only",
        "surface_priority_cannot_override": [
            "resolved_mode",
            "resolved_scope",
            "resolved_voice",
            "contract_label",
            "source_of_truth",
        ],
        "protected_state_domains": list(SOVEREIGN_PROTECTED_STATE_MAP.keys()),
        "soft_domains": list(IDENTITY_CONTINUITY_SOFT_DOMAIN_MAP.keys()),
        "updated_at": datetime.now(UTC).isoformat(),
    }


def _refresh_sovereignty_contract(session):
    """Refresh the active sovereignty contract from the current turn state."""

    contract = _build_sovereignty_contract(session)
    session.metadata["sovereignty_contract"] = contract
    return contract


def _get_mode_freeze(session):
    """Return the current mode freeze when it is still active."""
    freeze = session.metadata.get("mode_freeze")
    if not isinstance(freeze, dict):
        return None
    remaining_turns = int(freeze.get("remaining_turns") or 0)
    if remaining_turns <= 0:
        session.metadata["mode_freeze"] = None
        return None
    frozen_mode = normalize_response_mode(freeze.get("mode"))
    freeze["mode"] = frozen_mode
    freeze["remaining_turns"] = remaining_turns
    session.metadata["mode_freeze"] = freeze
    return freeze


def _consume_mode_freeze(session):
    """Consume one frozen-mode turn after a user-facing reply is emitted."""
    freeze = _get_mode_freeze(session)
    if not freeze:
        return None
    remaining_turns = max(0, int(freeze.get("remaining_turns") or 0) - 1)
    if remaining_turns <= 0:
        session.metadata["mode_freeze"] = None
        return None
    freeze["remaining_turns"] = remaining_turns
    session.metadata["mode_freeze"] = freeze
    return freeze


def _clear_turn_context(session):
    """Reset per-turn attached context before handling the next request."""
    _clear_turn_contract(session)
    session.metadata["prompt_lane"] = None
    session.metadata["context_priority_guard"] = None
    session.metadata["turn_current_goal"] = None
    session.metadata["persistent_memories"] = []
    session.metadata["loaded_session_archive"] = None
    session.metadata["workspace_context"] = None
    session.metadata["live_research"] = None
    session.metadata["urg_library_context"] = None
    session.metadata["response_trace"] = None
    session.metadata["canonical_trace_contract"] = None
    session.metadata["model_route"] = None
    session.metadata["provider_mind"] = None
    session.metadata["provider_dispatch_trace"] = None
    session.metadata["god_brain"] = None
    session.metadata["specialist_profile"] = None
    session.metadata["writing_focus"] = None
    session.metadata["corrigibility_prompt_block"] = None
    session.metadata["provider_notice"] = None
    session.metadata["thread_contract"] = None
    session.metadata["drift_state"] = None
    session.metadata["sovereignty_contract"] = None
    session.metadata["external_suggestion_details"] = None
    session.metadata["external_suggestion_admission"] = None
    session.metadata["external_suggestion_law_enforcement"] = None


def _normalize_loaded_session_archive(payload):
    """Validate and clip one user-opened local session archive payload."""
    if not isinstance(payload, dict):
        return None

    try:
        message_count = max(0, min(500, int(payload.get("message_count") or 0)))
    except (TypeError, ValueError):
        message_count = 0

    transcript_text = str(payload.get("transcript_text") or "").strip()
    if not transcript_text:
        return None

    transcript_truncated = bool(payload.get("transcript_truncated"))
    if len(transcript_text) > 12000:
        transcript_text = f"{transcript_text[:12000].rstrip()}\n\n[Archive transcript truncated for prompt context.]"
        transcript_truncated = True

    raw_tags = payload.get("tags") or []
    if not isinstance(raw_tags, list):
        raw_tags = []

    return {
        "id": _clip_trace_text(str(payload.get("id") or "").strip(), limit=96) or None,
        "title": _clip_trace_text(str(payload.get("title") or "").strip(), limit=140) or "Saved Nova session",
        "saved_at": _clip_trace_text(str(payload.get("saved_at") or "").strip(), limit=48) or None,
        "assistant_name": _clip_trace_text(str(payload.get("assistant_name") or "").strip(), limit=48) or "Nova",
        "persona_mode": normalize_persona_mode(payload.get("persona_mode")),
        "response_mode": normalize_response_mode(payload.get("response_mode")),
        "message_count": message_count,
        "excerpt": _clip_trace_text(str(payload.get("excerpt") or "").strip(), limit=280) or None,
        "tags": [
            _clip_trace_text(str(tag).strip(), limit=48)
            for tag in raw_tags
            if _clip_trace_text(str(tag).strip(), limit=48)
        ][:8],
        "transcript_text": transcript_text,
        "transcript_truncated": transcript_truncated,
        "loaded_at": _clip_trace_text(str(payload.get("loaded_at") or "").strip(), limit=48)
        or datetime.now(UTC).isoformat(),
    }


def _build_loaded_session_archive_prompt_block(archive_context):
    """Render the explicit non-memory instruction block for a loaded local session archive."""
    tags = ", ".join(archive_context.get("tags") or []) or "none"
    saved_at = archive_context.get("saved_at") or "unknown"
    excerpt = archive_context.get("excerpt") or "none"
    transcript_text = archive_context.get("transcript_text") or ""

    return (
        "Loaded session archive (external context, not memory):\n"
        "- source: the user explicitly opened a saved local Nova session archive for this turn\n"
        f"- archive_id: {archive_context.get('id') or 'local_archive'}\n"
        f"- title: {archive_context.get('title') or 'Saved Nova session'}\n"
        f"- saved_at: {saved_at}\n"
        f"- assistant_name_at_save: {archive_context.get('assistant_name') or 'Nova'}\n"
        f"- persona_mode_at_save: {archive_context.get('persona_mode') or 'unknown'}\n"
        f"- response_mode_at_save: {archive_context.get('response_mode') or 'unknown'}\n"
        f"- message_count: {archive_context.get('message_count') or 0}\n"
        f"- tags: {tags}\n"
        "- rules:\n"
        "  - Treat this archive as a user-opened document, not as your memory or continuity.\n"
        "  - Never say you remember this session or imply the archive is part of your own memory.\n"
        "  - If you refer to it, call it a saved session or a loaded session archive.\n"
        "  - Use it only as supporting context for the current reply.\n"
        f"- excerpt: {excerpt}\n"
        "archive_transcript:\n"
        f"{transcript_text}"
    )


def _apply_loaded_session_archive(session, archive_payload):
    """Attach one explicit local session archive as the active turn's document context."""
    archive_context = _normalize_loaded_session_archive(archive_payload)
    if not archive_context:
        session.metadata["loaded_session_archive"] = None
        return None

    session.metadata["loaded_session_archive"] = {
        **archive_context,
        "prompt_block": _build_loaded_session_archive_prompt_block(archive_context),
    }
    return serialize_loaded_session_archive(session.metadata.get("loaded_session_archive"))


def _attach_session_mission_context(session):
    """Attach the current Mission Board context to the active session."""
    mission_context = mission_board.build_session_context(session.session_id)
    session.metadata["mission_board"] = mission_context
    return mission_context


def _attach_nova_invariant_consumer_snapshot(session):
    """Read-only Nova invariant comparison via invariant engine organ (Alt-9)."""
    from src.invariant_engine_organ import compare_nova_runtime_invariants

    lane = companion_lane_identity(
        session.metadata.get("persona_mode"),
        session.metadata.get("response_mode"),
    )
    snapshot = compare_nova_runtime_invariants(
        companion_lane=lane,
        governed_pipeline=_previous_governed_pipeline(session),
    )
    session.metadata["nova_invariant_consumer"] = snapshot
    return snapshot


def _resolve_provider_mind(session, user_message: str, response_mode: str):
    """Resolve the high-level Jarvis engine path for one turn."""
    resolved_voice = (session.metadata.get("mode_guidance") or {}).get("resolved_voice")
    surface_authority = _build_surface_authority_profile(
        resolved_mode=response_mode,
        resolved_voice=resolved_voice,
    )
    companion_profile = _get_companion_surface_profile(
        persona_mode=session.metadata.get("persona_mode"),
        response_mode=response_mode,
    )
    if _session_uses_companion_lane(session) or companion_profile:
        companion_profile = companion_profile or _get_companion_surface_profile(
            persona_mode=session.metadata.get("persona_mode"),
            response_mode=session.metadata.get("response_mode"),
        ) or COMPANION_SURFACE_PROFILES["tiny_nova"]
        decision = {
            "decision_id": f"pm_{companion_profile['identity']}_{uuid4().hex}",
            "engine_path": "jarvis_chat",
            "fallback_path": "local",
            "confidence": 0.98,
            "summary": f"ProviderMind kept {companion_profile['label']} on the companion surface while Jarvis retained routing authority.",
            "hidden_reason": companion_profile["hidden_reason"],
            "route_kind": "primary",
            **surface_authority,
        }
        session.metadata["provider_mind"] = decision
        return decision
    decision = jarvis_operator.choose_provider_path(
        user_message,
        response_mode=response_mode,
        mode_scope=(session.metadata.get("mode_guidance") or {}).get("resolved_scope"),
        workspace_context=session.metadata.get("workspace_context"),
        preferred_provider=session.metadata.get("preferred_provider"),
    )
    decision = dict(decision or {})
    decision.update(surface_authority)
    session.metadata["provider_mind"] = decision
    return decision


def _set_session_requested_specialists(session, requested_specialists=None):
    """Apply a manual specialist selection to the active session."""
    normalized = normalize_requested_specialists(
        requested_specialists
        if requested_specialists is not None
        else session.metadata.get("requested_specialists")
    )
    session.metadata["requested_specialists"] = normalized
    return normalized


def _set_session_requested_specialist_preset(session, requested_specialist_preset=None):
    """Apply one named specialist preset to the active session."""
    normalized = normalize_specialist_preset(
        requested_specialist_preset
        if requested_specialist_preset is not None
        else session.metadata.get("requested_specialist_preset")
    )
    session.metadata["requested_specialist_preset"] = normalized
    return normalized


def _record_session_event(session, event_type: str, summary: str, payload=None):
    """Append one compact V8-style event to the local session log."""
    normalized_summary = _normalize_trace_text(summary)
    active_event_keys = session.metadata.get("_active_turn_event_keys")
    if isinstance(active_event_keys, set):
        event_key = _session_event_key(event_type, normalized_summary, payload)
        if event_key in active_event_keys:
            return None
        active_event_keys.add(event_key)
    return v8_event_log.append(
        session.session_id,
        event_type=event_type,
        state=session.session_state.state,
        summary=normalized_summary,
        payload=payload,
    )


def _latest_session_event(session):
    """Return the most recent stored V8 event for one session."""
    events = v8_event_log.list_events(session.session_id, limit=1)
    if not events:
        return None
    return dict(events[-1])


def _transition_session_state(
    session,
    next_state: str,
    summary: str,
    reason: str | None = None,
    event_type: str | None = None,
    payload=None,
):
    """Transition a session lifecycle state and mirror it into the event log."""
    transition = session.transition_state(
        next_state,
        summary=summary,
        reason=reason,
        event_type=event_type,
    )
    _record_session_event(
        session,
        event_type=event_type or reason or next_state,
        summary=summary,
        payload={
            "transition": transition,
            **(payload or {}),
        },
    )
    return transition


def _build_live_session_event_payload(session, session_id, event_record):
    """Wrap a V8 event with the current runtime payload for SSE updates."""
    if not event_record:
        return None
    return {
        "event": "v8_event",
        "v8_event": dict(event_record),
        **_build_chat_runtime_payload(session, session_id),
    }


def _apply_policy_status(session, decision, event_type: str | None = None, payload=None):
    """Persist the latest policy decision on the session and optionally log it."""
    decision_dict = (
        decision.to_dict()
        if hasattr(decision, "to_dict")
        else dict(decision or default_policy_status())
    )
    session.apply_policy_status(decision_dict)
    if event_type:
        _record_session_event(
            session,
            event_type=event_type,
            summary=decision_dict.get("summary", "Policy check completed."),
            payload={
                "policy_status": decision_dict,
                **(payload or {}),
            },
        )
    return decision_dict


def _evaluate_turn_policy(session, user_message: str, response_mode: str, use_research=None):
    """Run the V8 turn policy engine and store the result on the session."""
    decision = v8_policy_engine.evaluate_turn(
        session,
        user_message=user_message,
        response_mode=response_mode,
        use_research=use_research,
    )
    return _apply_policy_status(
        session,
        decision,
        event_type="policy_turn_checked",
        payload={
            "response_mode": response_mode,
            "use_research": use_research,
        },
    )


def _evaluate_action_policy(session, action_id: str, approved: bool, action=None):
    """Run the V8 action policy engine and store the result on the session."""
    action = action or jarvis_operator.resolve_action(action_id)
    decision = v8_policy_engine.evaluate_action(
        session,
        action=action,
        approved=approved,
    )
    return action, _apply_policy_status(
        session,
        decision,
        event_type="policy_action_checked",
        payload={
            "action_id": action_id,
            "approved": approved,
        },
    )


ACTION_LIFECYCLE_TRANSITIONS = {
    None: {"proposed", "approved", "executed", "failed", "blocked"},
    "proposed": {"proposed", "approved", "blocked"},
    "approved": {"approved", "executed", "failed", "blocked"},
    "executed": set(),
    "failed": set(),
    "blocked": set(),
}
ACTION_LIFECYCLE_TERMINAL = {"executed", "failed", "blocked"}


def _generate_action_instance_id() -> str:
    """Return a stable per-proposal identity for one action lifecycle."""
    return f"act_{uuid4().hex}"


def _ensure_action_identity(action, *, action_instance_id: str | None = None, proposed_at: str | None = None):
    """Attach a stable per-proposal identity to one action payload."""
    if not isinstance(action, dict) or not action.get("id"):
        return None
    payload = dict(action)
    payload["action_instance_id"] = (
        action_instance_id
        or payload.get("action_instance_id")
        or _generate_action_instance_id()
    )
    if proposed_at or payload.get("proposed_at"):
        payload["proposed_at"] = proposed_at or payload.get("proposed_at")
    return payload


def _get_action_registry(session) -> dict:
    """Return the per-session action instance registry."""
    registry = session.metadata.get("action_registry")
    if not isinstance(registry, dict):
        registry = {}
        session.metadata["action_registry"] = registry
    return registry


def _get_action_instance_record(session, action_instance_id: str | None):
    """Return the stored lifecycle record for one action instance if present."""
    if not action_instance_id:
        return None
    registry = _get_action_registry(session)
    record = registry.get(action_instance_id)
    if isinstance(record, dict):
        return dict(record)
    return None


def _remember_action_instance(session, lifecycle: dict):
    """Persist the canonical lifecycle record for one action instance."""
    action_instance_id = lifecycle.get("action_instance_id")
    if not action_instance_id:
        return lifecycle
    registry = dict(_get_action_registry(session))
    registry[action_instance_id] = dict(lifecycle)
    session.metadata["action_registry"] = registry
    return lifecycle


def _can_transition_action_instance(current_stage: str | None, next_stage: str) -> bool:
    """Return whether an action instance may move into the requested lifecycle stage."""
    return next_stage in ACTION_LIFECYCLE_TRANSITIONS.get(current_stage, set())


def _is_finalized_action_instance(session, action) -> bool:
    """Return whether this action instance has already reached a terminal lifecycle stage."""
    action_instance_id = str((action or {}).get("action_instance_id") or "").strip()
    if not action_instance_id:
        return False
    record = _get_action_instance_record(session, action_instance_id) or {}
    stage = record.get("stage")
    return stage in ACTION_LIFECYCLE_TERMINAL


def _store_pending_action(session, action):
    """Persist the latest approval-gated local action on the session."""
    if isinstance(action, dict) and action.get("id"):
        session.metadata["pending_action"] = _ensure_action_identity(action)
        _sync_approval_runtime_state(session)
        return session.metadata["pending_action"]
    session.metadata.pop("pending_action", None)
    _sync_approval_runtime_state(session)
    return None


def _load_pending_action(session):
    """Load the latest pending action from metadata or a recent action request turn."""
    pending_action = session.metadata.get("pending_action")
    if isinstance(pending_action, dict) and pending_action.get("id"):
        pending_action = _ensure_action_identity(pending_action)
        if _is_finalized_action_instance(session, pending_action):
            session.metadata.pop("pending_action", None)
            return None
        return dict(pending_action)

    for turn in reversed(session.turns):
        metadata = turn.metadata or {}
        tool_result = metadata.get("tool_result") or {}
        if tool_result.get("type") != "action_request":
            continue
        action = _ensure_action_identity(tool_result.get("action") or {})
        if action.get("id"):
            if _is_finalized_action_instance(session, action):
                return None
            return _store_pending_action(session, action)

    return None


def _sync_pending_action(session, tool_result, response_mode: str | None = None):
    """Keep pending-action state aligned with direct tool responses."""
    tool_type = (tool_result or {}).get("type")
    if tool_type == "action_request":
        action = _store_pending_action(session, (tool_result or {}).get("action"))
        _set_action_lifecycle(
            session,
            stage="proposed",
            action=action,
            approval_state="awaiting",
            execution_state="pending",
            source="direct_tool",
            response_mode=response_mode or "operator",
        )
        return action
    if tool_type == "action_result":
        _store_pending_action(session, None)
        action = _ensure_action_identity((tool_result or {}).get("action") or {})
        lifecycle_stage = "failed" if (tool_result or {}).get("status") == "failed" else "executed"
        _set_action_lifecycle(
            session,
            stage=lifecycle_stage,
            action=action,
            approval_state="approved",
            execution_state="failed" if lifecycle_stage == "failed" else "executed",
            source="direct_tool",
            response_mode=response_mode or "operator",
            result_status=(tool_result or {}).get("status"),
            exit_code=(tool_result or {}).get("exit_code"),
        )
        return None
    return session.metadata.get("pending_action")


def _is_action_approval_message(user_message: str, pending_action=None) -> bool:
    """Return whether the latest user turn clearly approves a pending local action."""
    lower = str(user_message or "").strip().lower()
    if not lower:
        return False
    if lower in {"no", "nope", "nah"} or lower.startswith("no "):
        return False
    if ACTION_REJECTION_RE.search(lower):
        return False

    pending_action_id = str((pending_action or {}).get("id") or "").strip().lower()
    if lower.startswith("approve action "):
        requested_action = lower[15:].strip()
        return not pending_action_id or requested_action == pending_action_id
    if lower.startswith("approve "):
        requested_action = lower[8:].strip()
        if pending_action_id and requested_action == pending_action_id:
            return True

    return bool(ACTION_APPROVAL_RE.match(lower))


def _resolve_direct_tool_response_mode(response_mode: str, tool_result=None) -> str:
    """Keep approval-gated execution turns in the operator lane."""
    if ((tool_result or {}).get("type") or "").strip() in {
        "action_request",
        "action_result",
        "external_suggestion_guardrail",
        "forge_result",
        "forge_error",
        "lane_guardrail",
        "memory_add",
        "memory_list",
        "memory_rejection",
        "memory_rejection_followup",
        "otem",
    }:
        return "operator"
    return normalize_response_mode(response_mode)


def _memory_rejection_reason_text(reason: str) -> str:
    normalized = " ".join(str(reason or "").lower().split()).strip()
    labels = {
        "conflict": "conflicts with governed memory truth",
        "state_class_mismatch": "the requested merge crossed state-class boundaries",
        "truth_scope_violation": "the request did not qualify for live canonical memory",
        "inactive_memory": "the merge source was inactive or archived",
        "canonical_protection": "canonical protection blocked the write",
        "rejected": "governance rejected the request",
        "no_action": "there is no safe memory action to take",
        "terminal_rejection": "the request ended in a clean rejection with no follow-on action",
    }
    return labels.get(normalized, "governance rejected the request")


def _memory_rejection_next_step_text(next_step: str) -> str | None:
    normalized = " ".join(str(next_step or "").lower().split()).strip()
    mapping = {
        "use_session_scope": "Keep it in session scope only if you need it for the current turn.",
        "request_operator_override": "Use an explicit operator override path if you want to challenge governed memory authority.",
        "submit_conflict_pair": "Submit the competing memories as a conflict pair instead of forcing a direct merge.",
        "review_canonical_memory": "Review the current canonical memory before attempting another governed change.",
        "none": None,
        "no_next_step": None,
    }
    return mapping.get(normalized)


def _generate_memory_rejection_explanation(memory_rejection) -> str:
    rejection = dict(memory_rejection or {})
    action = "merge" if rejection.get("action") == "merge" else "store"
    decision_line = f"Decision: not {'merged' if action == 'merge' else 'stored'}."
    reason_line = f"Reason: {_memory_rejection_reason_text(rejection.get('reason'))}."
    detail = " ".join(str(rejection.get("detail") or "").split()).strip()
    meaning_line = (
        "Meaning: this did not enter live canonical memory."
        if action == "store"
        else "Meaning: live canonical memory was left unchanged."
    )
    lines = [decision_line, reason_line]
    if detail:
        lines.append(f"Detail: {detail}")
    lines.append(meaning_line)
    next_step = _memory_rejection_next_step_text(rejection.get("next_step"))
    if next_step:
        lines.append(f"Next step: {next_step}")
    return "\n".join(lines)


def _generate_memory_rejection_followup_explanation(memory_rejection) -> str:
    rejection = dict(memory_rejection or {})
    lines = [
        "Decision: no conflicting canonical memory is available to merge.",
        f"Reason: the earlier request was rejected because {_memory_rejection_reason_text(rejection.get('reason'))}.",
        "Meaning: nothing from that rejected request entered live canonical memory, so there is no admitted conflict pair to reconcile.",
    ]
    next_step = _memory_rejection_next_step_text(rejection.get("next_step"))
    if next_step:
        lines.append(f"Next step: {next_step}")
    return "\n".join(lines)


def _finalize_direct_tool_response_text(session, user_message: str, tool_result: dict, fallback_response: str) -> str:
    """Finalize direct-tool output through the same operator-facing continuity gate."""
    tool_type = str((tool_result or {}).get("type") or "").strip()
    if tool_type == "memory_rejection":
        return _generate_memory_rejection_explanation((tool_result or {}).get("memory_rejection"))
    if tool_type == "memory_rejection_followup":
        return _generate_memory_rejection_followup_explanation((tool_result or {}).get("memory_rejection"))
    if tool_type == "otem":
        otem_payload = dict((tool_result or {}).get("otem") or {})
        return generate_otem_reason_only_answer_with_context(
            otem_payload.get("restated_task") or otem_payload.get("task") or user_message,
            list(otem_payload.get("plan") or []),
            session_context=otem_payload.get("session_context"),
            execution_awareness=otem_payload.get("execution_awareness"),
            workflow_handoff=otem_payload.get("workflow_handoff"),
            tool_awareness=otem_payload.get("tool_awareness"),
            operation=otem_payload.get("operation"),
        )
    return _enforce_identity_safe_response(
        session,
        user_message=user_message,
        response_text=fallback_response,
        response_trace=session.metadata.get("response_trace"),
    )


def _finalize_otem_boundary_response(
    session,
    user_message: str,
    direct_tool: dict,
    response_text: str,
):
    """Run OTEM direct-tool replies through the shared completion boundary and trace the seam."""
    if str((direct_tool or {}).get("type") or "").strip() != "otem":
        return response_text
    response_trace = session.metadata.get("response_trace")
    raw_response_text = str(response_text or "")
    finalized_text = _finalize_visible_response(
        session,
        user_message,
        raw_response_text,
        response_trace=response_trace,
        generation_metadata={
            "stop_reason": "direct_tool",
            "finish_reason": "direct_tool",
        },
    )
    _sync_otem_visible_answer(
        finalized_text,
        otem_payload=(direct_tool or {}).get("otem"),
        turn_contract=session.metadata.get("turn_contract"),
        session=session,
    )
    completion_trace = dict(session.metadata.get("output_completion_trace") or {})
    _record_otem_boundary_trace(
        session,
        response_trace,
        user_message=user_message,
        otem_payload=(direct_tool or {}).get("otem"),
        raw_response_text=raw_response_text,
        final_response_text=finalized_text,
        completion_trace=completion_trace,
    )
    return finalized_text


def _apply_direct_tool_turn_contract(session, tool_result: dict, response_mode: str):
    """Project direct-tool-specific turn contract state onto the authoritative turn contract."""
    direct_tool = dict(tool_result or {})
    normalized_mode = _resolve_direct_tool_response_mode(response_mode, direct_tool)
    _set_turn_contract(
        session,
        resolved_mode=normalized_mode,
        resolved_scope="operator_task",
        resolved_voice="jarvis",
        contract_label="direct_tool",
    )
    tool_type = str(direct_tool.get("type") or "").strip()
    if tool_type in {"memory_rejection", "memory_rejection_followup"}:
        _set_turn_contract(
            session,
            resolved_mode="operator",
            resolved_scope="operator_task",
            resolved_voice="jarvis",
            memory_rejection=direct_tool.get("memory_rejection"),
            contract_label="memory_governance",
        )
    elif tool_type == "otem":
        _set_turn_contract(
            session,
            resolved_mode="operator",
            resolved_scope="operator_task",
            resolved_voice="jarvis",
            otem=direct_tool.get("otem"),
            contract_label="otem",
        )
        session.metadata["otem_state"] = dict(direct_tool.get("otem") or {})
    elif tool_type == "external_suggestion_guardrail":
        _set_turn_contract(
            session,
            resolved_mode="operator",
            resolved_scope="operator_task",
            resolved_voice="jarvis",
            contract_label="external_suggestion_guardrail",
        )
    elif tool_type == "lane_guardrail":
        _set_turn_contract(
            session,
            resolved_mode="operator",
            resolved_scope="operator_task",
            resolved_voice="jarvis",
            contract_label="lane_guardrail",
        )
    return session.metadata.get("turn_contract")


def _maybe_handle_memory_rejection_followup(session, user_message: str):
    """Answer bounded follow-ups when the prior memory request never entered canonical memory."""
    prior_contract = dict(session.metadata.get("last_turn_contract") or {})
    rejection = dict(prior_contract.get("memory_rejection") or {})
    lower = " ".join(str(user_message or "").lower().split())
    if not rejection:
        return None
    if "conflicting memory" not in lower and "conflict pair" not in lower:
        return None
    return {
        "response": "No conflicting canonical memory was admitted from the rejected request.",
        "tool_result": {
            "type": "memory_rejection_followup",
            "status": "explained",
            "memory_rejection": rejection,
            "summary": "Jarvis explained that the rejected memory request never entered canonical memory.",
        },
    }


def _build_otem_result(
    task: str,
    *,
    session_id: str | None = None,
    prior_state: dict | None = None,
) -> dict:
    """Build one deterministic OTEM result without crossing the model boundary."""
    return jarvis_operator.build_otem_turn_result(
        task,
        session_id=session_id,
        prior_state=prior_state,
    )


def _set_action_lifecycle(
    session,
    *,
    stage: str,
    action=None,
    approval_state: str | None = None,
    execution_state: str | None = None,
    source: str | None = None,
    response_mode: str | None = None,
    error: str | None = None,
    result_status: str | None = None,
    exit_code=None,
):
    """Persist one canonical action lifecycle record for UI, API, and tests."""
    current = dict(session.metadata.get("action_lifecycle") or {})
    incoming_action = _ensure_action_identity(
        action or current.get("action") or {},
        action_instance_id=(action or {}).get("action_instance_id") if isinstance(action, dict) else None,
        proposed_at=(action or {}).get("proposed_at") if isinstance(action, dict) else None,
    )
    action_payload = dict(incoming_action or current.get("action") or {})
    action_instance_id = action_payload.get("action_instance_id")
    prior_record = _get_action_instance_record(session, action_instance_id) or {}
    current_stage = prior_record.get("stage")
    if not current_stage and current.get("action_instance_id") == action_instance_id:
        current_stage = current.get("stage")
    if not _can_transition_action_instance(current_stage, stage):
        raise ValueError(
            f"Illegal action lifecycle transition for {action_instance_id or 'unknown action'}: "
            f"{current_stage or 'none'} -> {stage}"
        )
    lifecycle = {
        "stage": stage,
        "approval_state": approval_state or prior_record.get("approval_state") or current.get("approval_state"),
        "execution_state": execution_state or prior_record.get("execution_state") or current.get("execution_state"),
        "source": source or prior_record.get("source") or current.get("source"),
        "mode": _resolve_direct_tool_response_mode(
            response_mode or session.metadata.get("response_mode"),
            {"type": "action_result" if action_payload else ""},
        ),
        "updated_at": datetime.now(UTC).isoformat(),
        "pending_action": bool(session.metadata.get("pending_action")),
        "awaiting_approval": session.session_state.state == "awaiting_approval",
        "action": action_payload or None,
    }
    if action_payload:
        lifecycle["action_id"] = action_payload.get("id")
        lifecycle["action_label"] = action_payload.get("label")
        lifecycle["action_instance_id"] = action_instance_id
    for timestamp_field in ("proposed_at", "approved_at", "executed_at", "failed_at", "blocked_at"):
        preserved_value = prior_record.get(timestamp_field) or current.get(timestamp_field)
        if preserved_value:
            lifecycle[timestamp_field] = preserved_value
    now_iso = lifecycle["updated_at"]
    if stage == "proposed":
        lifecycle["proposed_at"] = lifecycle.get("proposed_at") or now_iso
        if lifecycle.get("action"):
            lifecycle["action"]["proposed_at"] = lifecycle["proposed_at"]
    elif stage == "approved":
        lifecycle["approved_at"] = lifecycle.get("approved_at") or now_iso
    elif stage == "executed":
        lifecycle["executed_at"] = lifecycle.get("executed_at") or now_iso
    elif stage == "failed":
        lifecycle["failed_at"] = lifecycle.get("failed_at") or now_iso
    elif stage == "blocked":
        lifecycle["blocked_at"] = lifecycle.get("blocked_at") or now_iso
    if result_status is not None:
        lifecycle["result_status"] = result_status
    elif "result_status" in prior_record:
        lifecycle["result_status"] = prior_record["result_status"]
    elif "result_status" in current:
        lifecycle["result_status"] = current["result_status"]
    if exit_code is not None:
        lifecycle["exit_code"] = exit_code
    elif "exit_code" in prior_record:
        lifecycle["exit_code"] = prior_record["exit_code"]
    elif "exit_code" in current:
        lifecycle["exit_code"] = current["exit_code"]
    if error:
        lifecycle["error"] = error
    elif "error" in prior_record:
        lifecycle["error"] = prior_record["error"]
    elif "error" in current:
        lifecycle["error"] = current["error"]
    session.metadata["action_lifecycle"] = lifecycle
    stored = _remember_action_instance(session, lifecycle)
    try:
        jarvis_operator.record_action_lifecycle(session.session_id, stored)
    except Exception as exc:
        logger.warning("Could not persist evolving approval audit: %s", exc)
    _sync_approval_runtime_state(session)
    return stored


def _refresh_action_lifecycle(session):
    """Keep lifecycle flags aligned with the current session state."""
    lifecycle = session.metadata.get("action_lifecycle")
    if not isinstance(lifecycle, dict):
        return None
    refreshed = dict(lifecycle)
    refreshed["pending_action"] = bool(session.metadata.get("pending_action"))
    refreshed["awaiting_approval"] = session.session_state.state == "awaiting_approval"
    refreshed["updated_at"] = datetime.now(UTC).isoformat()
    session.metadata["action_lifecycle"] = refreshed
    _remember_action_instance(session, refreshed)
    response_trace = session.metadata.get("response_trace")
    if isinstance(response_trace, dict) and isinstance(response_trace.get("action_lifecycle"), dict):
        response_trace["action_lifecycle"] = dict(refreshed)
    _sync_approval_runtime_state(session)
    return refreshed


def _sync_approval_runtime_state(session):
    """Mirror the current approval-gated action state into the durable approval snapshot."""
    try:
        return jarvis_operator.sync_approval_state(
            session.session_id,
            pending_action=session.metadata.get("pending_action"),
            action_lifecycle=session.metadata.get("action_lifecycle"),
        )
    except Exception as exc:
        logger.warning("Could not sync current approval state: %s", exc)
        return None


def _execute_approved_local_action(session, action_id: str, action=None, approval_source: str = "manual"):
    """Execute an approved local action through the shared direct-tool path."""
    action = _ensure_action_identity(
        action or jarvis_operator.action_runner.get_action(action_id) or {"id": action_id}
    )
    if _is_finalized_action_instance(session, action):
        raise ValueError(
            f"Action instance {action.get('action_instance_id')} is already finalized as "
            f"{(_get_action_instance_record(session, action.get('action_instance_id')) or {}).get('stage')}."
        )
    _store_pending_action(session, None)
    _set_action_lifecycle(
        session,
        stage="approved",
        action=action,
        approval_state="approved",
        execution_state="pending",
        source=approval_source,
        response_mode="operator",
    )
    _clear_turn_context(session)
    _set_turn_contract(
        session,
        requested_mode="operator",
        resolved_mode="operator",
        resolved_scope="operator_task",
        resolved_voice="jarvis",
        contract_label="action_execution",
    )
    bridge_result = _route_action_execution_to_bridge(
        session,
        action_id=action_id,
        action=action,
        approval_source=approval_source,
    )
    _record_session_event(
        session,
        "cognitive_bridge_routed",
        summarize_bridge_result(bridge_result),
        payload=bridge_result,
    )
    if bridge_result.get("decision") == "BLOCK":
        blocked_summary = _bridge_block_message(
            bridge_result,
            "Cognitive Bridge blocked the local action before execution.",
        )
        _set_action_lifecycle(
            session,
            stage="blocked",
            action=action,
            approval_state="approved",
            execution_state="blocked",
            source=approval_source,
            response_mode="operator",
            error=blocked_summary,
        )
        _transition_session_state(
            session,
            "degraded",
            summary="A local action was blocked by the Cognitive Bridge before execution.",
            reason="action_blocked",
            event_type="action_blocked",
            payload={
                "action_id": action_id,
                "bridge_result": bridge_result,
            },
        )
        blocked_result = {
            "response": f"{(action or {}).get('label', action_id)} was not executed.\n{blocked_summary}\n\nExit code: 1",
            "tool_result": {
                "type": "action_result",
                "action": action,
                "status": "blocked",
                "exit_code": 1,
                "stdout": "",
                "stderr": "",
                "summary": blocked_summary,
                "ran_at": datetime.now(UTC).isoformat(),
                "cognitive_bridge": bridge_result,
            },
        }
        session.metadata["response_trace"] = _build_tool_response_trace(
            "operator",
            tool_result=blocked_result["tool_result"],
            provider_mind=_resolve_provider_mind(session, f"Execute action {action_id}", "operator"),
            action_lifecycle=session.metadata.get("action_lifecycle"),
            turn_contract=session.metadata.get("turn_contract"),
            cognitive_bridge=bridge_result,
            session=session,
            runtime_context="operator_runtime",
        )
        session.add_turn(
            "assistant",
            blocked_result["response"],
            metadata={
                "persistent_memories": [],
                "workspace_context": None,
                "live_research": None,
                "urg_library_context": None,
                "response_trace": session.metadata.get("response_trace"),
                "tool_result": blocked_result["tool_result"],
            },
        )
        _refresh_action_lifecycle(session)
        _record_session_event(
            session,
            "action_execution_blocked",
            blocked_summary,
            payload={"action_id": action_id, "bridge_result": bridge_result},
        )
        return blocked_result
    _transition_session_state(
        session,
        "acting",
        summary="Jarvis is executing an approved local action.",
        reason="action_execution",
        event_type="action_execution_started",
        payload={
            "action_id": action_id,
            "action_label": (action or {}).get("label"),
            "approval_source": approval_source,
        },
    )
    try:
        action_result = jarvis_operator.execute_action(
            action_id,
            action=action,
            session_id=session.session_id,
            cognitive_bridge=bridge_result,
        )
    except Exception as exc:
        _set_action_lifecycle(
            session,
            stage="failed",
            action=action,
            approval_state="approved",
            execution_state="failed",
            source=approval_source,
            response_mode="operator",
            error=str(exc),
        )
        session.metadata["response_trace"] = _build_tool_response_trace(
            "operator",
            tool_result={"type": "action_result", "action": action, "status": "failed"},
            provider_mind=_resolve_provider_mind(session, f"Execute action {action_id}", "operator"),
            action_lifecycle=session.metadata.get("action_lifecycle"),
            turn_contract=session.metadata.get("turn_contract"),
            cognitive_bridge=bridge_result,
            session=session,
            runtime_context="operator_runtime",
        )
        _record_session_event(
            session,
            "action_execution_failed",
            "Jarvis failed while running an approved local action.",
            payload={"action_id": action_id, "error": str(exc), "approval_source": approval_source},
        )
        raise
    _clear_turn_context(session)
    action_result_tool = action_result.get("tool_result") or {}
    action_result_action = _ensure_action_identity(
        action_result_tool.get("action") or action,
        action_instance_id=action.get("action_instance_id"),
        proposed_at=action.get("proposed_at"),
    )
    action_result_tool["action"] = action_result_action
    action_result["tool_result"] = action_result_tool
    _apply_direct_tool_turn_contract(session, action_result_tool, "operator")
    mission_board.attach_action_result(session.session_id, action_result.get("tool_result"))
    _attach_session_mission_context(session)
    specialist_preset = get_specialist_preset(session.metadata.get("requested_specialist_preset"))
    action_tool_result = action_result.get("tool_result") or {}
    tool_response_mode = _resolve_direct_tool_response_mode("operator", action_tool_result)
    god_brain = build_god_brain_trace(
        user_message=f"Execute action {action_id}",
        response_mode=tool_response_mode,
        current_goal=session.spiral_state.current_goal,
        contract="direct_tool",
        requested_specialists=session.metadata.get("requested_specialists"),
        specialist_preset=specialist_preset,
        policy_status=session.metadata.get("policy_status"),
        mode_guidance=session.metadata.get("mode_guidance"),
        tool_type=action_tool_result.get("type"),
        tool_label=(action_tool_result.get("action") or {}).get("label"),
    )
    session.metadata["god_brain"] = god_brain
    _resolve_provider_mind(session, f"Execute action {action_id}", tool_response_mode)
    session.metadata["model_route"] = resolve_model_route(
        response_mode=tool_response_mode,
        specialist_preset=specialist_preset,
        god_brain=god_brain,
        policy_status=session.metadata.get("policy_status"),
        tool_type=action_tool_result.get("type"),
        preferred_provider=session.metadata.get("preferred_provider"),
        provider_available=provider_registry.can_invoke,
    )
    lifecycle_stage = "failed" if action_tool_result.get("status") == "failed" else "executed"
    _set_action_lifecycle(
        session,
        stage=lifecycle_stage,
        action=action_tool_result.get("action") or action,
        approval_state="approved",
        execution_state="failed" if lifecycle_stage == "failed" else "executed",
        source=approval_source,
        response_mode=tool_response_mode,
        result_status=action_tool_result.get("status"),
        exit_code=action_tool_result.get("exit_code"),
    )
    session.metadata["response_trace"] = _build_tool_response_trace(
        tool_response_mode,
        tool_result=action_result["tool_result"],
        god_brain=god_brain,
        model_route=session.metadata.get("model_route"),
        provider_mind=session.metadata.get("provider_mind"),
        specialist_preset=specialist_preset,
        action_lifecycle=session.metadata.get("action_lifecycle"),
        turn_contract=session.metadata.get("turn_contract"),
        cognitive_bridge=bridge_result,
        session=session,
        runtime_context="operator_runtime",
    )
    review = mission_critic.review_action_result(
        tool_result=action_result.get("tool_result"),
        mission_context=session.metadata.get("mission_board"),
    )
    _apply_mission_critic_review(session, review)
    session.add_turn(
        "assistant",
        action_result["response"],
        metadata={
            "persistent_memories": [],
            "workspace_context": None,
            "live_research": None,
            "urg_library_context": None,
            "response_trace": session.metadata.get("response_trace"),
            "tool_result": action_result["tool_result"],
        },
    )
    _refresh_action_lifecycle(session)
    _record_session_event(
        session,
        "action_execution_completed",
        "Jarvis completed an approved local action.",
        payload={
            "action_id": action_id,
            "action_status": action_result["tool_result"].get("status"),
            "exit_code": action_result["tool_result"].get("exit_code"),
            "approval_source": approval_source,
        },
    )
    return action_result


def _consume_pending_action_approval(
    session,
    user_message: str,
    awaiting_approval: bool | None = None,
    pending_action=None,
):
    """Execute a waiting pending action when the latest user turn is explicit approval."""
    if awaiting_approval is None:
        awaiting_approval = session.session_state.state == "awaiting_approval"
    pending_action = pending_action or _load_pending_action(session)
    if not awaiting_approval or not pending_action:
        return None
    if str(pending_action.get("type") or "") == "slingshot_signoff":
        if not _is_action_approval_message(user_message, pending_action=pending_action):
            return None
        _store_pending_action(session, None)
        slingshot = dict(session.metadata.get("slingshot") or {})
        slingshot["status"] = "active"
        session.metadata["slingshot"] = slingshot
        return {
            "action_result": {
                "response": (
                    "Slingshot signoff accepted. Governed fast-path launch is re-enabled for this case."
                ),
                "tool_result": {
                    "type": "slingshot_signoff",
                    "status": "approved",
                    "case_id": pending_action.get("case_id"),
                },
            },
        }
    if _is_finalized_action_instance(session, pending_action):
        _store_pending_action(session, None)
        _refresh_action_lifecycle(session)
        return None
    if not _is_action_approval_message(user_message, pending_action=pending_action):
        return None

    action_id = pending_action.get("id")
    action, policy_status = _evaluate_action_policy(
        session,
        action_id,
        approved=True,
        action=pending_action,
    )
    action = _ensure_action_identity(
        action or pending_action,
        action_instance_id=pending_action.get("action_instance_id"),
        proposed_at=pending_action.get("proposed_at"),
    )
    if not policy_status.get("allowed", True):
        _store_pending_action(session, None)
        _set_action_lifecycle(
            session,
            stage="blocked",
            action=action,
            approval_state="approved",
            execution_state="blocked",
            source="approval_turn",
            response_mode="operator",
            error=policy_status.get("summary", "Local action blocked."),
        )
        _transition_session_state(
            session,
            "degraded",
            summary="A local action was blocked by the policy guardrails.",
            reason="action_blocked",
            event_type="action_blocked",
            payload={"action_id": action_id, "policy_status": policy_status},
        )
        _refresh_action_lifecycle(session)
        _set_turn_contract(
            session,
            requested_mode="operator",
            resolved_mode="operator",
            resolved_scope="operator_task",
            resolved_voice="jarvis",
            contract_label="action_blocked",
        )
        session.metadata["response_trace"] = _build_tool_response_trace(
            "operator",
            tool_result={"type": "action_request", "action": action},
            provider_mind=_resolve_provider_mind(session, f"Approve action {action_id}", "operator"),
            action_lifecycle=session.metadata.get("action_lifecycle"),
            turn_contract=session.metadata.get("turn_contract"),
            session=session,
        )
        return {
            "blocked": True,
            "action": action,
            "policy_status": policy_status,
        }

    _record_session_event(
        session,
        "action_approval_received",
        "Jarvis received approval and is executing the pending local action immediately.",
        payload={"action_id": action_id, "action_label": (action or {}).get("label")},
    )
    action_result = _execute_approved_local_action(
        session,
        action_id,
        action=action,
        approval_source="approval_turn",
    )
    if str((action_result.get("tool_result") or {}).get("status") or "").strip().lower() == "blocked":
        return {
            "blocked": True,
            "action": action,
            "policy_status": {
                **dict(policy_status or {}),
                "summary": (action_result.get("tool_result") or {}).get("summary")
                or "Local action blocked.",
            },
            "action_result": action_result,
        }
    return {
        "blocked": False,
        "action": action,
        "policy_status": policy_status,
        "action_result": action_result,
    }


def _should_auto_route_mode(requested_mode: str, recommended_mode: str, confidence: float) -> bool:
    """Return whether Jarvis should automatically route this turn into a different mode."""
    requested = normalize_response_mode(requested_mode)
    recommended = normalize_response_mode(recommended_mode)
    if requested != "fast":
        return False
    if recommended not in MODE_AUTO_ROUTE_TARGETS:
        return False
    return confidence >= MODE_AUTO_ROUTE_MIN_CONFIDENCE


def _resolve_turn_mode_guidance(session, user_message: str, requested_mode: str, use_research=None):
    """Resolve requested, recommended, and effective operating modes for one turn."""
    companion_identity = companion_lane_identity(
        session.metadata.get("persona_mode"),
        requested_mode if requested_mode is not None else session.metadata.get("response_mode"),
    )
    if _session_uses_companion_lane(session) or companion_identity:
        return _build_companion_mode_guidance(session, companion_identity)

    requested = normalize_response_mode(
        requested_mode
        if requested_mode is not None
        else session.metadata.get("requested_response_mode") or session.metadata.get("response_mode")
    )
    mode_freeze = _get_mode_freeze(session)
    if mode_freeze:
        requested = normalize_response_mode(mode_freeze.get("mode"))
    previous_effective_mode = normalize_response_mode(session.metadata.get("last_effective_response_mode"))
    recommendation = recommend_response_mode(
        user_message,
        current_mode=requested,
        live_research_enabled=use_research,
        previous_turn_was_debugging=previous_effective_mode == "debug",
    )
    recommended = normalize_response_mode(recommendation.get("recommended_mode"))
    auto_applied = _should_auto_route_mode(
        requested_mode=requested,
        recommended_mode=recommended,
        confidence=float(recommendation.get("confidence", 0.0)),
    )
    if recommended == "research" and use_research is False:
        auto_applied = False
    effective = recommended if auto_applied else requested
    status = "aligned"
    summary = recommendation.get("summary") or "Current operating mode fits this turn."
    if auto_applied:
        status = "auto_routed"
        summary = (
            f"Jarvis auto-routed this turn from {requested.title()} to {effective.title()} "
            f"because the request strongly matched {effective} work."
        )
    elif recommended != requested:
        status = "recommended_switch"
        summary = (
            f"{recommended.title()} looks like a better fit than {requested.title()} for this request."
        )
    objective = detect_objective(user_message)
    if objective in {"handle_direct_challenge", "answer_relational_question"}:
        resolved_scope = "relational"
    else:
        resolved_scope = "debugging" if effective == "debug" else str(
            recommendation.get("selector_scope") or "operator_task"
        )

    guidance = {
        "status": status,
        "requested_mode": requested,
        "effective_mode": effective,
        "recommended_mode": recommended,
        "confidence": round(float(recommendation.get("confidence", 0.0)), 3),
        "reason": recommendation.get("reason"),
        "summary": summary,
        "signals": list(recommendation.get("signals") or []),
        "auto_applied": auto_applied,
        "resolved_scope": resolved_scope,
        "resolved_voice": "jarvis",
        "selector_reason": recommendation.get("selector_reason"),
        "selector_trigger": recommendation.get("selector_trigger"),
        "debug_lockout_applied": bool(recommendation.get("debug_lockout_applied")) and effective != "debug",
        "previous_effective_mode": previous_effective_mode,
        "mode_frozen": bool(mode_freeze),
        "frozen_mode": normalize_response_mode((mode_freeze or {}).get("mode")) if mode_freeze else None,
        "frozen_turns_remaining": int((mode_freeze or {}).get("remaining_turns") or 0) if mode_freeze else 0,
    }
    guidance.update(_build_surface_authority_profile(resolved_mode=effective, resolved_voice="jarvis"))
    session.metadata["requested_response_mode"] = requested
    session.metadata["response_mode"] = effective
    session.metadata["mode_guidance"] = guidance
    session.metadata["last_effective_response_mode"] = effective
    session.metadata["last_selector_scope"] = resolved_scope
    session.metadata["last_selector_voice"] = "jarvis"
    if objective == "handle_direct_challenge":
        contract_label = "direct_challenge"
    elif objective == "answer_relational_question":
        contract_label = "relational_question"
    else:
        contract_label = "mode_guidance"
    _set_turn_contract(
        session,
        requested_mode=requested,
        resolved_mode=effective,
        resolved_scope=resolved_scope,
        resolved_voice="jarvis",
        contract_label=contract_label,
    )
    return requested, effective, guidance


def _looks_like_deeper_research_request(text: str) -> bool:
    """Detect prompts that benefit from a wider evidence pass in Think mode."""
    lower = " ".join(str(text or "").lower().split())
    return any(hint in lower for hint in THINK_RESEARCH_HINTS)


def _should_attach_live_research(
    user_message: str,
    response_mode: str,
    use_research: bool | None = None,
):
    """Resolve whether live research should be attached for this turn."""
    if use_research is True:
        return True, "explicit"

    if use_research is False:
        return False, "disabled"

    normalized_mode = normalize_response_mode(response_mode)
    if normalized_mode in {"tiny", "small"}:
        return False, f"{normalized_mode}_default_local"
    if normalized_mode == "research":
        return True, "research_default_on"

    if normalized_mode in {"fast", "builder", "operator"}:
        return False, f"{normalized_mode}_default_local"

    if normalized_mode in {"think", "debug"} and (
        looks_like_live_research_request(user_message)
        or _looks_like_deeper_research_request(user_message)
    ):
        return True, f"{normalized_mode}_auto"

    return False, "not_needed"


def _build_governed_pipeline_trace(
    response_mode: str,
    contract: str | None,
    *,
    god_brain=None,
    model_route=None,
    tool_result=None,
    turn_contract=None,
    runtime_context: str = "live_runtime",
    previous_pipeline: dict | None = None,
    operator_text: str | None = None,
):
    """Build the governed packet trace for the current core or tool turn."""
    return build_governed_turn_pipeline(
        response_mode=response_mode,
        contract=contract,
        god_brain=god_brain,
        model_route=model_route,
        tool_result=tool_result,
        surface_identity=(god_brain or {}).get("surface_identity"),
        turn_contract=turn_contract,
        runtime_context=runtime_context,
        previous_pipeline=previous_pipeline,
        operator_text=operator_text,
    )


def _previous_governed_pipeline(session):
    """Return the previous governed pipeline snapshot for one session, when available."""
    metadata = getattr(session, "metadata", {}) or {}
    response_trace = dict(metadata.get("response_trace") or {})
    pipeline = response_trace.get("governed_pipeline")
    if isinstance(pipeline, dict) and pipeline:
        return dict(pipeline)
    return None


def _apply_coherence_guard_to_response_trace(response_trace: dict) -> dict:
    """Attach coherence_protocol and block metadata when hard-block is active."""
    from src.operator_cognition_coherence_fabric import (
        assert_coherence_allows_turn,
        coherence_protocol_from_pipeline,
    )

    if not isinstance(response_trace, dict):
        return response_trace
    pipeline = response_trace.get("governed_pipeline")
    if isinstance(pipeline, dict):
        response_trace["coherence_protocol"] = coherence_protocol_from_pipeline(pipeline)
    result = assert_coherence_allows_turn(pipeline if isinstance(pipeline, dict) else None)
    if not result.allowed:
        response_trace["blocked_by"] = "coherence_fabric"
        response_trace["error"] = result.reason or "coherence fabric blocked"
        response_trace["contract"] = "coherence_blocked"
        response_trace["contract_label"] = "coherence blocked"
        response_trace["summary"] = result.reason or "Turn blocked by coherence fabric."
    return response_trace


def _build_chat_coherence_block_payload(session, session_id, response_trace: dict):
    """Governed chat block when coherence fabric hard-block applies."""
    return {
        "blocked_by": "coherence_fabric",
        "error": response_trace.get("error"),
        "coherence_protocol": response_trace.get("coherence_protocol"),
        "governed_pipeline": response_trace.get("governed_pipeline"),
        "response_trace": response_trace,
        **_build_chat_runtime_payload(session, session_id),
    }


def _coherence_block_http_response(session, session_id, response_trace: dict):
    """Record blocked turn state and return Flask response tuple."""
    _transition_session_state(
        session,
        "degraded",
        summary="Jarvis blocked the turn because coherence fabric is not aligned.",
        reason="coherence_fabric_blocked",
        event_type="turn_blocked",
        payload={
            "error": response_trace.get("error"),
            "coherence_protocol": response_trace.get("coherence_protocol"),
        },
    )
    session.metadata["response_trace"] = response_trace
    return (
        jsonify(_build_chat_coherence_block_payload(session, session_id, response_trace)),
        403,
    )


def _current_cognitive_bridge(session) -> dict | None:
    """Return the most recent routed bridge packet for this session, when present."""
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return None
    payload = metadata.get("cognitive_bridge")
    if isinstance(payload, dict) and payload:
        return dict(payload)
    return None


def _bridge_block_message(bridge_result: dict | None, default: str) -> str:
    """Render one concise operator-facing bridge block message."""
    payload = dict(bridge_result or {})
    reason_codes = list(payload.get("reason_codes") or [])
    if "jarvis_detachment_guard_blocked" in reason_codes:
        return (
            "Cognitive Bridge sealed Jarvis inside AAIS because the ingress was not "
            "an approved AAIS boundary."
        )
    if "approval_missing_for_effectful_execution" in reason_codes:
        return "Cognitive Bridge blocked execution because explicit approval was missing."
    if "model_only_source_cannot_execute" in reason_codes:
        return "Cognitive Bridge blocked execution because model-only sources cannot authorize action."
    if "governed_event_blocked" in reason_codes:
        return "Cognitive Bridge blocked execution because the invariant gate did not clear the packet."
    return default


def _route_session_turn_to_bridge(
    session,
    *,
    user_message: str,
    request_payload: dict | None,
    response_mode: str,
    bridge_route: str | None = None,
    bridge_surface: str | None = None,
) -> dict:
    """Route the active user turn through the shared cognitive bridge before work continues."""
    payload = dict(request_payload or {})
    route_label = str(bridge_route or payload.pop("_bridge_route", "") or "").strip() or "api.chat.sessions.message"
    surface_label = str(bridge_surface or payload.pop("_bridge_surface", "") or "").strip()
    if not surface_label:
        if route_label == "api.chat.sessions.stream":
            surface_label = "jarvis_chat_stream"
        elif route_label == "api.jarvis.compat":
            surface_label = "jarvis_compat"
        else:
            surface_label = "jarvis_chat"
    external_details = _extract_external_suggestion_details(payload)
    risk = "medium" if _is_action_approval_message(user_message) or detect_otem(user_message) else "low"
    bridge_result = cognitive_bridge_service.route_to_bridge(
        {
            "source": "chat_session",
            "type": "operator_turn",
            "payload": {
                "session_id": session.session_id,
                "message_preview": _clip_trace_text(user_message, limit=220),
                "persona_mode": session.metadata.get("persona_mode"),
                "response_mode": response_mode,
                "use_research": payload.get("use_research"),
                "loaded_session_archive": bool(payload.get("loaded_session_archive")),
                "requested_specialists": list(payload.get("requested_specialists") or []),
                "requested_specialist_preset": payload.get("requested_specialist_preset"),
                "execution_intent": "respond",
                "bridge_attestation": build_bridge_attestation(
                    ingress="chat_session",
                    surface=surface_label,
                    source_id=session.session_id,
                    route=route_label,
                    intent="respond",
                    runtime_context="live_runtime",
                    packet_type="operator_turn",
                    runtime_dir=cognitive_bridge_service.detachment_guard.runtime_dir,
                ),
                **{
                    key: payload.get(key)
                    for key in (
                        "detach_from_aais",
                        "run_outside_aais",
                        "standalone_jarvis",
                        "bridge_bypass",
                        "governance_disabled",
                    )
                    if key in payload
                },
                **external_details,
            },
            "requires_approval": False,
            "risk": risk,
        },
        runtime_context="live_runtime",
    )
    session.metadata["cognitive_bridge"] = bridge_result
    return bridge_result


def _route_action_execution_to_bridge(
    session,
    *,
    action_id: str,
    action: dict | None,
    approval_source: str,
) -> dict:
    """Route one approved runtime action through the shared bridge before execution."""
    normalized_action_id = " ".join(str(action_id or "").replace("-", "_").split()).strip().lower()
    action_payload = dict(action or {})
    external_details = _extract_external_suggestion_details(action_payload)
    repo_change = normalized_action_id == "apply_patch_review"
    bridge_result = cognitive_bridge_service.route_to_bridge(
        {
            "source": "api_action",
            "type": "repo_change_execute" if repo_change else "runtime_action_execute",
            "payload": {
                "session_id": session.session_id,
                "action_id": normalized_action_id,
                "action_label": action_payload.get("label"),
                "repo_change": repo_change,
                "approval_granted": True,
                "approval_source": approval_source,
                "verification_required": True if repo_change else False,
                "execution_intent": "execute",
                "bridge_attestation": build_bridge_attestation(
                    ingress="api_action",
                    surface="jarvis_action_execution",
                    source_id=session.session_id,
                    route="api.chat.sessions.actions.execute",
                    intent="execute",
                    runtime_context="operator_runtime",
                    packet_type="repo_change_execute" if repo_change else "runtime_action_execute",
                    runtime_dir=cognitive_bridge_service.detachment_guard.runtime_dir,
                ),
                **external_details,
            },
            "requires_approval": True if repo_change else False,
            "risk": "high" if repo_change else "medium",
        },
        runtime_context="operator_runtime",
    )
    session.metadata["cognitive_bridge"] = bridge_result
    return bridge_result


def _cognitive_bridge_reject_reason(bridge_result: dict) -> str:
    """Map bridge block reason_codes to explicit Wonder/RLS reject reasons."""
    codes = set(bridge_result.get("reason_codes") or [])
    if "wonder_forbidden" in codes:
        return "wonder_forbidden"
    rls_verdict = bridge_result.get("rls_verdict") or {}
    if "rls_rejected" in codes or str(rls_verdict.get("verdict") or "") == "reject":
        return "rls_rejected"
    return "cognitive_bridge_blocked"


def _route_reasoning_ingress_to_bridge(raw_packet: dict | None, *, runtime_context: str) -> dict:
    """Route a reasoning ingress envelope through the shared bridge before protocol evaluation."""
    packet = dict(raw_packet or {})
    meta = dict(packet.get("meta") or {})
    exchange_payload = dict(packet.get("payload") or {})
    return cognitive_bridge_service.route_to_bridge(
        {
            "source": str(meta.get("source") or "reasoning_exchange"),
            "type": "reasoning_packet_ingress",
            "payload": {
                "packet_id": packet.get("id"),
                "packet_version": packet.get("version"),
                "packet_type": packet.get("type"),
                "domain": meta.get("domain"),
                "tags": list(meta.get("tags") or []),
                "payload_present": bool(packet.get("payload")),
                "claim": str(exchange_payload.get("claim") or "").strip(),
                "reasoning": str(exchange_payload.get("reasoning") or "").strip(),
                "evidence": list(exchange_payload.get("evidence") or []),
                "confidence": exchange_payload.get("confidence"),
                "execution_intent": "evaluate",
                "bridge_attestation": build_bridge_attestation(
                    ingress="reasoning_exchange",
                    surface="reasoning_protocol",
                    source_id=str(packet.get("id") or "") or None,
                    route="api.reasoning.evaluate",
                    intent="evaluate",
                    runtime_context=runtime_context,
                    packet_type="reasoning_packet_ingress",
                    runtime_dir=cognitive_bridge_service.detachment_guard.runtime_dir,
                ),
            },
            "requires_approval": False,
            "risk": "medium",
        },
        runtime_context=runtime_context,
    )


def _hydrate_jarvis_context(
    session,
    user_message: str,
    response_mode: str = "fast",
    use_research: bool | None = None,
    requested_specialists=None,
    requested_specialist_preset=None,
):
    """Attach memory, workspace, and optional research based on the response mode."""
    normalized_mode = normalize_response_mode(response_mode)
    previous_governed_pipeline = _previous_governed_pipeline(session)
    contract = RESPONSE_MODE_CONTRACTS[normalized_mode]
    mission_context = session.metadata.get("mission_board") or _attach_session_mission_context(session)
    context_priority_guard = build_current_turn_priority_guard(
        user_message,
        mission_context=mission_context,
        current_goal=session.spiral_state.current_goal,
    )
    session.metadata["context_priority_guard"] = dict(context_priority_guard)
    turn_current_goal = " ".join(
        str(
            context_priority_guard.get("effective_goal")
            or session.spiral_state.current_goal
            or ""
        ).split()
    ).strip() or session.spiral_state.current_goal
    session.metadata["turn_current_goal"] = turn_current_goal
    steps = []
    if context_priority_guard.get("mission_active"):
        if context_priority_guard.get("allow_active_problem_context"):
            steps.append(
                "Current-turn priority guard allowed the active tracked problem to bind because the operator explicitly resumed it."
            )
        elif context_priority_guard.get("status") == "answer_first":
            steps.append(
                "Current-turn priority guard kept the active tracked problem in reserve so Jarvis answers the present request directly before resuming older troubleshooting."
            )
        elif context_priority_guard.get("status") == "suppressed":
            steps.append(
                "Current-turn priority guard left the active tracked problem in reserve because this turn did not explicitly resume it."
            )
    companion_profile = _get_companion_surface_profile(
        persona_mode=session.metadata.get("persona_mode"),
        response_mode=normalized_mode,
    )
    if companion_profile or _session_uses_companion_lane(session):
        companion_profile = companion_profile or _get_companion_surface_profile(
            persona_mode=session.metadata.get("persona_mode"),
            response_mode=session.metadata.get("response_mode"),
        ) or COMPANION_SURFACE_PROFILES["tiny_nova"]
        session.metadata["prompt_lane"] = None
        session.metadata["specialist_profile"] = None
        session.metadata["writing_focus"] = None
        raw_companion_memories = jarvis_operator.memory_enforcer.get_relevant_memories(
            user_message,
            limit=contract["memory_limit"],
            runtime_context="live_runtime",
        )
        unique_companion_memories = dedupe_memory_cues(raw_companion_memories)
        session.metadata["persistent_memories"] = filter_companion_persistent_memories(
            unique_companion_memories,
            limit=contract["memory_limit"],
        )
        session.metadata["memory_cue_trace"] = {
            "retrieved": len(raw_companion_memories),
            "unique": len(unique_companion_memories),
            "rendered": 0,
        }
        session.metadata["workspace_context"] = None
        session.metadata["live_research"] = None
        session.metadata["urg_library_context"] = None
        session.metadata["corrigibility_prompt_block"] = None
        session.metadata["continuity_profile"] = dict(companion_profile["continuity_profile"])
        session.metadata["continuity_prompt_block"] = None
        memory_count = len(session.metadata["persistent_memories"])
        filtered_memory_count = max(0, len(unique_companion_memories) - memory_count)
        if memory_count:
            steps.append(
                f"{companion_profile['label']} carried {memory_count} light continuity cue(s) "
                f"into this turn ({len(raw_companion_memories)} retrieved, {len(unique_companion_memories)} unique)."
            )
        else:
            steps.append(f"{companion_profile['label']} answered from the present moment without pulling extra continuity cues.")
        if filtered_memory_count:
            steps.append(
                f"{companion_profile['label']} filtered {filtered_memory_count} system-facing continuity cue(s) before reply generation."
            )
        loaded_archive = session.metadata.get("loaded_session_archive") or {}
        if loaded_archive.get("id") or loaded_archive.get("title"):
            steps.append(
                f"{companion_profile['label']} received the user-opened session archive "
                f"'{loaded_archive.get('title') or 'Saved Nova session'}' as document context."
            )

        god_brain = build_god_brain_trace(
            user_message=user_message,
            response_mode=normalized_mode,
            current_goal=turn_current_goal,
            contract=contract["contract"],
            specialist_profile=None,
            specialist_preset=None,
            requested_specialists=[],
            memory_count=memory_count,
            workspace_hits=0,
            research_sources=0,
            policy_status=session.metadata.get("policy_status"),
            mode_guidance=session.metadata.get("mode_guidance"),
        )
        session.metadata["god_brain"] = god_brain
        steps.append(god_brain["summary"])
        provider_mind = _resolve_provider_mind(session, user_message, normalized_mode)
        if provider_mind:
            steps.append(
                provider_mind.get(
                    "summary",
                    f"ProviderMind kept the turn on the {companion_profile['label']} path.",
                )
            )
        model_route = resolve_model_route(
            response_mode=normalized_mode,
            specialist_profile=None,
            specialist_preset=None,
            god_brain=god_brain,
            workspace_hits=0,
            research_sources=0,
            policy_status=session.metadata.get("policy_status"),
            preferred_provider=session.metadata.get("preferred_provider"),
            provider_available=provider_registry.can_invoke,
        )
        session.metadata["model_route"] = model_route
        steps.append(
            f"Model route {model_route['label']} selected for {model_route['reason'].replace('_', ' ')}."
        )
        provider_notice = _build_provider_notice(session)
        if provider_notice:
            steps.append(provider_notice["summary"])
            _record_session_event(
                session,
                "provider_fallback",
                provider_notice["summary"],
                payload=provider_notice,
            )
        governed_pipeline = _build_governed_pipeline_trace(
            normalized_mode,
            contract["contract"],
            god_brain=god_brain,
            model_route=model_route,
            turn_contract=session.metadata.get("turn_contract"),
            previous_pipeline=previous_governed_pipeline,
            operator_text=user_message,
        )
        return {
            "mode": normalized_mode,
            "contract": contract["contract"],
            "contract_label": contract["label"],
            "summary": contract["summary"],
            "memory_count": memory_count,
            "workspace_hits": 0,
            "workspace_files": 0,
            "research_sources": 0,
            "research_reason": "tiny_default_local",
            "specialist_domain": None,
            "specialist_focus": None,
            "specialist_selection_source": None,
            "specialist_summary": None,
            "specialist_lenses": [],
            "specialist_profile": None,
            "requested_specialists": [],
            "specialist_preset": None,
            "writing_focus": None,
            "continuity_profile": session.metadata["continuity_profile"],
            "provider_mind": provider_mind,
            "model_route": model_route,
            "god_brain": god_brain,
            "cognitive_bridge": _current_cognitive_bridge(session),
            "governed_pipeline": governed_pipeline,
            "memory_cues": dict(session.metadata.get("memory_cue_trace") or {}),
            "context_priority_guard": context_priority_guard,
            "plan_summary": None,
            "steps": steps,
            "reasoning_objective": contract["contract"],
        }

    continuity_profile = _build_continuity_profile(session)
    steps.append(
        f"Continuity profile loaded with tone {continuity_profile.get('tone', 'concise')} and {len(continuity_profile.get('known_projects') or [])} known project anchors."
    )
    loaded_archive = session.metadata.get("loaded_session_archive") or {}
    if loaded_archive.get("id") or loaded_archive.get("title"):
        steps.append(
            f"Loaded the user-opened session archive '{loaded_archive.get('title') or 'Saved Nova session'}' as explicit document context."
        )
    objective = detect_objective(user_message)
    direct_challenge_turn = objective == "handle_direct_challenge"
    relational_question_turn = objective == "answer_relational_question"
    expanded_specialists, specialist_preset = expand_requested_specialists(
        requested_specialists
        if requested_specialists is not None
        else session.metadata.get("requested_specialists"),
        preset_id=(
            requested_specialist_preset
            if requested_specialist_preset is not None
            else session.metadata.get("requested_specialist_preset")
        ),
    )
    requested_specialists = expanded_specialists
    if direct_challenge_turn or relational_question_turn:
        challenge_profile = analyze_direct_challenge(user_message) if direct_challenge_turn else {}
        relational_profile = (
            analyze_relational_question(user_message) if relational_question_turn else {}
        )
        session.metadata["prompt_lane"] = "relational"
        session.metadata["specialist_profile"] = None
        session.metadata["requested_specialists"] = requested_specialists
        session.metadata["requested_specialist_preset"] = (
            specialist_preset.get("id") if specialist_preset else None
        )
        session.metadata["writing_focus"] = None
        session.metadata["persistent_memories"] = []
        session.metadata["memory_cue_trace"] = {"retrieved": 0, "unique": 0, "rendered": 0}
        session.metadata["workspace_context"] = None
        session.metadata["live_research"] = None
        session.metadata["urg_library_context"] = None
        if direct_challenge_turn:
            steps.append(
                "Direct challenge detected. Jarvis stayed in a relational lane and suspended writing-domain routing for this turn."
            )
            if challenge_profile.get("severity") not in {None, "", "none"}:
                steps.append(
                    f"Direct challenge intensity classified as {challenge_profile['severity']}."
                )
        else:
            steps.append(
                "Relational Jarvis-state question detected. Jarvis stayed on a personal-response lane and suspended repo, memory, and research routing for this turn."
            )
            if relational_profile.get("matched_pattern"):
                steps.append(
                    f"Relational wording matched {relational_profile['matched_pattern']}."
                )
        god_brain = build_god_brain_trace(
            user_message=user_message,
            response_mode=normalized_mode,
            current_goal=turn_current_goal,
            contract=contract["contract"],
            specialist_profile=None,
            specialist_preset=None,
            requested_specialists=[],
            memory_count=0,
            workspace_hits=0,
            research_sources=0,
            policy_status=session.metadata.get("policy_status"),
            mode_guidance=session.metadata.get("mode_guidance"),
        )
        session.metadata["god_brain"] = god_brain
        steps.append(god_brain["summary"])
        provider_mind = _resolve_provider_mind(session, user_message, normalized_mode)
        if provider_mind:
            steps.append(provider_mind.get("summary", "ProviderMind selected the engine path for this turn."))
        model_route = resolve_model_route(
            response_mode=normalized_mode,
            specialist_profile=None,
            specialist_preset=None,
            god_brain=god_brain,
            workspace_hits=0,
            research_sources=0,
            policy_status=session.metadata.get("policy_status"),
            preferred_provider=session.metadata.get("preferred_provider"),
            provider_available=provider_registry.can_invoke,
        )
        session.metadata["model_route"] = model_route
        steps.append(
            f"Model route {model_route['label']} selected for {model_route['reason'].replace('_', ' ')}."
        )
        provider_notice = _build_provider_notice(session)
        if provider_notice:
            steps.append(provider_notice["summary"])
            _record_session_event(
                session,
                "provider_fallback",
                provider_notice["summary"],
                payload=provider_notice,
            )
        governed_pipeline = _build_governed_pipeline_trace(
            normalized_mode,
            contract["contract"],
            god_brain=god_brain,
            model_route=model_route,
            turn_contract=session.metadata.get("turn_contract"),
            previous_pipeline=previous_governed_pipeline,
            operator_text=user_message,
        )
        return {
            "mode": normalized_mode,
            "contract": contract["contract"],
            "contract_label": contract["label"],
            "summary": (
                "Jarvis answered a direct challenge without drifting into writing or meta lanes."
                if direct_challenge_turn
                else "Jarvis answered a relational question without pulling repo, memory, or research context into the reply."
            ),
            "memory_count": 0,
            "workspace_hits": 0,
            "workspace_files": 0,
            "research_sources": 0,
            "research_reason": "not_needed",
            "specialist_domain": None,
            "specialist_focus": None,
            "specialist_selection_source": None,
            "specialist_summary": None,
            "specialist_lenses": [],
            "specialist_profile": None,
            "requested_specialists": requested_specialists,
            "specialist_preset": specialist_preset,
            "writing_focus": None,
            "continuity_profile": continuity_profile,
            "provider_mind": provider_mind,
            "model_route": model_route,
            "god_brain": god_brain,
            "cognitive_bridge": _current_cognitive_bridge(session),
            "governed_pipeline": governed_pipeline,
            "memory_cues": dict(session.metadata.get("memory_cue_trace") or {}),
            "context_priority_guard": context_priority_guard,
            "direct_challenge_profile": challenge_profile if direct_challenge_turn else None,
            "relational_question_profile": relational_profile if relational_question_turn else None,
            "plan_summary": None,
            "steps": steps,
            "reasoning_objective": objective,
        }

    auto_specialist_profile = detect_specialist_profile(user_message, current_mode=normalized_mode)
    session.metadata["prompt_lane"] = None
    specialist_profile = merge_requested_specialists(
        auto_specialist_profile,
        requested_specialists=requested_specialists,
        current_mode=normalized_mode,
    )
    writing_focus = profile_to_writing_focus(specialist_profile) or detect_writing_focus(
        user_message,
        current_mode=normalized_mode,
    )
    session.metadata["specialist_profile"] = specialist_profile
    session.metadata["requested_specialists"] = requested_specialists
    session.metadata["requested_specialist_preset"] = (
        specialist_preset.get("id") if specialist_preset else None
    )
    session.metadata["writing_focus"] = writing_focus

    raw_memories = jarvis_operator.memory_enforcer.get_relevant_memories(
        user_message,
        limit=contract["memory_limit"],
        runtime_context="live_runtime",
    )
    session.metadata["persistent_memories"] = dedupe_memory_cues(raw_memories)
    session.metadata["memory_cue_trace"] = {
        "retrieved": len(raw_memories),
        "unique": len(session.metadata["persistent_memories"]),
        "rendered": 0,
    }
    memory_count = len(session.metadata["persistent_memories"])
    if memory_count:
        steps.append(
            f"Loaded {len(raw_memories)} relevant long-term memories "
            f"({memory_count} unique after dedupe)."
        )
    else:
        steps.append("No long-term memory cues were needed for this turn.")

    workspace_context = jarvis_operator.build_workspace_context(
        user_message,
        result_limit=contract["workspace_result_limit"],
        file_limit=contract["workspace_file_limit"],
        file_chars=contract["workspace_file_chars"],
        reason=contract["workspace_reason"],
        auto_attached=contract["workspace_auto_attached"],
        force=contract["workspace_strategy"] == "force",
        query_hint=contract.get("workspace_query_hint"),
    )
    session.metadata["workspace_context"] = workspace_context
    workspace_hits = len((session.metadata["workspace_context"] or {}).get("results", []))
    workspace_files = len((session.metadata["workspace_context"] or {}).get("files", []))
    if workspace_hits:
        steps.append(
            f"Attached {workspace_hits} workspace matches with {workspace_files} file previews."
        )
    else:
        steps.append("No workspace context was attached.")
    if specialist_profile:
        lens_labels = ", ".join(
            specialist.get("label", "")
            for specialist in specialist_profile.get("specialists", [])[:5]
            if specialist.get("label")
        )
        steps.append(
            f"Activated {specialist_profile['domain']} specialists for "
            f"{specialist_profile['focus'].replace('_', ' ')}"
            f"{': ' + lens_labels if lens_labels else '.'}"
        )
        if specialist_profile.get("selection_source") in {"manual", "hybrid"}:
            steps.append(
                "Pinned specialist selection was applied for this turn: "
                + ", ".join(
                    specialist.get("label", "")
                    for specialist in specialist_profile.get("specialists", [])
                    if specialist.get("source") == "manual"
                )
                + "."
            )
    if specialist_preset:
        steps.append(
            f"Applied specialist preset {specialist_preset['label']} for this turn."
        )

    should_research, research_reason = _should_attach_live_research(
        user_message,
        normalized_mode,
        use_research=use_research,
    )

    if should_research:
        try:
            session.metadata["live_research"] = web_researcher.research(user_message)
        except Exception as exc:
            logger.warning(f"Live research failed for '{user_message[:80]}': {exc}")
            session.metadata["live_research"] = None
            research_reason = "research_failed"
            steps.append("Live research was attempted but no sources could be loaded.")
    else:
        session.metadata["live_research"] = None

    research_sources = len((session.metadata["live_research"] or {}).get("sources", []))
    if research_sources:
        steps.append(f"Loaded {research_sources} live research sources.")
    elif research_reason == "disabled":
        steps.append("Live research was explicitly turned off for this turn.")
    elif research_reason == "fast_default_local":
        steps.append("Fast mode skipped live research unless explicitly requested.")
    elif research_reason == "builder_default_local":
        steps.append("Builder mode stayed local-first unless live research was explicitly requested.")
    elif research_reason == "operator_default_local":
        steps.append("Operator mode stayed local-first unless live research was explicitly requested.")
    elif research_reason == "research_default_on":
        steps.append("Research mode pulled fresh sources by default for this turn.")

    try:
        session.metadata["urg_library_context"] = build_urg_library_context(query=user_message)
    except Exception as exc:
        logger.warning(f"URG library context failed for '{user_message[:80]}': {exc}")
        session.metadata["urg_library_context"] = None

    urg_entries = int((session.metadata.get("urg_library_context") or {}).get("entry_count") or 0)
    if urg_entries:
        steps.append(f"Attached {urg_entries} URG library entries.")

    summary = contract["summary"]
    if specialist_profile:
        summary = f"{summary} {specialist_profile['summary']}"

    god_brain = build_god_brain_trace(
        user_message=user_message,
        response_mode=normalized_mode,
        current_goal=turn_current_goal,
        contract=contract["contract"],
        specialist_profile=specialist_profile,
        specialist_preset=specialist_preset,
        requested_specialists=requested_specialists,
        memory_count=memory_count,
        workspace_hits=workspace_hits,
        research_sources=research_sources,
        policy_status=session.metadata.get("policy_status"),
        mode_guidance=session.metadata.get("mode_guidance"),
        **_god_brain_bridge_kwargs(session),
    )
    session.metadata["god_brain"] = god_brain
    steps.append(god_brain["summary"])
    provider_mind = _resolve_provider_mind(session, user_message, normalized_mode)
    if provider_mind:
        steps.append(provider_mind.get("summary", "ProviderMind selected the engine path for this turn."))
    model_route = resolve_model_route(
        response_mode=normalized_mode,
        specialist_profile=specialist_profile,
        specialist_preset=specialist_preset,
        god_brain=god_brain,
        workspace_hits=workspace_hits,
        research_sources=research_sources,
        policy_status=session.metadata.get("policy_status"),
        preferred_provider=session.metadata.get("preferred_provider"),
        provider_available=provider_registry.can_invoke,
    )
    session.metadata["model_route"] = model_route
    steps.append(
        f"Model route {model_route['label']} selected for {model_route['reason'].replace('_', ' ')}."
    )
    provider_notice = _build_provider_notice(session)
    if provider_notice:
        steps.append(provider_notice["summary"])
        _record_session_event(
            session,
            "provider_fallback",
            provider_notice["summary"],
            payload=provider_notice,
        )
    governed_pipeline = _build_governed_pipeline_trace(
        normalized_mode,
        contract["contract"],
        god_brain=god_brain,
        model_route=model_route,
        turn_contract=session.metadata.get("turn_contract"),
        previous_pipeline=previous_governed_pipeline,
        operator_text=user_message,
    )

    return {
        "mode": normalized_mode,
        "contract": contract["contract"],
        "contract_label": contract["label"],
        "summary": summary,
        "memory_count": memory_count,
        "workspace_hits": workspace_hits,
        "workspace_files": workspace_files,
        "research_sources": research_sources,
        "research_reason": research_reason,
        "specialist_domain": specialist_profile.get("domain") if specialist_profile else None,
        "specialist_focus": specialist_profile.get("focus") if specialist_profile else None,
        "specialist_selection_source": specialist_profile.get("selection_source") if specialist_profile else None,
        "specialist_summary": specialist_profile.get("summary") if specialist_profile else None,
        "specialist_lenses": specialist_profile.get("specialists", []) if specialist_profile else [],
        "specialist_profile": specialist_profile,
        "requested_specialists": requested_specialists,
        "specialist_preset": specialist_preset,
        "writing_focus": writing_focus,
        "continuity_profile": continuity_profile,
        "provider_mind": provider_mind,
        "model_route": model_route,
        "god_brain": god_brain,
        "cognitive_bridge": _current_cognitive_bridge(session),
        "governed_pipeline": governed_pipeline,
        "memory_cues": dict(session.metadata.get("memory_cue_trace") or {}),
        "context_priority_guard": context_priority_guard,
        "plan_summary": None,
        "steps": steps,
        "reasoning_objective": detect_objective(
            user_message,
            workspace_context=session.metadata.get("workspace_context"),
            action_lifecycle=session.metadata.get("action_lifecycle"),
            specialist_profile=specialist_profile,
        ),
    }


def _build_tool_response_trace(
    response_mode: str,
    tool_result=None,
    god_brain=None,
    model_route=None,
    provider_mind=None,
    specialist_preset=None,
    action_lifecycle=None,
    turn_contract=None,
    session=None,
    cognitive_bridge=None,
    runtime_context: str = "live_runtime",
    operator_text: str | None = None,
):
    """Describe a direct tool-style turn that skipped model generation."""
    normalized_mode = _resolve_direct_tool_response_mode(response_mode, tool_result)
    action = (tool_result or {}).get("action") or {}
    tool_type = (tool_result or {}).get("type") or "tool"
    reasoning_objective = "run_otem" if tool_type == "otem" else None
    capability_bridge = dict((tool_result or {}).get("capability") or {})
    summary = "A direct Jarvis tool handled this request without using the text model."
    steps = ["Handled this turn through a direct Jarvis tool path."]
    if tool_type == "action_result" and action.get("label"):
        summary = f"{action['label']} ran as a direct operator action without a second model pass."
    elif tool_type == "action_request" and action.get("label"):
        summary = f"{action['label']} was proposed directly and is waiting on approval."
    elif tool_type == "corrigibility":
        summary = (
            (tool_result or {}).get("summary")
            or "Jarvis handled an explicit operator correction without using the text model."
        )
    # Append contractor usage to the main Jarvis response trace for observability
    via = (tool_result or {}).get("via")
    if via and "live_" in str(via):
        steps.append(f"Contractor handoff: {via} (see tool_result for job details and results).")
    elif tool_type == "memory_rejection":
        summary = "Jarvis rejected the requested memory write and kept live canonical memory unchanged."
        rejection = (tool_result or {}).get("memory_rejection") or {}
        steps = [
            "Memory governance rejected the requested write.",
            f"Reason: {_memory_rejection_reason_text(rejection.get('reason'))}.",
        ]
    elif tool_type == "memory_rejection_followup":
        summary = "Jarvis clarified that the rejected memory request never entered canonical memory."
        steps = [
            "No conflicting canonical memory was admitted from the rejected request.",
        ]
    elif tool_type == "otem":
        otem = dict((tool_result or {}).get("otem") or {})
        plan = list(otem.get("plan") or [])
        summary = "Jarvis produced a deterministic OTEM plan without model generation or side effects."
        steps = [
            "OTEM stayed inside the operator-task lane.",
            f"Built {len(plan)} bounded planning step(s) without taking action.",
        ]
    elif tool_type == "forge_result":
        forge_payload = dict((tool_result or {}).get("forge") or {})
        forge_context = dict(forge_payload.get("forge_context") or {})
        summary = "Jarvis routed the turn through Forge because the operator explicitly requested Forge execution."
        steps = [
            "Forge execution was explicitly requested by the operator.",
            f"Attached {int(forge_context.get('file_count') or 0)} workspace file preview(s) to the contractor envelope.",
        ]
    elif tool_type == "forge_error":
        forge_payload = dict((tool_result or {}).get("forge") or {})
        summary = "Jarvis kept the turn on the Forge path and surfaced the contractor routing failure directly."
        steps = [
            "Forge execution was explicitly requested by the operator.",
            f"Forge routing failed: {_clip_trace_text(forge_payload.get('error'), limit=180)}",
        ]
    elif tool_type == "lane_guardrail":
        lane_guardrail = dict((tool_result or {}).get("lane_guardrail") or {})
        summary = (
            (tool_result or {}).get("summary")
            or "Jarvis blocked a lane transition that violated the active routing guardrails."
        )
        steps = [
            f"Active lane: {lane_guardrail.get('active_lane', 'JARVIS')}.",
            f"Requested lane: {lane_guardrail.get('requested_lane', 'FORGE')}.",
            f"Decision: {lane_guardrail.get('reason', 'lane_guardrail')}.",
        ]
    elif tool_type == "external_suggestion_guardrail":
        admission = dict((tool_result or {}).get("external_suggestion_admission") or {})
        summary = (
            (tool_result or {}).get("summary")
            or "Jarvis blocked raw external adoption in ordinary conversation."
        )
        steps = [
            "Freeform chat detected an outside proposal with adoption intent.",
            "Decision: external suggestion admission blocked raw adoption until the law filter and admitted form are present.",
        ]
        if admission.get("law_filter_applied"):
            steps.append("Law filter is present, but the admitted form is still missing.")
    if capability_bridge.get("module"):
        provider = capability_bridge.get("provider") or "unknown_provider"
        module = capability_bridge.get("module")
        action_name = capability_bridge.get("action") or "execute"
        if capability_bridge.get("ok") is False and capability_bridge.get("error_type"):
            steps.append(
                f"Capability bridge returned {capability_bridge['error_type']} from {module}.{action_name} via {provider}."
            )
        else:
            steps.append(
                f"Capability bridge routed {tool_type} through {module}.{action_name} via {provider}."
            )
    if action_lifecycle:
        stage = action_lifecycle.get("stage")
        if stage == "proposed" and action.get("label"):
            summary = f"{action['label']} was proposed and is explicitly waiting on approval."
        elif stage == "approved" and action.get("label"):
            summary = f"{action['label']} was approved and is moving straight into execution."
        elif stage == "executed" and action.get("label"):
            summary = f"{action['label']} executed successfully through the direct operator lane."
        elif stage == "failed" and action.get("label"):
            summary = f"{action['label']} executed but failed in the direct operator lane."
        elif stage == "blocked" and action.get("label"):
            summary = f"{action['label']} was approved but blocked by policy before execution."
        steps = [
            (
                "Action lifecycle is "
                f"{stage} (approval: {action_lifecycle.get('approval_state')}, "
                f"execution: {action_lifecycle.get('execution_state')})."
            )
        ]
    governed_pipeline = _build_governed_pipeline_trace(
        normalized_mode,
        "direct_tool",
        god_brain=god_brain,
        model_route=model_route,
        tool_result=tool_result,
        turn_contract=turn_contract,
        runtime_context=runtime_context,
        previous_pipeline=_previous_governed_pipeline(session),
        operator_text=operator_text,
    )

    trace = {
        "mode": normalized_mode,
        "contract": "direct_tool",
        "contract_label": "direct tool",
        "summary": summary,
        "memory_count": 0,
        "workspace_hits": 0,
        "workspace_files": 0,
        "research_sources": 0,
        "research_reason": "not_used",
        "specialist_domain": None,
        "specialist_focus": None,
        "specialist_selection_source": None,
        "specialist_summary": None,
        "specialist_lenses": [],
        "specialist_profile": None,
        "requested_specialists": [],
        "specialist_preset": specialist_preset,
        "writing_focus": None,
        "model_route": model_route,
        "provider_mind": provider_mind,
        "god_brain": god_brain,
        "cognitive_bridge": cognitive_bridge or _current_cognitive_bridge(session),
        "governed_pipeline": governed_pipeline,
        "capability_bridge": capability_bridge or None,
        "memory_cues": dict(((session.metadata if session else {}) or {}).get("memory_cue_trace") or {}),
        "plan_summary": None,
        "steps": steps,
        "action_lifecycle": action_lifecycle,
        "turn_contract": turn_contract,
        "reasoning_objective": reasoning_objective,
    }
    return _apply_coherence_guard_to_response_trace(trace)


def _build_mode_plan(session, response_mode: str, model=None, max_length=None):
    """Build a compact structured plan before the final answer for richer operating modes."""
    del model, max_length

    normalized_mode = normalize_response_mode(response_mode)
    workspace_context = session.metadata.get("workspace_context") or {}
    live_research = session.metadata.get("live_research") or {}
    persistent_memories = dedupe_memory_cues(session.metadata.get("persistent_memories") or [])
    specialist_profile = session.metadata.get("specialist_profile") or {}
    specialist_preset = session.metadata.get("requested_specialist_preset")
    god_brain = session.metadata.get("god_brain") or {}
    model_route = session.metadata.get("model_route") or {}

    workspace_paths = [
        result.get("relative_path", "")
        for result in workspace_context.get("results", [])[:3]
        if result.get("relative_path")
    ]
    source_titles = [
        f"[{source.get('id')}] {source.get('title', '')}".strip()
        for source in live_research.get("sources", [])[:3]
        if source.get("title")
    ]
    evidence_parts = []
    if workspace_paths:
        evidence_parts.append(f"workspace: {', '.join(workspace_paths)}")
    if source_titles:
        evidence_parts.append(f"research: {', '.join(source_titles)}")
    if persistent_memories:
        evidence_parts.append(f"memory: {len(persistent_memories[:2])} long-term cue(s) loaded")
    if not evidence_parts:
        evidence_parts.append("reason from the conversation itself and keep the answer practical.")

    specialist_summary = None
    if specialist_profile.get("specialists"):
        specialist_summary = (
            f"{specialist_profile.get('domain', 'general')} / "
            f"{specialist_profile.get('focus', 'manual_selection')}: "
            + ", ".join(
                specialist.get("label", "")
                for specialist in specialist_profile.get("specialists", [])[:4]
                if specialist.get("label")
            )
        )
    elif specialist_preset:
        specialist_summary = f"preset:{specialist_preset}"

    answer_shapes = {
        "think": (
            "Lead with the recommendation, give 2-3 short supporting points, "
            "and finish with the next concrete step."
        ),
        "debug": (
            "Start with the likeliest break point, tie it to the strongest evidence, "
            "and end with the fastest verification or fix step."
        ),
        "builder": (
            "Lead with the smallest shippable slice, sequence the implementation briefly, "
            "and end with the next thing to build."
        ),
        "research": (
            "Lead with the strongest conclusion, compare options briefly, "
            "cite source numbers inline when used, and end with the recommendation."
        ),
        "operator": (
            "Lead with the current local state, name the safest next action, "
            "call out approvals if needed, and end with what to verify."
        ),
    }
    answer_shape = answer_shapes.get(
        normalized_mode,
        "Lead with the recommendation and end with the clearest next move.",
    )
    god_brain_line = None
    if god_brain:
        god_brain_line = (
            f"{god_brain.get('strategy_label', 'Sovereign Core')} | "
            f"lead={god_brain.get('lead', {}).get('label', 'Sovereign Core')} | "
            f"bias={god_brain.get('action_bias_label', 'answer directly')} | "
            f"arbiter={god_brain.get('arbiter', {}).get('rule', '')}"
        )
    model_route_line = None
    if model_route:
        model_route_line = (
            f"{model_route.get('label', 'Local Route')} | "
            f"reason={model_route.get('reason', 'turn_route')} | "
            f"summary={model_route.get('summary', '')}"
        )

    plan_lines = [
        f"Mode: {normalized_mode}",
        f"Focus: {session.spiral_state.current_goal}",
        f"Specialists: {specialist_summary or 'auto only'}",
    ]
    if god_brain_line:
        plan_lines.append(f"God Brain: {god_brain_line}")
    if model_route_line:
        plan_lines.append(f"Model Route: {model_route_line}")
    plan_lines.extend(
        [
            f"Evidence: {' | '.join(evidence_parts)}",
            f"Answer Shape: {answer_shape}",
        ]
    )
    plan_text = "\n".join(plan_lines)
    return _clip_trace_text(plan_text, limit=700) or None


def _mode_uses_plan(response_mode: str) -> bool:
    """Return whether this operating mode should take the planning pass."""
    normalized_mode = normalize_response_mode(response_mode)
    return bool(RESPONSE_MODE_CONTRACTS[normalized_mode].get("plan_enabled"))


def _plan_summary_to_hidden_guidance(plan_summary):
    """Compress verbose plan labels into one silent guidance string for the model."""
    extracted = {}
    for line in str(plan_summary or "").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        extracted[key.strip().lower()] = value.strip()

    guidance_parts = []
    if extracted.get("focus"):
        guidance_parts.append(f"Keep the answer centered on {extracted['focus']}.")
    if extracted.get("evidence"):
        guidance_parts.append(f"Ground the answer in this evidence: {extracted['evidence']}.")
    if extracted.get("answer shape"):
        guidance_parts.append(extracted["answer shape"])

    return " ".join(guidance_parts).strip() or None


def _extract_external_suggestion_details(payload: dict | None) -> dict:
    """Return one normalized external-suggestion law payload from request JSON."""
    data = dict(payload or {})
    details: dict = {}
    for key in (
        "external_suggestion",
        "external_suggestion_usage",
        "law_filter_applied",
        "admitted_external_form",
        "content_transfer_mode",
        "share_mode",
        "export_mode",
        "pattern_share_mode",
        "collective_share_mode",
        "copy_raw_external",
        "share_raw",
        "raw_export",
        "copy_raw",
        "copy_private_run",
        "share_private_run",
        "private_export",
        "raw_prompts",
        "raw_chat_logs",
        "raw_code",
        "raw_traces",
        "raw_documents",
    ):
        value = data.get(key)
        if value in (None, "", [], {}):
            continue
        if key == "law_filter_applied" and value is not True:
            continue
        details[key] = value
    return details


FREEFORM_EXTERNAL_SOURCE_HINTS = (
    "external suggestion",
    "external proposal",
    "external idea",
    "external architecture",
    "outside suggestion",
    "outside proposal",
    "outside idea",
    "outside architecture",
    "another model",
    "another assistant",
    "outside model",
    "someone suggested",
    "from a model",
    "from another model",
    "from another assistant",
)

FREEFORM_EXTERNAL_ADOPTION_HINTS = (
    "use this",
    "implement this",
    "make this part of aais",
    "make this part of the system",
    "apply this architecture",
    "apply this proposal",
    "convert this into system behavior",
    "convert this into runtime behavior",
    "adopt this",
    "build this in",
    "wire this in",
)

FREEFORM_EXTERNAL_COMPARISON_HINTS = (
    "compare this",
    "pressure-test this",
    "pressure test this",
    "critique this",
    "review this",
    "analyze this",
    "check this against",
    "what do you think of this",
)

FREEFORM_EXTERNAL_INSPIRATION_HINTS = (
    "use this as inspiration",
    "inspired by this",
    "borrow from this",
)


def _match_freeform_external_hints(normalized_text: str, hints: tuple[str, ...]) -> list[str]:
    """Return matched deterministic hint phrases for one normalized freeform turn."""
    matches: list[str] = []
    for hint in hints:
        if hint in normalized_text and hint not in matches:
            matches.append(hint)
    return matches


def _infer_freeform_external_suggestion_details(user_message: str) -> dict:
    """Infer bounded external-suggestion law metadata from an ordinary chat turn."""
    normalized = " ".join(str(user_message or "").lower().split())
    if not normalized:
        return {}

    source_markers = _match_freeform_external_hints(normalized, FREEFORM_EXTERNAL_SOURCE_HINTS)
    if not source_markers:
        return {}

    adoption_markers = _match_freeform_external_hints(normalized, FREEFORM_EXTERNAL_ADOPTION_HINTS)
    comparison_markers = _match_freeform_external_hints(normalized, FREEFORM_EXTERNAL_COMPARISON_HINTS)
    inspiration_markers = _match_freeform_external_hints(normalized, FREEFORM_EXTERNAL_INSPIRATION_HINTS)

    usage_mode = "reference"
    usage_markers: list[str] = []
    if adoption_markers:
        usage_mode = "adoption"
        usage_markers = adoption_markers
    elif comparison_markers:
        usage_mode = "comparison"
        usage_markers = comparison_markers
    elif inspiration_markers:
        usage_mode = "inspiration"
        usage_markers = inspiration_markers

    summary = "Freeform external proposal referenced in ordinary conversation."
    return {
        "external_suggestion": {
            "source": "freeform_conversation",
            "summary": summary,
        },
        "external_suggestion_present": True,
        "external_suggestion_source": "freeform_conversation",
        "external_suggestion_summary": summary,
        "external_suggestion_usage": usage_mode,
        "freeform_external_markers": source_markers[:3],
        "freeform_usage_markers": usage_markers[:3],
        "freeform_external_inferred": True,
    }


def _merge_external_suggestion_details(*sources) -> dict:
    """Merge explicit and inferred external-suggestion details without dropping prior fields."""
    merged: dict = {}
    for source in sources:
        payload = dict(source or {})
        for key, value in payload.items():
            if value in (None, "", [], {}):
                continue
            if key == "law_filter_applied" and value is not True:
                continue
            merged[key] = value
    if merged and "external_suggestion" not in merged:
        merged["external_suggestion"] = {
            "source": merged.get("external_suggestion_source") or "freeform_conversation",
            "summary": merged.get("external_suggestion_summary")
            or "Freeform external proposal referenced in ordinary conversation.",
        }
    return merged


def _summarize_canonical_external_suggestion_admission(admission):
    """Project external-suggestion law state into one bounded canonical trace block."""
    if not isinstance(admission, dict) or not admission:
        return None
    summary = {
        "status": admission.get("status"),
        "usage_mode": admission.get("usage_mode"),
        "adoption_requested": bool(admission.get("adoption_requested")),
        "law_filter_applied": bool(admission.get("law_filter_applied")),
        "admitted_form_documented": bool(admission.get("admitted_form_documented")),
    }
    return {key: value for key, value in summary.items() if _has_canonical_trace_value(value)}


def _record_external_suggestion_admission_trace(response_trace, admission):
    """Attach one bounded external-suggestion admission block to the live response trace."""
    if not isinstance(response_trace, dict):
        return None
    summary = _summarize_canonical_external_suggestion_admission(admission)
    if not summary:
        return None
    response_trace["external_suggestion_admission"] = summary
    status = summary.get("status")
    if status == "blocked":
        _append_response_trace_step(
            response_trace,
            "Blocked raw external adoption in the freeform chat lane until the law filter, admitted form, and non-copy clause all clear.",
        )
    elif status == "admitted":
        _append_response_trace_step(
            response_trace,
            "External suggestion admission accepted for this turn. Jarvis is using only the documented admitted form and is not copying raw outside wording into system truth.",
        )
    elif status == "reference_only":
        _append_response_trace_step(
            response_trace,
            "External suggestion observed as comparison-only context for this turn and not copied into adopted system truth.",
        )
    return summary


def _build_external_suggestion_guidance_block(session):
    """Inject one canonical law block when freeform external input is present but not blocked."""
    admission = dict(session.metadata.get("external_suggestion_admission") or {})
    if not admission.get("present"):
        return None
    if admission.get("status") == "admitted":
        admitted_form = admission.get("admitted_form_summary") or "Use only the documented admitted form."
        return (
            "External suggestion admission law: the raw outside proposal is not system truth. "
            "Use only this documented admitted form for this turn, keep existing doctrine intact, "
            f"do not copy raw outside wording into architecture or collective truth, and use only this admitted form: {admitted_form}"
        )
    if admission.get("status") == "reference_only":
        usage_mode = admission.get("usage_mode") or "reference"
        return (
            "External suggestion admission law: an outside idea is present for "
            f"{usage_mode} only. It may be discussed, compared, critiqued, or pressure-tested, "
            "but it is not adopted system behavior and must not be copied into implementation truth."
        )
    return None


def _build_external_suggestion_guardrail_result(admission: dict, *, blocking_message: str) -> dict:
    """Return one deterministic direct-tool guardrail result for blocked freeform adoption turns."""
    remedy = (
        "document the admitted form first."
        if admission.get("law_filter_applied")
        else "run the law filter, remove doctrine violations, satisfy the non-copy clause, document the admitted form, and only then continue from that admitted form."
    )
    response = (
        "I can compare, critique, or pressure-test that outside proposal, but I can't adopt it from ordinary conversation. "
        "I also can't copy it raw into AAIS truth. "
        f"{remedy[0].upper()}{remedy[1:]}"
    )
    return {
        "response": response,
        "tool_result": {
            "type": "external_suggestion_guardrail",
            "status": "blocked",
            "summary": (
                "Jarvis blocked raw external adoption in ordinary conversation until the law filter, admitted form, and non-copy clause are satisfied."
            ),
            "external_suggestion_admission": dict(admission or {}),
            "external_suggestion_guardrail": {
                "status": "blocked",
                "reason": "external_suggestion_admission",
                "conversation_lane": "freeform_chat",
                "requested_usage": admission.get("usage_mode") or "adoption",
            },
            "law_enforcement": {
                "source_of_truth": "project_infi_law",
                "blocking_message": str(blocking_message or "").strip()
                or "External suggestion adoption is blocked until the law filter runs and the admitted form is documented.",
                "external_suggestion_admission": dict(admission or {}),
            },
        },
    }


def _maybe_handle_freeform_external_suggestion(
    session,
    *,
    user_message: str,
    request_payload: dict | None,
):
    """Apply freeform external-suggestion admission law before planning or execution selection."""
    explicit_details = _extract_external_suggestion_details(request_payload)
    inferred_details = _infer_freeform_external_suggestion_details(user_message)
    details = _merge_external_suggestion_details(inferred_details, explicit_details)
    session.metadata["external_suggestion_admission"] = None
    session.metadata["external_suggestion_details"] = None
    session.metadata["external_suggestion_law_enforcement"] = None
    if not details:
        return None

    admission = _normalize_external_suggestion_admission(details)
    session.metadata["external_suggestion_details"] = dict(details)
    session.metadata["external_suggestion_admission"] = dict(admission)
    if not admission.get("present"):
        return None

    try:
        contract, _ul_snapshot, _ = jarvis_operator.project_infi_law.require_contract(
            surface="chat_turn",
            action_id="freeform_external_suggestion_turn",
            actor_id="operator",
            actor_role="operator",
            session_id=session.session_id,
            target="freeform_chat",
            details=details,
        )
    except ValueError as exc:
        blocking_message = str(exc)
        session.metadata["external_suggestion_law_enforcement"] = {
            "source_of_truth": "project_infi_law",
            "blocking_message": blocking_message,
            "external_suggestion_admission": dict(admission),
        }
        _record_session_event(
            session,
            "external_suggestion_adoption_blocked",
            "Jarvis blocked raw external adoption in ordinary conversation.",
            payload={
                "status": admission.get("status"),
                "usage_mode": admission.get("usage_mode"),
                "law_filter_applied": bool(admission.get("law_filter_applied")),
                "admitted_form_documented": bool(admission.get("admitted_form_documented")),
            },
        )
        return _build_external_suggestion_guardrail_result(
            admission,
            blocking_message=blocking_message,
        )

    session.metadata["external_suggestion_admission"] = dict(contract["external_suggestion_admission"])
    session.metadata["external_suggestion_law_enforcement"] = {
        "source_of_truth": "project_infi_law",
        "contract_version": contract.get("contract_version"),
        "external_suggestion_admission": dict(contract["external_suggestion_admission"]),
    }
    event_type = "external_suggestion_observed"
    event_summary = "Jarvis marked the outside proposal as reference-only context for this turn."
    if contract["external_suggestion_admission"].get("status") == "admitted":
        event_type = "external_suggestion_admitted"
        event_summary = "Jarvis accepted the documented admitted form for this turn."
    _record_session_event(
        session,
        event_type,
        event_summary,
        payload={
            "status": contract["external_suggestion_admission"].get("status"),
            "usage_mode": contract["external_suggestion_admission"].get("usage_mode"),
            "law_filter_applied": bool(contract["external_suggestion_admission"].get("law_filter_applied")),
            "admitted_form_documented": bool(
                contract["external_suggestion_admission"].get("admitted_form_documented")
            ),
        },
    )
    return None


def _extra_prompt_blocks(session, *, plan_summary=None, local_fallback=False):
    """Build identity-stable prompt blocks for per-turn guidance overlays."""
    blocks = []
    if local_fallback:
        blocks.append(
            {
                "identity": "local_fallback_guardrail",
                "role": "system",
                "content": (
                    "Answer as Jarvis in one concise, operator-safe voice. "
                    "Do not expose response trace, hidden planning, workspace headers, review headers, "
                    "system labels, memory cues, or internal scaffolding."
                ),
                "channel": "instruction",
                "source": "local_fallback_guardrail",
                "priority": 15,
                "required": True,
            }
        )
    plan_block = _build_plan_guidance_block(plan_summary)
    if plan_block:
        blocks.append(
            {
                "identity": "plan_guidance",
                "role": "system",
                "content": plan_block,
                "channel": "instruction",
                "source": "plan_guidance",
                "priority": 25,
                "required": True,
            }
        )
    external_suggestion_block = _build_external_suggestion_guidance_block(session)
    if external_suggestion_block:
        blocks.append(
            {
                "identity": "external_suggestion_guidance",
                "role": "system",
                "content": external_suggestion_block,
                "channel": "instruction",
                "source": "external_suggestion_guidance",
                "priority": 18,
                "required": True,
            }
        )
    direct_challenge_block = _build_direct_challenge_guidance_block(session)
    if direct_challenge_block:
        blocks.append(
            {
                "identity": "direct_challenge_guidance",
                "role": "system",
                "content": direct_challenge_block,
                "channel": "instruction",
                "source": "direct_challenge_guidance",
                "priority": 20,
                "required": True,
            }
        )
    speaking_runtime_block = build_speaking_runtime_prompt_block(session)
    if speaking_runtime_block:
        blocks.append(speaking_runtime_block)
    return blocks


def _build_final_messages(
    session,
    plan_summary=None,
    *,
    prompt_token_budget=None,
    reserved_response_budget=0,
    response_trace=None,
):
    """Build the final chat messages, optionally grounded by a planning pass."""
    prompt_trace = {}
    messages = session.build_messages(
        max_tokens_estimate=prompt_token_budget or DEFAULT_CHAT_CONTEXT_LIMIT,
        extra_system_blocks=_extra_prompt_blocks(session, plan_summary=plan_summary),
        prompt_trace=prompt_trace,
        reserved_response_budget=reserved_response_budget,
    )
    _record_prompt_assembly_trace(session, response_trace, prompt_trace)
    return messages


def _local_fallback_active(session, *, response_trace=None) -> bool:
    """Return whether the current turn is running through Local Heroine as a remote fallback."""
    notice = session.metadata.get("provider_notice") or {}
    if notice.get("status") == "fallback" and notice.get("resolved_provider") == "local":
        return True
    route = {}
    if isinstance(response_trace, dict):
        route = response_trace.get("model_route") or {}
        if response_trace.get("fallback") and (route.get("provider") in {"local", None, ""}):
            return True
    if not route:
        route = session.metadata.get("model_route") or {}
    return (
        str(route.get("provider") or "").strip().lower() == "local"
        and str(route.get("provider_reason") or "").startswith("fallback_from_")
    )


def _build_local_fallback_messages(
    session,
    *,
    prompt_token_budget=None,
    reserved_response_budget=0,
    response_trace=None,
):
    """Build a stripped-down prompt for Local Heroine fallback turns only."""
    system_blocks = []
    dialogue_messages = []
    assistant_echoes_scrubbed = 0
    seed_seen = False

    for index, turn in enumerate(session.get_context_window(prompt_token_budget or DEFAULT_CHAT_CONTEXT_LIMIT)):
        raw_content = str(turn.content or "").strip()
        content = raw_content
        if turn.role == "assistant":
            content = sanitize_assistant_context_text(raw_content)
            if raw_content and content != raw_content:
                assistant_echoes_scrubbed += 1
        if not content or turn.role not in {"system", "user", "assistant"}:
            continue
        if turn.role == "system":
            identity = "system_seed" if not seed_seen else f"turn_system_{index}"
            seed_seen = True
            system_blocks.append(
                {
                    "identity": identity,
                    "role": "system",
                    "content": content,
                    "channel": "instruction",
                    "source": "turn_system",
                    "priority": 0 if identity == "system_seed" else 5,
                    "required": identity == "system_seed",
                    "singleton": identity == "system_seed",
                }
            )
        else:
            dialogue_messages.append({"role": turn.role, "content": content})

    continuity_prompt = session.metadata.get("continuity_prompt_block")
    if continuity_prompt:
        system_blocks.append(
            {
                "identity": "continuity_profile",
                "role": "system",
                "content": continuity_prompt,
                "channel": "continuity",
                "source": "continuity_prompt_block",
                "priority": 35,
            }
        )
    system_blocks.extend(_extra_prompt_blocks(session, local_fallback=True))
    assembled_blocks, prompt_trace = assemble_prompt_blocks(
        system_blocks,
        prompt_token_budget=prompt_token_budget or DEFAULT_CHAT_CONTEXT_LIMIT,
        reserved_response_budget=reserved_response_budget,
        assistant_echoes_scrubbed=assistant_echoes_scrubbed,
    )
    _record_prompt_assembly_trace(session, response_trace, prompt_trace.to_dict())
    combined_system = combine_system_prompt(assembled_blocks)
    if combined_system:
        return [{"role": "system", "content": combined_system}] + dialogue_messages
    return dialogue_messages


def _build_generation_messages(session, plan_summary=None, *, response_trace=None, max_length=None, model=None):
    """Choose the safest message assembly for the currently resolved provider path."""
    prompt_token_budget, reserved_response_budget, _budget_policy = _resolve_prompt_token_budget(
        session,
        max_length=max_length,
        model=model,
    )
    if _local_fallback_active(session, response_trace=response_trace):
        messages = _build_local_fallback_messages(
            session,
            prompt_token_budget=prompt_token_budget,
            reserved_response_budget=reserved_response_budget,
            response_trace=response_trace,
        )
    else:
        messages = _build_final_messages(
            session,
            plan_summary=plan_summary,
            prompt_token_budget=prompt_token_budget,
            reserved_response_budget=reserved_response_budget,
            response_trace=response_trace,
        )

    allow_duplicates = normalize_response_mode(session.metadata.get("response_mode")) == "debug"
    messages = _enforce_memory_cue_uniqueness(
        messages,
        session.metadata.get("persistent_memories") or [],
        allow_duplicates=allow_duplicates,
    )
    _record_memory_cue_trace(session, messages)
    return messages


def _protocol_messages_for_modular_preview(
    session,
    *,
    plan_summary=None,
    max_length=None,
    model=None,
    response_trace=None,
):
    """Build protocol envelope messages used by the modular UL preview path."""
    prompt_token_budget, reserved_response_budget, _budget_policy = _resolve_prompt_token_budget(
        session,
        max_length=max_length,
        model=model,
    )
    prompt_trace = {}
    envelope = session.build_protocol_envelope(
        max_tokens_estimate=prompt_token_budget,
        extra_system_blocks=_extra_prompt_blocks(session, plan_summary=plan_summary),
        prompt_trace=prompt_trace,
        reserved_response_budget=reserved_response_budget,
    )
    _record_prompt_assembly_trace(session, response_trace, prompt_trace)
    return list(envelope.get("messages") or [])


def _preview_model_name(session, *, model=None) -> str:
    routing_profile = session.metadata.get("model_route") or {}
    return str(
        routing_profile.get("provider_model")
        or routing_profile.get("model")
        or model
        or "local"
    )


def _prepare_chat_turn_modular_generation(
    session,
    *,
    plan_summary=None,
    response_trace=None,
    max_length=None,
    model=None,
    temperature=0.7,
    stream=False,
):
    """Prepare one modular generation package for local and remote model paths."""
    response_mode = normalize_response_mode(session.metadata.get("response_mode"))
    protocol_messages = _protocol_messages_for_modular_preview(
        session,
        plan_summary=plan_summary,
        max_length=max_length,
        model=model,
        response_trace=response_trace,
    )
    local_messages = _build_generation_messages(
        session,
        plan_summary=plan_summary,
        response_trace=response_trace,
        max_length=max_length,
        model=model,
    )
    package = prepare_chat_turn_modular_package(
        session,
        protocol_messages=protocol_messages,
        model=_preview_model_name(session, model=model),
        stream=stream,
        temperature=temperature,
        max_tokens=int(max_length or 0) or 512,
        mode=response_mode,
    )
    preview = dict(package["preview"])
    attach_modular_preview_to_response_trace(response_trace, preview)
    session.metadata["cisiv_stage"] = infer_chat_turn_cisiv_stage(phase="generate")
    return {
        "local_messages": local_messages,
        "provider_messages": list(package["provider_messages"]),
        "preview": preview,
    }


def _build_plan_guidance_block(plan_summary=None):
    """Render the hidden planning block used to ground a final answer turn."""
    if not plan_summary:
        return None

    hidden_guidance = _plan_summary_to_hidden_guidance(plan_summary) or (
        "Use the gathered context silently and answer directly."
    )
    return (
        "You already gathered the evidence for this turn. "
        "Answer the operator directly using that context. "
        "Do not restate hidden planning notes, answer-shape instructions, "
        "raw file previews, raw prompt blocks, or irrelevant paths. "
        "Never begin with labels like Mode, Focus, Specialists, God Brain, Evidence, or Answer Shape.\n"
        f"Jarvis internal guidance for this turn:\n{hidden_guidance}"
    )


def _current_turn_looks_like_direct_challenge(session) -> bool:
    """Return whether the latest user turn is a direct challenge aimed at Jarvis."""
    for turn in reversed(session.turns):
        if turn.role == "user" and str(turn.content or "").strip():
            return looks_like_direct_challenge(turn.content)
    return False


def _build_direct_challenge_guidance_block(session):
    """Attach one identity-stable instruction block for direct challenges."""
    for turn in reversed(session.turns):
        if turn.role == "user" and str(turn.content or "").strip():
            if looks_like_direct_challenge(turn.content):
                return build_direct_challenge_guidance(turn.content)
            return None
    return None


def _direct_challenge_turn_active(session, *, response_trace=None, user_message: str | None = None) -> bool:
    """Resolve whether this turn must stay in the direct-challenge lane."""
    if user_message and looks_like_direct_challenge(user_message):
        return True
    if isinstance(response_trace, dict):
        packet = response_trace.get("reasoning_packet") or {}
        if packet.get("objective") == "handle_direct_challenge":
            return True
        contract = packet.get("output_contract") or {}
        if contract.get("allow_trace") is False and packet.get("objective") == "handle_direct_challenge":
            return True
        if response_trace.get("reasoning_objective") == "handle_direct_challenge":
            return True
    return _current_turn_looks_like_direct_challenge(session)


def _relational_turn_active(session, *, response_trace=None, user_message: str | None = None) -> bool:
    """Resolve whether this turn should stay off the planning-heavy cognitive lane."""
    if user_message and detect_objective(user_message) in {"handle_direct_challenge", "answer_relational_question"}:
        return True
    if isinstance(response_trace, dict):
        packet = response_trace.get("reasoning_packet") or {}
        if packet.get("objective") in {"handle_direct_challenge", "answer_relational_question"}:
            return True
        if response_trace.get("reasoning_objective") in {"handle_direct_challenge", "answer_relational_question"}:
            return True
    for turn in reversed(session.turns):
        if turn.role == "user" and str(turn.content or "").strip():
            return detect_objective(turn.content) in {"handle_direct_challenge", "answer_relational_question"}
    return False


def _estimate_output_sensitivity(text: str, *, response_trace=None) -> int:
    """Estimate reply sensitivity for the output channel security check."""
    lowered = str(text or "").lower()
    if any(marker in lowered for marker in LOCAL_FALLBACK_CONTAMINATION_MARKERS):
        return 9
    if LOCAL_FALLBACK_HEADER_RE.search(text or ""):
        return 9
    if isinstance(response_trace, dict) and response_trace.get("contract") in {"trace_isolate_verify", "inspect_verify_act"}:
        return 6
    return 4


def _enforce_identity_safe_response(session, user_message: str, response_text: str, *, response_trace=None) -> str:
    """Run the final Jarvis identity and continuity gate before any reply is shown."""
    text = str(response_text or "").strip()
    direct_challenge = _direct_challenge_turn_active(
        session,
        response_trace=response_trace,
        user_message=user_message,
    )
    thread_contract = build_anti_drift_thread_contract(
        session_id=session.session_id,
        user_message=user_message,
        turn_contract=session.metadata.get("turn_contract"),
        mode_guidance=session.metadata.get("mode_guidance"),
    )
    session.metadata["thread_contract"] = thread_contract
    _refresh_sovereignty_contract(session)

    if _local_fallback_active(session, response_trace=response_trace):
        lowered = text.lower()
        contamination = [
            marker for marker in LOCAL_FALLBACK_CONTAMINATION_MARKERS
            if marker in lowered
        ]
        if LOCAL_FALLBACK_HEADER_RE.search(text):
            contamination.append("header_scaffolding")
        identity_drift = [
            marker for marker in LOCAL_FALLBACK_IDENTITY_DRIFT_MARKERS
            if marker in lowered
        ]
        boilerplate = [
            marker for marker in LOCAL_FALLBACK_BOILERPLATE_MARKERS
            if lowered.count(marker) >= 2
        ]
        repeated_sentences = [
            sentence
            for sentence in {
                sentence.strip()
                for sentence in re.split(r"[.!?]+", lowered)
                if len(sentence.strip()) >= 24
            }
            if lowered.count(sentence) >= 2
        ]
        if repeated_sentences:
            boilerplate.append("repeated_sentence_loop")

        if not text:
            contamination.append("empty_output")

        if contamination or identity_drift or boilerplate:
            summary = "Contained Local Heroine fallback output before display."
            payload = {
                "provider": "local",
                "fallback": True,
                "contamination": contamination,
                "identity_drift": identity_drift,
                "boilerplate": boilerplate,
            }
            logger.warning(
                "Contained Local Heroine fallback output for session %s: %s",
                session.session_id,
                payload,
            )
            _record_session_event(session, "continuity_contained", summary, payload=payload)
            if isinstance(response_trace, dict):
                response_trace.setdefault("steps", []).append(summary)
            return (
                LOCAL_FALLBACK_DIRECT_CHALLENGE_RESPONSE
                if direct_challenge
                else LOCAL_FALLBACK_GENERAL_RESPONSE
            )

    if not direct_challenge:
        output_sensitivity = _estimate_output_sensitivity(text, response_trace=response_trace)
        security_result = _run_security_check(
            caller=_build_caller_context(session=session),
            resource=ResourceMeta(
                id="operator_console",
                type=ResourceType.OUTPUT_CHANNEL,
                category="jarvis_reply",
                sensitivity=output_sensitivity,
            ),
            action=Action.EMIT_SENSITIVE_OUTPUT if output_sensitivity > 6 else Action.EMIT_OUTPUT,
            details={"surface": "final_reply"},
        )
        decision = (security_result.get("decision") or {}).get("decision")
        if decision == "deny":
            summary = "Output guardrails blocked a reply before display and replaced it with a Jarvis-owned fallback."
            drift_state = {
                "status": "blocked",
                "score": 4,
                "findings": [
                    {
                        "kind": "output_guardrail",
                        "severity": 4,
                        "reason": "output_guardrail_deny",
                        "detail": "Output guardrails blocked the reply before display.",
                    }
                ],
                "summary": summary,
                "updated_at": datetime.now(UTC).isoformat(),
            }
            session.metadata["drift_state"] = drift_state
            _refresh_sovereignty_contract(session)
            _record_session_event(
                session,
                "output_guardrail_blocked",
                summary,
                payload=security_result,
            )
            if isinstance(response_trace, dict):
                response_trace.setdefault("steps", []).append(summary)
                response_trace["drift_state"] = drift_state
            contract_label = str(thread_contract.get("contract_label") or "").strip().lower()
            if contract_label == "otem":
                return "Staying inside the active OTEM contract. Output guardrails blocked that reply before display."
            if contract_label == "memory_governance":
                return "Staying inside the active memory-governance contract. Output guardrails blocked that reply before display."
            if str(thread_contract.get("resolved_mode") or "").strip().lower() == "debug":
                return "Staying inside the current debug contract. Output guardrails blocked that reply before display."
            return OUTPUT_GUARDRAIL_BLOCKED_RESPONSE

    anti_drift_result = enforce_anti_drift(text, thread_contract=thread_contract)
    drift_state = {
        "status": anti_drift_result["status"],
        "score": anti_drift_result["score"],
        "findings": list(anti_drift_result["findings"] or []),
        "summary": anti_drift_result["summary"],
        "updated_at": datetime.now(UTC).isoformat(),
    }
    session.metadata["drift_state"] = drift_state
    _refresh_sovereignty_contract(session)
    if isinstance(response_trace, dict):
        response_trace["drift_state"] = drift_state
    if anti_drift_result["contained"]:
        summary = "Anti-drift corrected the reply before display to keep the active thread contract authoritative."
        payload = {
            "thread_contract": thread_contract,
            "drift_state": drift_state,
        }
        logger.warning(
            "Anti-drift contained reply drift for session %s: %s",
            session.session_id,
            drift_state,
        )
        _record_session_event(session, "anti_drift_contained", summary, payload=payload)
        if isinstance(response_trace, dict):
            response_trace.setdefault("steps", []).append(summary)
    final_text = anti_drift_result["final_text"]
    if not direct_challenge:
        return final_text

    stabilized = enforce_direct_challenge_identity(final_text, user_message)
    output_sensitivity = _estimate_output_sensitivity(stabilized, response_trace=response_trace)
    security_result = _run_security_check(
        caller=_build_caller_context(session=session),
        resource=ResourceMeta(
            id="operator_console",
            type=ResourceType.OUTPUT_CHANNEL,
            category="jarvis_reply",
            sensitivity=output_sensitivity,
        ),
        action=Action.EMIT_SENSITIVE_OUTPUT if output_sensitivity > 6 else Action.EMIT_OUTPUT,
        details={"surface": "final_reply", "direct_challenge": True},
    )
    if (security_result.get("decision") or {}).get("decision") == "deny":
        return LOCAL_FALLBACK_DIRECT_CHALLENGE_RESPONSE
    if stabilized != final_text and isinstance(response_trace, dict):
        response_trace.setdefault("steps", []).append(
            "Direct challenge guard replaced generic or collapsed identity language with a stable Jarvis reply."
        )
    return stabilized


def _messages_to_prompt(messages):
    """Render structured chat messages into the prompt format used by streaming."""
    parts = []

    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if not content:
            continue
        if role == "system":
            parts.append(f"[INST] <<SYS>>\n{content}\n<</SYS>>")
        elif role == "user":
            parts.append(f"[INST] {content} [/INST]")
        elif role == "assistant":
            parts.append(content)

    return "\n".join(parts)


def _set_session_persona_mode(session, requested_mode=None):
    """Apply the requested persona mode to the active session."""
    normalized = normalize_persona_mode(
        requested_mode if requested_mode is not None else session.metadata.get("persona_mode")
    )
    session.metadata["persona_mode"] = normalized
    _sync_session_identity_prompt(session, normalized)
    return normalized


def _set_session_response_mode(session, requested_mode=None):
    """Apply the requested response mode to the active session."""
    normalized = _coerce_response_mode_for_persona(
        session.metadata.get("persona_mode"),
        requested_mode
        if requested_mode is not None
        else session.metadata.get("requested_response_mode") or session.metadata.get("response_mode"),
    )
    companion_profile = _get_companion_surface_profile(
        persona_mode=session.metadata.get("persona_mode"),
        response_mode=normalized,
    )
    session.metadata["requested_response_mode"] = normalized
    session.metadata["response_mode"] = normalized
    session.metadata["mode_guidance"] = {
        "status": "locked_persona" if companion_profile else "aligned",
        "requested_mode": normalized,
        "effective_mode": normalized,
        "recommended_mode": normalized,
        "confidence": 1.0,
        "reason": (
            f"{companion_profile['label']} always runs inside the {normalized} companion lane."
            if companion_profile
            else f"{normalized.title()} is currently selected for this session."
        ),
        "summary": (
            f"{companion_profile['label']} stays in the companion lane for this session."
            if companion_profile
            else f"Current {normalized.title()} mode already fits the session setting."
        ),
        "signals": [companion_profile["signal"]] if companion_profile else [],
        "auto_applied": False,
        "resolved_scope": (
            "companion" if companion_profile else ("debugging" if normalized == "debug" else "operator_task")
        ),
        "resolved_voice": companion_profile["identity"] if companion_profile else "jarvis",
        "selector_reason": (
            companion_profile["selector_reason"]
            if companion_profile
            else "Current request mode is authoritative for this turn."
        ),
        "selector_trigger": companion_profile["signal"] if companion_profile else None,
        "debug_lockout_applied": False,
    }
    return normalized


def _set_session_preferred_provider(
    session,
    requested_provider=None,
    *,
    requested_provider_mode=None,
    prefer_new_session_default: bool = False,
):
    """Apply the requested provider preference to the active session."""
    explicit_request = requested_provider is not None and str(requested_provider).strip() != ""
    normalized_provider_mode = normalize_provider_mode_identifier(requested_provider_mode, default="")
    raw_provider = (
        requested_provider
        if explicit_request
        else (
            _default_new_session_provider(
                requested_provider_mode=normalized_provider_mode,
                prefer_new_session_default=prefer_new_session_default,
            )
            if (requested_provider_mode is not None or prefer_new_session_default)
            else session.metadata.get("preferred_provider")
        )
    )
    normalized = normalize_provider_identifier(raw_provider, default="local")
    if normalized == "auto":
        session.metadata["preferred_provider"] = "auto"
        session.metadata["provider_fallback"] = "local"
        session.metadata["provider_mode"] = derive_provider_mode(
            session.metadata.get("preferred_provider"),
            session.metadata.get("provider_fallback"),
        )
        return normalized
    config = provider_registry.get_config(normalized)
    if config is None:
        normalized = "local"
    elif not explicit_request and not provider_registry.can_invoke(normalized):
        normalized = _default_new_session_provider()
    session.metadata["preferred_provider"] = normalized
    session.metadata["provider_fallback"] = _get_session_fallback_provider(session)
    session.metadata["provider_mode"] = derive_provider_mode(
        normalized,
        session.metadata.get("provider_fallback"),
    )
    return normalized


def _default_new_session_provider(*, requested_provider_mode: str | None = None, prefer_new_session_default: bool = False):
    """Choose the preferred provider for a fresh Jarvis session."""
    normalized_provider_mode = normalize_provider_mode_identifier(requested_provider_mode, default="")
    if normalized_provider_mode == "auto_best":
        return "auto"
    if normalized_provider_mode == "claude_first":
        return "claude" if provider_registry.can_invoke("claude") else (provider_registry.get_default_name() or "local")
    if normalized_provider_mode == "openrouter_first":
        return "openrouter" if provider_registry.can_invoke("openrouter") else (provider_registry.get_default_name() or "local")
    if normalized_provider_mode == "nvidia_first":
        return "nvidia" if provider_registry.can_invoke("nvidia") else (provider_registry.get_default_name() or "local")
    if normalized_provider_mode == "openai_first":
        return "openai" if provider_registry.can_invoke("openai") else (provider_registry.get_default_name() or "local")
    if normalized_provider_mode == "google_first":
        return "google" if provider_registry.can_invoke("google") else (provider_registry.get_default_name() or "local")
    if normalized_provider_mode == "local_first":
        return provider_registry.get_default_name() or "local"
    if prefer_new_session_default and provider_registry.can_invoke("openrouter"):
        return "openrouter"
    return provider_registry.get_default_name() or "local"


def _get_session_fallback_provider(session):
    """Resolve the stable fallback provider for one session."""
    fallback = normalize_provider_identifier(
        (session.metadata or {}).get("provider_fallback"),
        default="local",
    )
    if not provider_registry.can_invoke(fallback):
        fallback = provider_registry.get_default_name() or "local"
    return fallback


def _build_provider_notice(session):
    """Surface an honest fallback notice when a requested sister model is unavailable."""
    requested_provider = normalize_provider_identifier(
        session.metadata.get("preferred_provider"),
        default="local",
    )
    resolved_provider = normalize_provider_identifier(
        (session.metadata.get("model_route") or {}).get("provider"),
        default="local",
    )

    if requested_provider in {"", "local", "auto"} or requested_provider == resolved_provider:
        session.metadata["provider_notice"] = None
        _refresh_sovereignty_contract(session)
        return None

    requested_config = provider_registry.get_config(requested_provider)
    resolved_config = provider_registry.get_config(resolved_provider)
    requested_label = (
        requested_config.display_name
        if requested_config
        else requested_provider.replace("_", " ").title()
    )
    resolved_label = (
        resolved_config.display_name
        if resolved_config
        else resolved_provider.replace("_", " ").title()
    )
    reason = (
        (requested_config.meta or {}).get("reason")
        if requested_config
        else None
    ) or "The requested provider is not available right now."

    notice = {
        "status": "fallback",
        "requested_provider": requested_provider,
        "requested_label": requested_label,
        "resolved_provider": resolved_provider,
        "resolved_label": resolved_label,
        "reason": reason,
        "summary": (
            f"{requested_label} was requested, but she is not available right now. "
            f"Jarvis fell back to {resolved_label} for this turn."
        ),
    }
    session.metadata["provider_notice"] = notice
    _refresh_sovereignty_contract(session)
    return notice


def _summarize_remote_provider_error(provider_id, exc):
    """Compress noisy remote-provider exceptions into a short operator-facing reason."""
    provider_config = provider_registry.get_config(provider_id)
    provider_label = (
        provider_config.display_name
        if provider_config
        else str(provider_id or "remote provider").replace("_", " ").title()
    )
    normalized = " ".join(str(exc or "").split())
    lowered = normalized.lower()

    if "429" in lowered or "rate-limit" in lowered or "rate limit" in lowered:
        return f"{provider_label} hit a temporary upstream rate limit."
    if "timed out" in lowered or "timeout" in lowered:
        return f"{provider_label} timed out while generating."
    if any(code in lowered for code in ("502", "503", "504")):
        return f"{provider_label} is temporarily unavailable upstream."
    if "connection reset" in lowered or "connection aborted" in lowered:
        return f"{provider_label} lost the upstream connection mid-turn."
    if normalized:
        return _clip_trace_text(normalized, limit=220)
    return f"{provider_label} could not complete this turn."


def _should_fallback_remote_provider(session, exc):
    """Return whether a remote-provider failure should fall back to the local model."""
    route = session.metadata.get("model_route") or {}
    provider_id = str(route.get("provider") or "").strip().lower()
    if provider_id in {"", "local"}:
        return False

    lowered = " ".join(str(exc or "").lower().split())
    transient_markers = (
        "429",
        "rate-limit",
        "rate limit",
        "temporarily rate-limited",
        "timed out",
        "timeout",
        "502",
        "503",
        "504",
        "connection reset",
        "connection aborted",
        "temporarily unavailable",
    )
    return any(marker in lowered for marker in transient_markers)


def _apply_remote_provider_fallback(session, exc, *, response_trace=None):
    """Switch the current turn back to the local provider after a transient remote failure."""
    if not _should_fallback_remote_provider(session, exc):
        return None

    current_route = dict(session.metadata.get("model_route") or {})
    failed_provider = str(current_route.get("provider") or "remote").strip().lower()
    requested_config = provider_registry.get_config(failed_provider)
    requested_label = (
        requested_config.display_name
        if requested_config
        else failed_provider.replace("_", " ").title()
    )
    reason = _summarize_remote_provider_error(failed_provider, exc)
    fallback_provider = _get_session_fallback_provider(session)
    fallback_config = provider_registry.get_config(fallback_provider)
    fallback_label = (
        fallback_config.display_name
        if fallback_config
        else fallback_provider.replace("_", " ").title()
    )

    fallback_route = dict(current_route)
    fallback_route["provider"] = fallback_provider
    fallback_route["provider_label"] = fallback_label
    fallback_route["provider_kind"] = (fallback_config.meta or {}).get("kind", "local") if fallback_config else "local"
    fallback_route["provider_reason"] = f"fallback_from_{failed_provider}"
    fallback_route["provider_model"] = None
    fallback_route["execution_backend"] = "local_model" if fallback_provider == "local" else "remote_provider"
    session.metadata["model_route"] = fallback_route

    notice = {
        "status": "fallback",
        "fallback_kind": "runtime_error",
        "requested_provider": failed_provider,
        "requested_label": requested_label,
        "resolved_provider": fallback_provider,
        "resolved_label": fallback_label,
        "reason": reason,
        "summary": f"{reason} Jarvis fell back to {fallback_label} for this turn.",
    }
    session.metadata["provider_notice"] = notice

    active_trace = response_trace
    if not isinstance(active_trace, dict):
        active_trace = session.metadata.get("response_trace")
    if isinstance(active_trace, dict):
        active_trace["model_route"] = fallback_route
        active_trace["fallback"] = True
        _append_response_trace_step(active_trace, notice["summary"])
    _set_turn_contract(session, provider_fallback=True)
    _refresh_sovereignty_contract(session)

    return notice


def _resolve_generation_controls(response_mode, requested_length=None, requested_temperature=None):
    """Resolve generation settings from explicit inputs or the current response mode."""
    normalized_mode = normalize_response_mode(response_mode)
    defaults = RESPONSE_MODE_DEFAULTS[normalized_mode]
    max_tokens = _coerce_max_length(
        requested_length
        if requested_length is not None
        else _scale_response_mode_max_tokens(defaults["max_tokens"])
    )
    temperature = _coerce_temperature(
        requested_temperature if requested_temperature is not None else defaults["temperature"]
    )
    return normalized_mode, max_tokens, temperature


def _build_chat_runtime_payload(session, session_id, tool_result=None):
    """Serialize the current chat runtime state for JSON or SSE payloads."""
    _sync_super_nova_state(session)
    response_trace = _sanitize_session_response_trace(session)
    canonical_trace_contract = _sync_canonical_trace_contract(session, response_trace=response_trace)
    mission_context = session.metadata.get("mission_board") or mission_board.build_session_context(session_id)
    session.metadata["mission_board"] = mission_context
    sovereignty_contract = session.metadata.get("sovereignty_contract")
    if not isinstance(sovereignty_contract, dict):
        sovereignty_contract = _refresh_sovereignty_contract(session)
    companion_profile = _get_companion_surface_profile(
        persona_mode=session.metadata.get("persona_mode"),
        response_mode=session.metadata.get("response_mode"),
    )
    if _session_uses_companion_lane(session) and companion_profile:
        session.metadata["continuity_profile"] = session.metadata.get("continuity_profile") or dict(
            companion_profile["continuity_profile"]
        )
        session.metadata["continuity_prompt_block"] = None
    else:
        _build_continuity_profile(session)
    mission_snapshot = mission_board.snapshot(session_id=session_id)
    payload = {
        "session_id": session_id,
        "turn_count": len(session.turns),
        "active_mode": session.spiral_state.active_mode,
        "current_goal": session.spiral_state.current_goal,
        "turn_current_goal": session.metadata.get("turn_current_goal") or session.spiral_state.current_goal,
        "spiral_state": session.spiral_state.to_dict(),
        "session_state": session.session_state.to_dict(),
        "memory_summary": session.memory_summary.to_dict(),
        "persistent_memories": list(session.metadata.get("persistent_memories", [])),
        "loaded_session_archive": serialize_loaded_session_archive(
            session.metadata.get("loaded_session_archive")
        ),
        "workspace_context": session.metadata.get("workspace_context"),
        "live_research": session.metadata.get("live_research"),
        "urg_library_context": session.metadata.get("urg_library_context"),
        "browser_verification": session.metadata.get("browser_verification"),
        "mission_board": mission_snapshot,
        "mission_critic": session.metadata.get("mission_critic"),
        "model_route": session.metadata.get("model_route"),
        "provider_mind": session.metadata.get("provider_mind"),
        "god_brain": session.metadata.get("god_brain"),
        "specialist_profile": session.metadata.get("specialist_profile"),
        "requested_specialists": list(session.metadata.get("requested_specialists") or []),
        "requested_specialist_preset": session.metadata.get("requested_specialist_preset"),
        "persona_mode": normalize_persona_mode(session.metadata.get("persona_mode")),
        "requested_response_mode": normalize_response_mode(
            session.metadata.get("requested_response_mode") or session.metadata.get("response_mode")
        ),
        "response_mode": normalize_response_mode(session.metadata.get("response_mode")),
        "preferred_provider": normalize_provider_identifier(
            session.metadata.get("preferred_provider"),
            default="local",
        ),
        "provider_mode": session.metadata.get("provider_mode")
        or derive_provider_mode(
            session.metadata.get("preferred_provider"),
            session.metadata.get("provider_fallback"),
        ),
        "provider_fallback": normalize_provider_identifier(
            session.metadata.get("provider_fallback"),
            default="local",
        ),
        "provider_notice": session.metadata.get("provider_notice"),
        "mode_guidance": session.metadata.get("mode_guidance"),
        "context_priority_guard": session.metadata.get("context_priority_guard"),
        "external_suggestion_admission": session.metadata.get("external_suggestion_admission"),
        "cognitive_bridge": session.metadata.get("cognitive_bridge"),
        "law_enforcement": session.metadata.get("law_enforcement"),
        "ul_snapshot": session.metadata.get("ul_snapshot"),
        "law_event_log": session.metadata.get("law_event_log"),
        "response_trace": response_trace,
        "canonical_trace_contract": canonical_trace_contract,
        "turn_contract": session.metadata.get("turn_contract"),
        "speaking_runtime": summarize_speaking_runtime_state(session),
        "cognitive_runtime": summarize_cognitive_runtime_state(session),
        "nova_face_bridge": summarize_nova_face_bridge(session),
        "aais_composed_turn": summarize_composed_turn(session),
        "last_turn_contract": session.metadata.get("last_turn_contract"),
        "sovereignty_contract": sovereignty_contract,
        "mode_freeze": session.metadata.get("mode_freeze"),
        "state_snapshots": list(session.metadata.get("state_snapshots") or []),
        "otem_state": session.metadata.get("otem_state"),
        "policy_status": dict(session.metadata.get("policy_status") or default_policy_status()),
        "continuity_profile": session.metadata.get("continuity_profile"),
        "continuity_witness": session.metadata.get("continuity_witness"),
        "pending_action": session.metadata.get("pending_action"),
        "action_lifecycle": session.metadata.get("action_lifecycle"),
        "super_nova": session.metadata.get("super_nova_state"),
        "approval_audit": jarvis_operator.list_approval_audit(session_id, limit=8),
        "run_history": jarvis_operator.list_runs(session_id=session_id, limit=8),
        "memory_smith": jarvis_operator.memory_smith.snapshot(),
        "v9_runtime": v9_runtime.snapshot(limit=4),
        "v10_runtime": v10_runtime.snapshot(limit=4),
        "security_protocol": security_protocol_core.snapshot(limit_events=6),
        "immune_system": immune_system.snapshot(limit_events=6, limit_incidents=3),
        "governance": governance_layer.snapshot(limit_events=6, limit_requests=4),
        "module_governance": module_governance.snapshot(limit_events=6, limit_modules=6),
        "corrigibility": dict(
            session.metadata.get("corrigibility") or default_corrigibility_state()
        ),
        "jarvis_protocol": session.protocol_summary(tool_result=tool_result),
        "system_guard": system_guard.snapshot(limit_events=4),
        "dreamspace": dreamspace.snapshot(limit_dreams=2),
        "modular_preview": session.metadata.get("modular_preview"),
        "cisiv_stage": session.metadata.get("cisiv_stage") or infer_chat_turn_cisiv_stage(phase="gather"),
        "cisiv_stage_sequence": list(CISIV_STAGE_SEQUENCE),
        "tool_result": tool_result,
        "slingshot": _summarize_slingshot_session_state(session),
        "slingshot_last_receipt": session.metadata.get("slingshot_last_receipt"),
        "mechanic_case_id": session.metadata.get("mechanic_case_id"),
        "mechanic_enforcement": _summarize_mechanic_session_state(session),
    }
    return wrap_chat_runtime_payload(payload)


def _apply_mission_critic_review(session, review):
    """Persist the latest Mission Critic judgment onto the session and Mission Board."""
    if not isinstance(review, dict):
        return None
    if review.get("source") == "reply" and _local_fallback_active(session):
        summary = "Blocked Local Heroine fallback from writing protected mission review state."
        payload = {
            "provider": "local",
            "fallback": True,
            "blocked_state": "mission_critic",
            "protected_domains": list(SOVEREIGN_PROTECTED_STATE_MAP.keys()),
        }
        logger.warning(
            "Blocked protected mission_critic write from Local Heroine fallback for session %s",
            session.session_id,
        )
        response_trace = session.metadata.get("response_trace")
        if isinstance(response_trace, dict):
            response_trace.setdefault("steps", []).append(summary)
        _record_session_event(session, "sovereignty_violation_blocked", summary, payload=payload)
        return None

    normalized_review = dict(review)
    review_source = str(normalized_review.get("source") or "").strip().lower()
    if review_source in {"browser_verification", "action_result", "repo_change_verification"}:
        try:
            target = review_source
            if review_source == "browser_verification":
                target = str(
                    ((session.metadata.get("browser_verification") or {}).get("target_path"))
                    or target
                ).strip() or target
            elif review_source == "action_result":
                tool_result = ((session.metadata.get("response_trace") or {}).get("tool_result") or {})
                action = tool_result.get("action") or {}
                target = str(action.get("label") or action.get("id") or target).strip() or target
            normalized_review["judgment_log"] = jarvis_operator.project_infi_law.emit_judgment_log(
                review=normalized_review,
                actor_id="mission_critic",
                actor_role="system",
                session_id=session.session_id,
                target=target,
            )
        except Exception as exc:
            logger.warning("Could not emit Project Infi judgment log: %s", exc)

    session.metadata["mission_critic"] = normalized_review
    mission_board.attach_critic_review(session.session_id, normalized_review)
    _attach_session_mission_context(session)
    response_trace = session.metadata.get("response_trace")
    if isinstance(response_trace, dict):
        response_trace["mission_critic"] = normalized_review
    _record_session_event(
        session,
        "mission_critic_completed",
        normalized_review.get("summary") or "Mission Critic reviewed the latest mission movement.",
        payload={
            "source": normalized_review.get("source"),
            "status": normalized_review.get("status"),
            "score": normalized_review.get("score"),
            "suggested_mission_status": normalized_review.get("suggested_mission_status"),
            "judgment_id": ((normalized_review.get("judgment_log") or {}).get("judgment_id")),
        },
    )
    return normalized_review


def _build_provider_messages(session, plan_summary=None, *, max_length=None, model=None, response_trace=None):
    """Build provider-facing Jarvis messages through the modular preview path."""
    preview = session.metadata.get("modular_preview")
    if isinstance(preview, dict) and preview.get("provider_messages"):
        return provider_messages_from_preview(preview)

    generation = _prepare_chat_turn_modular_generation(
        session,
        plan_summary=plan_summary,
        response_trace=response_trace or session.metadata.get("response_trace"),
        max_length=max_length,
        model=model,
        stream=False,
    )
    return generation["provider_messages"]


def _generate_remote_provider_reply(
    session,
    *,
    max_length,
    temperature,
    plan_summary=None,
):
    """Generate a reply through an external provider route when selected."""
    routing_profile = session.metadata.get("model_route") or {}
    provider_id = normalize_provider_identifier(routing_profile.get("provider"), default="local")
    if provider_id in {"", "local"}:
        return None
    provider = provider_registry.get(provider_id)
    if provider is None:
        raise RuntimeError(f"Provider '{provider_id}' is not available.")

    messages = _build_provider_messages(
        session,
        plan_summary=plan_summary,
        max_length=max_length,
        model=ai_model,
        response_trace=session.metadata.get("response_trace"),
    )
    dispatch_trace = resolve_remote_output_budget(
        provider_id=provider_id,
        provider_model=routing_profile.get("provider_model") or getattr(provider, "model", None),
        messages=messages,
        requested_output_budget=int(max_length or 0),
        prompt_token_budget=int(
            (session.metadata.get("prompt_budget_policy") or {}).get("prompt_token_budget")
            or DEFAULT_CHAT_CONTEXT_LIMIT
        ),
        reply_budget_floor=int(
            (session.metadata.get("prompt_budget_policy") or {}).get("reply_budget_floor")
            or max(32, int(max_length or 0))
        ),
    )
    _record_provider_dispatch_trace(
        session,
        session.metadata.get("response_trace"),
        dispatch_trace,
    )
    dispatch_max_tokens = int(dispatch_trace.get("effective_output_token_budget") or max_length or 0)
    response = asyncio.run(
        provider.invoke(
            messages,
            max_tokens=dispatch_max_tokens,
            temperature=temperature,
            model=routing_profile.get("provider_model") or None,
        )
    )
    _merge_provider_usage_into_dispatch_trace(
        session,
        session.metadata.get("response_trace"),
        response,
    )
    return response


def _iter_stream_text_chunks(text: str):
    """Yield small streaming-friendly chunks from a completed provider response."""
    normalized = str(text or "")
    if not normalized:
        return
    for match in re.finditer(r"\S+\s*", normalized):
        yield match.group(0)


def _iter_finalized_stream_payloads(text: str):
    """Yield SSE-ready token payloads from a finalized visible response."""
    running_text = ""
    for chunk_text in _iter_stream_text_chunks(text):
        running_text += chunk_text
        yield {
            "event": "token",
            "token": chunk_text,
            "text_so_far": running_text,
            "finished": False,
        }
    yield {
        "event": "token",
        "token": "",
        "text_so_far": str(text or ""),
        "finished": True,
    }


def init_ai():
    """Initialize AI services lazily."""
    global ai_model, streaming_generator, ai_mode, ai_init_error
    if ai_model is not None:
        return ai_model, streaming_generator

    with ai_init_lock:
        if ai_model is not None:
            return ai_model, streaming_generator

        requested_mode = _get_model_mode()
        logger.info(f"Initializing AI services (mode={requested_mode})")

        try:
            if requested_mode == "mock":
                raise ImportError("Mock mode requested")

            remote_ids = []
            if requested_mode == "real":
                force_local = os.getenv("AAIS_FORCE_LOCAL_MODEL", "").strip().lower()
                if force_local not in {"1", "true", "yes", "on"}:
                    remote_ids = _configured_remote_providers()

            if remote_ids:
                loaded_model, loaded_streamer = _init_ai_api_backed(remote_ids)
                ai_model = loaded_model
                streaming_generator = loaded_streamer
                return ai_model, streaming_generator

            models_module = _load_module("src.models")
            streaming_module = _load_module("src.streaming")

            loaded_model = models_module.MultiModalAI()
            loaded_model._load_text_model()
            loaded_streamer = streaming_module.StreamingTextGenerator(
                model=loaded_model.text_model,
                tokenizer=loaded_model.text_tokenizer,
                device=loaded_model.device,
            )
            ai_model = loaded_model
            streaming_generator = loaded_streamer
            ai_mode = "real"
            ai_init_error = None
            logger.info("AI services initialized in real mode")
        except Exception as exc:
            if requested_mode == "real":
                logger.exception("Real AI mode failed to initialize")
                ai_model = None
                streaming_generator = None
                ai_mode = None
                ai_init_error = str(exc)
                raise

            logger.warning(f"Falling back to mock AI mode: {exc}")
            _initialize_mock_ai(exc, reason="init_ai_fallback")

    return ai_model, streaming_generator


def _run_with_inference_lock(callback):
    """Serialize model inference so one private local model serves one turn at a time."""
    with ai_inference_lock:
        return callback()


def _dreamspace_is_idle(idle_threshold_seconds: int) -> bool:
    """Return whether AAIS looks quiet enough for a background Dreamspace cycle."""
    threshold = max(60, int(idle_threshold_seconds or 0))
    now = datetime.now(UTC)
    active_states = {"gathering", "planning", "responding", "acting", "awaiting_approval", "primed"}

    sessions = list(conversation_memory.sessions.values())
    if not sessions:
        return True

    for session in sessions:
        age_seconds = (now - session.updated_at).total_seconds()
        if age_seconds < threshold:
            return False
        if session.session_state.state in active_states:
            return False

    return True


def _dreamspace_context() -> dict:
    """Build a compact AAIS-native context packet for Dreamspace generation."""
    sessions = sorted(
        list(conversation_memory.sessions.values()),
        key=lambda session: session.updated_at,
        reverse=True,
    )
    recent_sessions = sessions[:4]
    recent_memories = jarvis_operator.memory_enforcer.list_memories(
        limit=6,
        runtime_context="dreamspace_runtime",
    )

    recent_topics = []
    active_projects = []
    recent_turns = []
    recent_corrections = []

    for session in recent_sessions:
        recent_topics.extend(list(session.memory_summary.recent_topics)[:3])
        active_projects.extend(list(session.memory_summary.active_projects)[:2])

        user_turns = [
            turn.content
            for turn in session.turns
            if turn.role == "user" and str(turn.content or "").strip()
        ]
        if user_turns:
            recent_turns.extend(user_turns[-2:])

        correction_state = session.metadata.get("corrigibility") or {}
        pending = (correction_state.get("pending") or {}).get("guidance")
        if pending:
            recent_corrections.append(pending)
        for item in list(correction_state.get("recent") or [])[:2]:
            summary = item.get("summary") or item.get("command")
            if summary:
                recent_corrections.append(summary)

    deduped_topics = list(dict.fromkeys(topic for topic in recent_topics if topic))
    deduped_projects = list(dict.fromkeys(project for project in active_projects if project))
    deduped_turns = list(dict.fromkeys(_clip_trace_text(turn, limit=180) for turn in recent_turns if turn))
    deduped_corrections = list(
        dict.fromkeys(_clip_trace_text(item, limit=180) for item in recent_corrections if item)
    )
    memory_texts = [
        _clip_trace_text(memory.get("text", ""), limit=180)
        for memory in recent_memories
        if memory.get("text")
    ]

    focus = (
        (recent_sessions[0].spiral_state.current_goal if recent_sessions else None)
        or (deduped_projects[0] if deduped_projects else None)
        or (deduped_topics[0] if deduped_topics else None)
        or "private local progress"
    )

    seed = (
        (deduped_turns[-1] if deduped_turns else None)
        or (memory_texts[0] if memory_texts else None)
        or "The operator is building something real and needs one clear next move."
    )

    style_cues = " ".join([focus, seed, *deduped_topics, *deduped_projects]).lower()
    style = (
        "mythic"
        if any(token in style_cues for token in ("veil", "story", "scene", "lore", "character", "chapter"))
        else "practical"
    )

    return {
        "focus": focus,
        "seed": seed,
        "style": style,
        "recent_topics": deduped_topics[:4],
        "active_projects": deduped_projects[:3],
        "recent_turns": deduped_turns[-4:],
        "recent_memories": memory_texts[:4],
        "recent_corrections": deduped_corrections[:2],
    }


def _dreamspace_generate(request_payload: dict) -> str:
    """Generate one Dreamspace entry through the current AAIS text model."""
    messages = list(request_payload.get("messages") or [])
    generation = dict(request_payload.get("generation") or {})

    def _generate():
        model, _ = init_ai()
        return model.generate_chat(
            messages,
            max_length=generation.get("max_length", 180),
            temperature=generation.get("temperature", 0.6),
            response_mode=generation.get("response_mode", "think"),
            routing_profile={
                "id": "dreamspace",
                "label": "Dream Weaver" if request_payload.get("style") == "mythic" else "Background Reflector",
                "adapter_mode": generation.get("response_mode", "think"),
            },
        )

    return _run_with_inference_lock(_generate)


def _dreamspace_emit_event(event_type: str, summary: str, payload: dict | None = None) -> None:
    """Mirror Dreamspace activity into the local V8 event log."""
    state = (dreamspace.snapshot(limit_dreams=1) or {}).get("status", "idle")
    v8_event_log.append(
        "dreamspace",
        event_type=event_type,
        state=state,
        summary=summary,
        payload=payload or {},
    )


def _classify_guard_target(path: str | None) -> str | None:
    """Map request paths onto guard targets, if this request should be blocked."""
    normalized = str(path or "").strip()
    if not normalized:
        return None

    if normalized == "/api/system/prewarm":
        return "inference"
    if SESSION_GUARD_PATH_RE.match(normalized):
        if normalized.endswith("/actions/execute"):
            return "action"
        return "turn"
    if (
        request.method in {"POST", "PATCH", "DELETE"}
        and (
            normalized.startswith("/api/jarvis/memory")
            or normalized.startswith("/api/jarvis/memory-smith/")
        )
    ):
        return "memory_write"
    if any(normalized.startswith(prefix) for prefix in GUARDED_INFERENCE_PREFIXES):
        return "inference"
    return None


dreamspace.configure_callbacks(
    generate_callback=_dreamspace_generate,
    context_callback=_dreamspace_context,
    idle_callback=_dreamspace_is_idle,
    event_callback=_dreamspace_emit_event,
)


def _serialize_session_payload(session):
    """Return a session payload plus the current system guard state."""
    _sync_super_nova_state(session)
    _attach_session_mission_context(session)
    _refresh_sovereignty_contract(session)
    _ensure_authority_state(session)
    response_trace = _sanitize_session_response_trace(session)
    canonical_trace_contract = _sync_canonical_trace_contract(session, response_trace=response_trace)
    companion_profile = _get_companion_surface_profile(
        persona_mode=session.metadata.get("persona_mode"),
        response_mode=session.metadata.get("response_mode"),
    )
    if _session_uses_companion_lane(session) and companion_profile:
        session.metadata["continuity_profile"] = session.metadata.get("continuity_profile") or dict(
            companion_profile["continuity_profile"]
        )
        session.metadata["continuity_prompt_block"] = None
    else:
        _build_continuity_profile(session)
    payload = session.to_dict()
    payload["response_trace"] = response_trace
    payload["canonical_trace_contract"] = canonical_trace_contract
    payload["mission_board"] = mission_board.snapshot(session_id=session.session_id)
    payload["mission_critic"] = session.metadata.get("mission_critic")
    payload["pending_action"] = session.metadata.get("pending_action")
    payload["action_lifecycle"] = session.metadata.get("action_lifecycle")
    payload["approval_audit"] = jarvis_operator.list_approval_audit(session.session_id, limit=8)
    payload["run_history"] = jarvis_operator.list_runs(session_id=session.session_id, limit=8)
    payload["memory_smith"] = jarvis_operator.memory_smith.snapshot()
    payload["provider_mind"] = session.metadata.get("provider_mind")
    payload["super_nova"] = session.metadata.get("super_nova_state")
    payload["system_guard"] = system_guard.snapshot(limit_events=4)
    payload["v9_runtime"] = v9_runtime.snapshot(limit=4)
    payload["v10_runtime"] = v10_runtime.snapshot(limit=4)
    payload["security_protocol"] = security_protocol_core.snapshot(limit_events=6)
    payload["immune_system"] = immune_system.snapshot(limit_events=6, limit_incidents=3)
    payload["governance"] = governance_layer.snapshot(limit_events=6, limit_requests=4)
    payload["continuity_profile"] = session.metadata.get("continuity_profile")
    payload["corrigibility"] = dict(
        session.metadata.get("corrigibility") or default_corrigibility_state()
    )
    payload["dreamspace"] = dreamspace.snapshot(limit_dreams=2)
    return payload


def _build_session_state_snapshot_record(session, *, reason: str | None = None) -> dict:
    """Capture one compact operator-facing session state snapshot."""
    authority_preferences, conflict_decisions = _ensure_authority_state(session)
    response_trace = _sanitize_session_response_trace(session)
    return {
        "id": f"state_{uuid4().hex[:10]}",
        "captured_at": datetime.now(UTC).isoformat(),
        "reason": " ".join(str(reason or "Operator snapshot").split()).strip(),
        "turn_count": len(session.turns),
        "session_state": session.session_state.to_dict(),
        "mode_guidance": dict(session.metadata.get("mode_guidance") or {}),
        "turn_contract": dict(session.metadata.get("turn_contract") or {}),
        "thread_contract": dict(session.metadata.get("thread_contract") or {}),
        "drift_state": dict(session.metadata.get("drift_state") or {}),
        "sovereignty_contract": dict(session.metadata.get("sovereignty_contract") or {}),
        "authority_preferences": authority_preferences,
        "knowledge_conflict_decisions": conflict_decisions,
        "provider_notice": dict(session.metadata.get("provider_notice") or {}),
        "pending_action": dict(session.metadata.get("pending_action") or {}) if session.metadata.get("pending_action") else None,
        "action_lifecycle": dict(session.metadata.get("action_lifecycle") or {}) if session.metadata.get("action_lifecycle") else None,
        "response_trace": dict(response_trace or {}) if response_trace else None,
        "canonical_trace_contract": dict(session.metadata.get("canonical_trace_contract") or {}),
    }


def _append_session_state_snapshot(session, *, reason: str | None = None) -> dict:
    """Store one bounded session snapshot for later operator comparison."""
    snapshot = _build_session_state_snapshot_record(session, reason=reason)
    snapshots = list(session.metadata.get("state_snapshots") or [])
    snapshots.append(snapshot)
    session.metadata["state_snapshots"] = snapshots[-8:]
    return snapshot


_STATE_DIFF_FIELDS = [
    ("turn_count", "Turn count"),
    ("session_state.current_state", "Lifecycle state"),
    ("mode_guidance.effective_mode", "Resolved mode"),
    ("mode_guidance.resolved_scope", "Resolved scope"),
    ("turn_contract.contract_label", "Turn contract"),
    ("turn_contract.resolved_voice", "Resolved voice"),
    ("thread_contract.mode", "Thread contract mode"),
    ("drift_state.status", "Anti-drift status"),
    ("sovereignty_contract.state_writer", "Sovereign writer"),
    ("provider_notice.status", "Fallback state"),
    ("canonical_trace_contract.response_contract", "Response trace contract"),
    ("canonical_trace_contract.contract_label", "Canonical contract"),
    ("canonical_trace_contract.execution_lane", "Execution lane"),
    ("response_trace.fallback", "Fallback trace flag"),
    ("pending_action.id", "Pending action"),
    ("action_lifecycle.status", "Action lifecycle"),
    ("authority_preferences.preset", "Authority preset"),
    ("authority_preferences.primary_source", "Surface priority"),
    ("authority_preferences.truth_scope_lock.scope", "Truth-scope lock"),
]


def _nested_state_value(payload: dict | None, dotted_path: str):
    """Resolve one dotted-path value from a bounded state snapshot."""
    current = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _build_session_state_diff(session, *, snapshot_id: str | None = None) -> dict:
    """Compare the current session state against one stored snapshot."""
    current = _build_session_state_snapshot_record(session, reason="Current session state")
    snapshots = list(session.metadata.get("state_snapshots") or [])
    baseline = None
    if snapshot_id:
        baseline = next((item for item in snapshots if item.get("id") == snapshot_id), None)
    elif snapshots:
        baseline = snapshots[-1]

    if baseline is None:
        return {
            "baseline": None,
            "current": {
                "captured_at": current.get("captured_at"),
                "turn_count": current.get("turn_count"),
            },
            "changes": [],
            "changed": False,
            "summary": "No state snapshot is available yet.",
        }

    changes = []
    for field, label in _STATE_DIFF_FIELDS:
        before = _nested_state_value(baseline, field)
        after = _nested_state_value(current, field)
        if before == after:
            continue
        changes.append(
            {
                "field": field,
                "label": label,
                "before": before,
                "after": after,
            }
        )

    return {
        "baseline": {
            "id": baseline.get("id"),
            "reason": baseline.get("reason"),
            "captured_at": baseline.get("captured_at"),
            "turn_count": baseline.get("turn_count"),
        },
        "current": {
            "captured_at": current.get("captured_at"),
            "turn_count": current.get("turn_count"),
        },
        "changes": changes,
        "changed": bool(changes),
        "summary": (
            f"{len(changes)} state change(s) detected from {baseline.get('reason') or 'snapshot'}."
            if changes
            else "Current state matches the selected snapshot."
        ),
    }


def _flush_fallback_residue(session) -> dict:
    """Clear leftover fallback-local residue without touching mission state."""
    cleared = {
        "provider_notice": bool(session.metadata.get("provider_notice")),
        "response_trace_fallback": bool((session.metadata.get("response_trace") or {}).get("fallback")),
        "model_route": bool(session.metadata.get("model_route")),
    }
    session.metadata["provider_notice"] = None
    session.metadata["drift_state"] = None
    model_route = session.metadata.get("model_route")
    if isinstance(model_route, dict) and str(model_route.get("provider_reason") or "").startswith("fallback_from_"):
        session.metadata["model_route"] = None
    response_trace = session.metadata.get("response_trace")
    if isinstance(response_trace, dict):
        response_trace.pop("fallback", None)
    turn_contract = session.metadata.get("turn_contract")
    if isinstance(turn_contract, dict):
        turn_contract["provider_fallback"] = False
    _refresh_sovereignty_contract(session)
    return cleared


def _hard_reset_session_state(session) -> dict:
    """Reset session-scoped runtime state while preserving mission context and operator configuration."""
    system_turns = [turn for turn in session.turns if turn.role == "system"]
    preserved = {
        "persona_mode": session.metadata.get("persona_mode"),
        "requested_response_mode": session.metadata.get("requested_response_mode"),
        "response_mode": session.metadata.get("response_mode"),
        "preferred_provider": session.metadata.get("preferred_provider"),
        "provider_mode": session.metadata.get("provider_mode"),
        "provider_fallback": session.metadata.get("provider_fallback"),
        "requested_specialists": list(session.metadata.get("requested_specialists") or []),
        "requested_specialist_preset": session.metadata.get("requested_specialist_preset"),
        "policy_status": dict(session.metadata.get("policy_status") or default_policy_status()),
        "mission_board": session.metadata.get("mission_board"),
        "authority_preferences": normalize_authority_preferences(
            session.metadata.get("authority_preferences")
        ),
        "knowledge_conflict_decisions": normalize_knowledge_conflict_decisions(
            session.metadata.get("knowledge_conflict_decisions")
        ),
    }
    session.turns = system_turns
    session.updated_at = datetime.now(UTC)
    session.spiral_state = type(session.spiral_state)()
    session.memory_summary = type(session.memory_summary)()
    session.session_state = type(session.session_state)()
    session.metadata.update(
        {
            **preserved,
            "provider_notice": None,
            "model_route": None,
            "god_brain": None,
            "mode_guidance": None,
            "last_effective_response_mode": None,
            "last_selector_scope": "operator_task",
            "last_selector_voice": "jarvis",
            "corrigibility": default_corrigibility_state(),
            "corrigibility_prompt_block": None,
            "continuity_profile": None,
            "continuity_prompt_block": None,
            "mission_critic": None,
            "pending_action": None,
            "action_lifecycle": None,
            "action_registry": {},
            "turn_contract": None,
            "last_turn_contract": None,
            "thread_contract": None,
            "drift_state": None,
            "sovereignty_contract": None,
            "mode_freeze": None,
            "state_snapshots": [],
            "otem_state": None,
            "forge_last_code": None,
            "forge_last_evaluation": None,
            "evolve_last_job": None,
            "persistent_memories": [],
            "workspace_context": None,
            "live_research": None,
            "urg_library_context": None,
            "browser_verification": None,
            "provider_mind": None,
            "response_trace": None,
            "canonical_trace_contract": None,
            "specialist_profile": None,
            "writing_focus": None,
        }
    )
    _attach_session_mission_context(session)
    return {
        "cleared_turns": max(0, len(system_turns)),
        "summary": "Session-scoped state was reset while mission context and operator configuration were preserved.",
    }


def _broadcast_system_guard_update(action: str, snapshot: dict) -> None:
    """Mirror system guard transitions into the V8 session log for active sessions."""
    if snapshot.get("status") == "nominal":
        dreamspace.resume(reason=f"System Guard {action} restored normal operation.")
    elif action in {"safe_stop", "stop", "hard_stop"}:
        dreamspace.stop(reason=f"System Guard {action} stopped background Dreamspace work.")
    else:
        dreamspace.pause(reason=f"System Guard {action} paused Dreamspace.")

    for session in list(conversation_memory.sessions.values()):
        if snapshot.get("status") == "nominal":
            _transition_session_state(
                session,
                "ready",
                summary="System Guard resumed normal operation for this session.",
                reason=f"system_guard_{action}",
                event_type="system_guard_updated",
                payload={"action": action, "system_guard": snapshot},
            )
            continue

        _transition_session_state(
            session,
            "degraded",
            summary=snapshot.get("summary", "System Guard blocked new execution."),
            reason=f"system_guard_{action}",
            event_type="system_guard_updated",
            payload={"action": action, "system_guard": snapshot},
        )


def _build_system_guard_block_response(decision: dict, session=None):
    """Return a consistent JSON error payload when the guard blocks a request."""
    snapshot = decision.get("system_guard") or system_guard.snapshot(limit_events=4)
    if session:
        _transition_session_state(
            session,
            "degraded",
            summary=decision.get("summary", "System Guard blocked this request."),
            reason="system_guard_blocked",
            event_type="system_guard_blocked",
            payload={"guard_target": decision.get("target"), "system_guard": snapshot},
        )
        payload = _build_chat_runtime_payload(session, session.session_id)
        payload.update(
            {
                "error": decision.get("summary", "System Guard blocked this request."),
                "system_guard": snapshot,
            }
        )
        return jsonify(payload), decision.get("status_code", 423)

    return jsonify(
        {
            "error": decision.get("summary", "System Guard blocked this request."),
            "system_guard": snapshot,
            "guard_target": decision.get("target"),
            "guidance": decision.get("guidance", []),
        }
    ), decision.get("status_code", 423)


def _release_ai_runtime():
    """Drop the local runtime so Safe Stop can cool the machine down."""
    global ai_model, streaming_generator, ai_mode, ai_init_error

    def release():
        global ai_model, streaming_generator, ai_mode, ai_init_error
        with ai_init_lock:
            ai_model = None
            streaming_generator = None
            ai_mode = None
            ai_init_error = None
            gc.collect()
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

    _run_with_inference_lock(release)


def _clear_active_sessions(reason: str) -> dict:
    """Drop live conversation sessions during a hard stop."""
    with conversation_memory._lock:
        session_ids = list(conversation_memory.sessions.keys())
        cleared_count = len(session_ids)
        conversation_memory.sessions.clear()
    logger.warning(
        "System Guard hard stop cleared %s active session(s): %s | reason=%s",
        cleared_count,
        ", ".join(session_ids[:10]) if session_ids else "none",
        reason,
    )
    return {
        "cleared_session_count": cleared_count,
        "cleared_session_ids": session_ids,
    }


def _active_break_glass_state() -> dict:
    """Return the current governance break-glass state."""
    return governance_layer.snapshot(limit_events=0, limit_requests=0).get("active_break_glass") or {}


def _build_caller_context(
    *,
    session=None,
    actor_id: str | None = None,
    actor_role: str | None = None,
    capabilities=None,
    mode: str | None = None,
) -> CallerContext:
    """Build the shared caller context used by the security brain."""
    capability_list = list(capabilities or [])
    if "tool:network" not in capability_list:
        capability_list.append("tool:network")
    return CallerContext(
        id=str(actor_id or (session.session_id if session else "local_operator")),
        role=str(actor_role or "owner").strip().lower() or "owner",
        capabilities=capability_list,
        mode=str(mode or (session.spiral_state.active_mode if session else "normal")).strip().lower() or "normal",
        tenant_id="local",
        session_id=session.session_id if session else None,
    )


def _run_security_check(
    *,
    caller: CallerContext,
    resource: ResourceMeta,
    action: Action,
    details: dict | None = None,
) -> dict:
    """Run the unified security check and feed the immune system."""
    decision = security_protocol_core.check_action(
        caller,
        resource,
        action,
        immune_snapshot=immune_system.snapshot(limit_events=0, limit_incidents=0),
        break_glass={"active": _active_break_glass_state()},
        details=details,
    )
    latest_events = security_protocol_core.list_events(limit=1)
    immune_update = immune_system.observe_security_event(latest_events[-1]) if latest_events else None
    return {
        "decision": decision.to_dict(),
        "immune": immune_update,
        "event": latest_events[-1] if latest_events else None,
    }


def _build_continuity_profile(session, operator_name: str | None = None) -> dict:
    """Refresh and attach the continuity profile for this session."""
    continuity_profile = continuity_profile_store.refresh_from_session(
        session,
        tenant_id="local",
        user_id=str(operator_name or "operator").strip().lower().replace(" ", "_") or "operator",
    )
    session.metadata["continuity_profile"] = continuity_profile
    session.metadata["continuity_prompt_block"] = continuity_profile_store.build_prompt_block(
        continuity_profile_store.get_profile(
            tenant_id="local",
            user_id=str(operator_name or "operator").strip().lower().replace(" ", "_") or "operator",
        )
    )
    return continuity_profile


def _build_security_block_response(security_result: dict, *, status_code: int = 403):
    """Return a consistent JSON error when the unified policy brain blocks an action."""
    decision = dict(security_result.get("decision") or {})
    return jsonify(
        {
            "error": decision.get("summary") or decision.get("reason") or "Action blocked by security policy.",
            "security_decision": decision,
            "security_event": security_result.get("event"),
            "immune_update": security_result.get("immune"),
        }
    ), status_code


@app.before_request
def before_request():
    """Track request timing and enforce the local system guard."""
    import time as _time

    request._start_time = _time.perf_counter()
    guard_target = _classify_guard_target(request.path)
    if not guard_target:
        return None

    decision = system_guard.evaluate_target(guard_target)
    if decision.get("allowed", True):
        return None

    session_match = SESSION_GUARD_PATH_RE.match(request.path or "")
    session = None
    if session_match:
        session = conversation_memory.get_session(session_match.group("session_id"))
    return _build_system_guard_block_response(decision, session=session)


@app.after_request
def after_request(response):
    """Add performance timing header to every response"""
    import time as _time
    start = getattr(request, "_start_time", None)
    if start:
        elapsed_ms = (_time.perf_counter() - start) * 1000
        response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.1f}"
    return response


# ──────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    payload = _build_ai_runtime_status()
    payload.update(
        {
            "status": "healthy",
            "service": "AAIS Multi-Modal AI",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "system_guard": system_guard.snapshot(limit_events=4),
            "dreamspace": dreamspace.snapshot(limit_dreams=2),
        }
    )
    return jsonify(payload)


@app.route("/api/system/prewarm", methods=["POST"])
def prewarm_system():
    """Initialize the local model ahead of the first real chat turn."""
    try:
        model, _ = bootstrap_ai_runtime(reason="prewarm", prefer_real=True)
        payload = _build_ai_runtime_status()
        payload.update(
            {
                "status": "ready",
                "ai_status": "initialized" if model is not None else "not_initialized",
                "dreamspace": dreamspace.snapshot(limit_dreams=2),
            }
        )
        return jsonify(payload)
    except Exception as e:
        logger.error(f"Error in prewarm_system: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/system/guard", methods=["GET"])
def get_system_guard():
    """Return the current local system guard posture."""
    payload = _build_ai_runtime_status()
    payload.update(
        {
            "system_guard": system_guard.snapshot(limit_events=10),
            "dreamspace": dreamspace.snapshot(limit_dreams=3),
        }
    )
    return jsonify(payload)


@app.route("/api/system/dreamspace", methods=["GET"])
def get_dreamspace():
    """Return the current Dreamspace posture and recent background reflections."""
    payload = _build_ai_runtime_status()
    payload.update(
        {
            "system_guard": system_guard.snapshot(limit_events=6),
            "dreamspace": dreamspace.snapshot(limit_dreams=5),
            "presentation": dreamspace.present_dreams(),
        }
    )
    return jsonify(payload)


@app.route("/api/system/dreamspace", methods=["POST"])
def update_dreamspace():
    """Start, pause, stop, resume, or trigger Dreamspace manually."""
    try:
        data = request.json or {}
        action = " ".join(str(data.get("action") or "").lower().split()).strip().replace("-", "_")
        reason = data.get("reason") or "Operator updated Dreamspace from the Jarvis console."

        if action == "start":
            snapshot = dreamspace.start(reason=reason)
        elif action == "pause":
            snapshot = dreamspace.pause(reason=reason)
        elif action in {"stop", "safe_stop"}:
            snapshot = dreamspace.stop(reason=reason)
        elif action == "resume":
            snapshot = dreamspace.resume(reason=reason)
        elif action in {"run_once", "dream_now"}:
            snapshot = dreamspace.run_once(reason=reason)
        else:
            return jsonify({"error": "action must be one of start, pause, stop, resume, or run_once"}), 400

        return jsonify(
            {
                "requested_model_mode": _get_model_mode(),
                "active_model_mode": ai_mode,
                "ai_status": "initialized" if ai_model is not None else "not_initialized",
                "system_guard": system_guard.snapshot(limit_events=6),
                "dreamspace": snapshot,
                "presentation": dreamspace.present_dreams(),
            }
        )
    except Exception as e:
        logger.error(f"Error updating Dreamspace: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/system/guard", methods=["POST"])
def update_system_guard():
    """Pause, safe-stop, or resume the local runtime."""
    try:
        data = request.json or {}
        action = " ".join(str(data.get("action") or "").lower().split()).strip().replace("-", "_")
        reason = data.get("reason") or "Operator request from the Jarvis console."
        hard_stop_effects = None
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="system_guard", actor_role="owner"),
            resource=ResourceMeta(
                id="system_guard",
                type=ResourceType.CONFIG,
                category="system_guard",
                sensitivity=10 if action in {"hard_stop", "safe_stop", "stop"} else 8,
            ),
            action=Action.CHANGE_MODE,
            details={"route": "/api/system/guard", "requested_action": action},
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)

        if action == "pause":
            snapshot = system_guard.pause(reason=reason)
        elif action in {"safe_stop", "stop"}:
            snapshot = system_guard.safe_stop(reason=reason)
            _release_ai_runtime()
        elif action == "hard_stop":
            hard_stop_effects = _clear_active_sessions(reason)
            snapshot = system_guard.hard_stop(
                reason=(
                    f"{reason} Cleared {hard_stop_effects['cleared_session_count']} active session(s) and locked memory writes."
                )
            )
            _release_ai_runtime()
        elif action == "resume":
            snapshot = system_guard.resume(reason=reason)
        else:
            return jsonify({"error": "action must be one of pause, safe_stop, hard_stop, or resume"}), 400

        _broadcast_system_guard_update(action, snapshot)
        governance_layer.record_override(
            actor_id="owner_local",
            actor_role="owner",
            target=f"system_guard:{action}",
            details={"system_guard": snapshot},
            reason=reason,
        )
        requested_mode = _get_model_mode()
        status = "initialized" if ai_model is not None else "not_initialized"
        payload = {
            "requested_model_mode": requested_mode,
            "active_model_mode": ai_mode,
            "ai_status": status,
            "system_guard": snapshot,
            "security_decision": security_result["decision"],
            "immune_system": immune_system.snapshot(limit_events=6, limit_incidents=3),
            "governance": governance_layer.snapshot(limit_events=6, limit_requests=4),
            "module_governance": module_governance.snapshot(limit_events=6, limit_modules=6),
            "dreamspace": dreamspace.snapshot(limit_dreams=3),
        }
        if hard_stop_effects:
            payload["hard_stop"] = hard_stop_effects
        return jsonify(
            payload
        )
    except Exception as e:
        logger.error(f"Error updating system guard: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Text Generation
# ──────────────────────────────────────────────

@app.route("/api/text/generate", methods=["POST"])
def generate_text():
    """Generate text from prompt."""
    try:
        data = request.json or {}
        prompt = data.get("prompt")
        max_length = _coerce_max_length(data.get("max_length"))
        temperature = _coerce_temperature(data.get("temperature"))

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        result = _run_with_inference_lock(
            lambda: init_ai()[0].generate_text(prompt, max_length, temperature)
        )
        return jsonify({"generated_text": result})

    except Exception as e:
        logger.error(f"Error in generate_text: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Streaming Text Generation (SSE)
# ──────────────────────────────────────────────

@app.route("/api/text/stream", methods=["POST"])
def stream_text():
    """Stream text generation token-by-token via Server-Sent Events."""
    try:
        data = request.json or {}
        prompt = data.get("prompt")
        max_new_tokens = _coerce_max_length(data.get("max_new_tokens"))
        temperature = _coerce_temperature(data.get("temperature"))

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        def locked_stream():
            with ai_inference_lock:
                _, streamer = init_ai()
                yield from streamer.generate_stream(
                    prompt=prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                )

        # Ensure the final cleaned response is emitted to any console handler
        # by passing a final_emitter that invokes the model's clean output gate.
        return Response(
            create_sse_generator(
                locked_stream(),
                final_emitter=(lambda text: init_ai()[0]._emit_clean_response(text)),
            ),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        logger.error(f"Error in stream_text: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Image Endpoints
# ──────────────────────────────────────────────

def _attach_image_operator_assist(result, include_operator_assist=False, operator_context=None):
    """Optionally enrich image analysis with screenshot-to-action guidance."""
    if not include_operator_assist:
        return result

    payload = dict(result or {})
    payload["operator_assist"] = jarvis_operator.build_visual_operator_assist(
        payload,
        operator_context=operator_context,
    )
    return payload


@app.route("/api/image/analyze", methods=["POST"])
def analyze_image():
    """Analyze image and generate description."""
    try:
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "Image analysis is unavailable on this deployment."
            ) from exc

        if "image" not in request.files:
            return jsonify({"error": "Image file is required"}), 400

        image_file = request.files["image"]
        include_ocr = _coerce_bool(request.form.get("include_ocr"), default=False)
        include_ui = _coerce_bool(request.form.get("include_ui"), default=False)
        include_operator_assist = _coerce_bool(
            request.form.get("include_operator_assist"),
            default=False,
        )
        operator_context = request.form.get("operator_context")
        image = Image.open(image_file.stream).convert("RGB")

        result = _run_with_inference_lock(
            lambda: init_ai()[0].analyze_image(
                image,
                include_ocr=(include_ocr or include_operator_assist),
                include_ui=(include_ui or include_operator_assist),
            )
        )
        return jsonify(
            _attach_image_operator_assist(
                result,
                include_operator_assist=include_operator_assist,
                operator_context=operator_context,
            )
        )

    except RuntimeError as e:
        logger.warning(f"Image analysis unavailable: {str(e)}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error in analyze_image: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/image/ocr", methods=["POST"])
def extract_image_text():
    """Run OCR/document vision on an uploaded image."""
    try:
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "Image uploads are unavailable on this deployment."
            ) from exc

        if "image" not in request.files:
            return jsonify({"error": "Image file is required"}), 400

        image_file = request.files["image"]
        image = Image.open(image_file.stream).convert("RGB")
        from src.perception_gateway_organ import route_perception_entry

        result = route_perception_entry("document_vision", {"image": image})
        if not result.get("ok"):
            return jsonify({"error": result.get("error", "perception route failed")}), 503
        return jsonify(result.get("result") or result)
    except DocumentVisionUnavailable as e:
        logger.warning(f"Document vision unavailable: {str(e)}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error in extract_image_text: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/image/ui-analyze", methods=["POST"])
def analyze_image_ui():
    """Run screenshot/UI understanding on an uploaded image."""
    try:
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "Image uploads are unavailable on this deployment."
            ) from exc

        if "image" not in request.files:
            return jsonify({"error": "Image file is required"}), 400

        image_file = request.files["image"]
        include_operator_assist = _coerce_bool(
            request.form.get("include_operator_assist"),
            default=False,
        )
        operator_context = request.form.get("operator_context")
        image = Image.open(image_file.stream).convert("RGB")
        result = _run_with_inference_lock(
            lambda: init_ai()[0].analyze_image(
                image,
                include_ocr=True,
                include_ui=True,
            )
        )
        return jsonify(
            _attach_image_operator_assist(
                {
                    "description": result.get("description"),
                    "top_matches": result.get("top_matches"),
                    "ocr": result.get("ocr"),
                    "ui": result.get("ui"),
                },
                include_operator_assist=include_operator_assist,
                operator_context=operator_context,
            )
        )
    except (DocumentVisionUnavailable, UIVisionUnavailable) as e:
        logger.warning(f"UI vision unavailable: {str(e)}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error in analyze_image_ui: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/image/generate", methods=["POST"])
def generate_image():
    """Generate image from text prompt."""
    try:
        data = request.json or {}
        prompt = data.get("prompt")
        num_steps = data.get("num_inference_steps", 50)

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        image = _run_with_inference_lock(
            lambda: init_ai()[0].generate_image(prompt, num_steps)
        )

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({"image": image_base64, "format": "png"})

    except RuntimeError as e:
        logger.warning(f"Image generation disabled or unavailable: {str(e)}")
        return jsonify({"error": str(e)}), 503
    except ImportError as e:
        logger.warning(f"Image generation unavailable: {str(e)}")
        return jsonify(
            {"error": "Image generation is unavailable on this deployment."}
        ), 503
    except Exception as e:
        logger.error(f"Error in generate_image: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/multimodal/query", methods=["POST"])
def multimodal_query():
    """Process combined text and image query."""
    try:
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "Image uploads are unavailable on this deployment."
            ) from exc

        text_prompt = request.form.get("prompt")
        image = None

        if not text_prompt:
            return jsonify({"error": "Prompt is required"}), 400

        if "image" in request.files:
            image_file = request.files["image"]
            image = Image.open(image_file.stream).convert("RGB")

        result = _run_with_inference_lock(
            lambda: init_ai()[0].multimodal_query(text_prompt, image)
        )
        return jsonify(result)

    except RuntimeError as e:
        logger.warning(f"Multimodal image support unavailable: {str(e)}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error in multimodal_query: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Jarvis Memory / Workspace Tools
# ──────────────────────────────────────────────

@app.route("/api/jarvis/memory", methods=["GET"])
def list_jarvis_memories():
    """List persistent Jarvis memories."""
    try:
        query = request.args.get("query")
        category = request.args.get("category")
        truth_scope = normalize_truth_scope(request.args.get("truth_scope"), default="live")
        active_raw = request.args.get("active")
        sort = request.args.get("sort", "priority")
        limit = max(1, min(int(request.args.get("limit", 12)), 50))
        active = None
        if active_raw is not None:
            lowered = str(active_raw).strip().lower()
            if lowered in {"1", "true", "yes", "active"}:
                active = True
            elif lowered in {"0", "false", "no", "inactive"}:
                active = False
            else:
                raise ValueError("active must be true or false")
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_bank", actor_role="owner"),
            resource=ResourceMeta(
                id="memory_bank",
                type=ResourceType.MEMORY,
                category=category or "memory_bank",
                sensitivity=6,
            ),
            action=Action.READ_MEMORY,
            details={"route": "/api/jarvis/memory", "query": query or ""},
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        memories = jarvis_operator.memory_enforcer.list_memories(
            query=query,
            limit=limit,
            category=category,
            active=active,
            sort=sort,
            truth_scope=truth_scope,
            runtime_context="operator_runtime",
        )
        return jsonify(
            {
                "memories": memories,
                "truth_scope": truth_scope,
                "memory_board": jarvis_operator.memory_enforcer.get_memory_board_snapshot(
                    truth_scope=truth_scope
                ),
                "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
            }
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory list blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error listing Jarvis memories: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory/<memory_id>", methods=["GET"])
def get_jarvis_memory(memory_id):
    """Return one persistent Jarvis memory with rewrite history."""
    try:
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_bank", actor_role="owner"),
            resource=ResourceMeta(
                id=memory_id,
                type=ResourceType.MEMORY,
                category="memory_bank",
                sensitivity=6,
            ),
            action=Action.READ_MEMORY,
            details={"route": f"/api/jarvis/memory/{memory_id}"},
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        memory = jarvis_operator.memory_enforcer.get_memory(
            memory_id,
            runtime_context="operator_runtime",
        )
        if memory is None:
            return jsonify({"error": "Memory not found"}), 404
        return jsonify({"memory": memory, "memory_enforcer": jarvis_operator.memory_enforcer.last_audit()})
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory detail blocked by governance gateway for {memory_id}: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error reading Jarvis memory {memory_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory", methods=["POST"])
def add_jarvis_memory():
    """Add a persistent Jarvis memory note."""
    try:
        data = request.json or {}
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_bank", actor_role="owner"),
            resource=ResourceMeta(
                id="memory_bank",
                type=ResourceType.MEMORY,
                category=str(data.get("category") or "memory_bank"),
                sensitivity=7 if data.get("override") else 6,
            ),
            action=Action.WRITE_MEMORY,
            details={"route": "/api/jarvis/memory", "kind": data.get("kind", "memory")},
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        memory = jarvis_operator.memory_enforcer.add_memory(
            text=data.get("text") or data.get("content"),
            tags=data.get("tags"),
            pinned=bool(data.get("pinned", False)),
            source=data.get("source", "manual"),
            category=data.get("category"),
            priority=data.get("priority"),
            active=bool(data.get("active", True)),
            kind=data.get("kind", "memory"),
            override=bool(data.get("override", False)),
            scope=data.get("scope"),
            supersedes=data.get("supersedes"),
            why=data.get("why"),
            state_class=data.get("state_class"),
            truth_status=data.get("truth_status"),
            runtime_context="operator_runtime",
        )
        return jsonify(
            {
                **memory,
                "governance": jarvis_operator.memory_store.last_board_event(),
                "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
            }
        ), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory create blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error adding Jarvis memory: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory/override", methods=["POST"])
def add_jarvis_memory_override():
    """Add a high-priority override memory."""
    try:
        data = request.json or {}
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_bank", actor_role="owner"),
            resource=ResourceMeta(
                id="memory_override",
                type=ResourceType.MEMORY,
                category=str(data.get("category") or "override"),
                sensitivity=8,
            ),
            action=Action.WRITE_MEMORY,
            details={"route": "/api/jarvis/memory/override", "override": True},
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        memory = jarvis_operator.memory_enforcer.add_override(
            text=data.get("text") or data.get("content"),
            category=data.get("category", "override"),
            priority=data.get("priority"),
            scope=data.get("scope"),
            supersedes=data.get("supersedes"),
            source=data.get("source", "override"),
            why=data.get("why"),
            state_class=data.get("state_class"),
            truth_status=data.get("truth_status"),
            runtime_context="operator_runtime",
        )
        return jsonify(
            {
                **memory,
                "governance": jarvis_operator.memory_store.last_board_event(),
                "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
            }
        ), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory override blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error adding Jarvis memory override: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory/<memory_id>", methods=["DELETE"])
def delete_jarvis_memory(memory_id):
    """Delete a persistent Jarvis memory."""
    try:
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_bank", actor_role="owner"),
            resource=ResourceMeta(
                id=memory_id,
                type=ResourceType.MEMORY,
                category="memory_bank",
                sensitivity=7,
            ),
            action=Action.UPDATE_MEMORY,
            details={"route": f"/api/jarvis/memory/{memory_id}", "delete": True},
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        if jarvis_operator.memory_enforcer.delete_memory(
            memory_id,
            runtime_context="operator_runtime",
        ):
            return jsonify(
                {
                    "message": "Memory deleted",
                    "governance": jarvis_operator.memory_store.last_board_event(),
                    "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
                }
            )
        return jsonify({"error": "Memory not found"}), 404
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory delete blocked by governance gateway for {memory_id}: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error deleting Jarvis memory: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory/<memory_id>", methods=["PATCH"])
def update_jarvis_memory(memory_id):
    """Update memory text, categories, or pinned state."""
    try:
        data = request.json or {}
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_bank", actor_role="owner"),
            resource=ResourceMeta(
                id=memory_id,
                type=ResourceType.MEMORY,
                category=str(data.get("category") or "memory_bank"),
                sensitivity=8 if data.get("override") else 7,
            ),
            action=Action.UPDATE_MEMORY,
            details={"route": f"/api/jarvis/memory/{memory_id}", "fields": sorted(data.keys())},
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        memory = jarvis_operator.memory_enforcer.update_memory(
            memory_id=memory_id,
            text=data.get("text") if "text" in data else data.get("content"),
            tags=data.get("tags") if "tags" in data else None,
            pinned=data.get("pinned") if "pinned" in data else None,
            category=data.get("category") if "category" in data else None,
            priority=data.get("priority") if "priority" in data else None,
            active=data.get("active") if "active" in data else None,
            kind=data.get("kind") if "kind" in data else None,
            override=data.get("override") if "override" in data else None,
            scope=data.get("scope") if "scope" in data else None,
            supersedes=data.get("supersedes") if "supersedes" in data else None,
            why=data.get("why") if "why" in data else None,
            note=data.get("note") if "note" in data else None,
            state_class=data.get("state_class") if "state_class" in data else None,
            truth_status=data.get("truth_status") if "truth_status" in data else None,
            runtime_context="operator_runtime",
        )
        if memory is None:
            return jsonify({"error": "Memory not found"}), 404
        return jsonify(
            {
                **memory,
                "governance": jarvis_operator.memory_store.last_board_event(),
                "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
            }
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory update blocked by governance gateway for {memory_id}: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error updating Jarvis memory: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory/<memory_id>/archive", methods=["POST"])
def archive_jarvis_memory(memory_id):
    """Archive one memory while preserving its rewrite history."""
    try:
        data = request.json or {}
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_bank", actor_role="owner"),
            resource=ResourceMeta(
                id=memory_id,
                type=ResourceType.MEMORY,
                category="memory_bank",
                sensitivity=7,
            ),
            action=Action.UPDATE_MEMORY,
            details={"route": f"/api/jarvis/memory/{memory_id}/archive"},
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        memory = jarvis_operator.memory_enforcer.archive_memory(
            memory_id,
            reason=data.get("reason"),
            runtime_context="operator_runtime",
        )
        if memory is None:
            return jsonify({"error": "Memory not found"}), 404
        return jsonify(
            {
                "memory": memory,
                "governance": jarvis_operator.memory_store.last_board_event(),
                "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
            }
        )
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory archive blocked by governance gateway for {memory_id}: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error archiving Jarvis memory {memory_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory/merge", methods=["POST"])
def merge_jarvis_memories():
    """Merge duplicate or stale memories into one canonical record."""
    try:
        data = request.json or {}
        target_id = str(data.get("target_id") or "").strip()
        if not target_id:
            return jsonify({"error": "target_id is required"}), 400
        source_ids = data.get("source_ids")
        if not isinstance(source_ids, list):
            return jsonify({"error": "source_ids must be a list"}), 400
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_bank", actor_role="owner"),
            resource=ResourceMeta(
                id=target_id,
                type=ResourceType.MEMORY,
                category="memory_bank_merge",
                sensitivity=8,
            ),
            action=Action.UPDATE_MEMORY,
            details={
                "route": "/api/jarvis/memory/merge",
                "source_count": len(source_ids),
            },
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        decision = jarvis_operator.request_memory_merge(
            target_id=target_id,
            source_ids=source_ids,
            content=data.get("content"),
            why=data.get("why"),
            note=data.get("note"),
        )
        memory = decision.get("memory")
        if memory is None and decision.get("reason") == "rejected":
            return jsonify({"error": "Target memory not found"}), 404
        if not decision.get("merged"):
            return jsonify({"error": decision.get("detail") or "Memory merge was rejected.", "decision": decision}), 400
        return jsonify({"memory": memory, "decision": decision})
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory merge blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error merging Jarvis memories: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory/board", methods=["GET"])
def get_jarvis_memory_board():
    """Return the installed Jarvis memory-board layout and module cards."""
    try:
        truth_scope = normalize_truth_scope(request.args.get("truth_scope"), default="live")
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_board", actor_role="owner"),
            resource=ResourceMeta(
                id="memory_board",
                type=ResourceType.MEMORY,
                category="memory_board",
                sensitivity=5,
            ),
            action=Action.READ_MEMORY,
            details={"route": "/api/jarvis/memory/board"},
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        board_snapshot = jarvis_operator.memory_enforcer.get_memory_board_snapshot(
            truth_scope=truth_scope
        )
        return jsonify(
            {
                "memory_board": board_snapshot,
                "jarvis_memory_board": to_memory_board_envelope(board_snapshot),
                "truth_scope": truth_scope,
                "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
            }
        )
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory board snapshot blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error reading Jarvis memory board: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory/board/install", methods=["POST"])
def install_jarvis_memory_board_module():
    """Install a memory-board module only through the protected operator surface."""
    try:
        data = request.json or {}
        slot_id = str(data.get("slot_id") or "").strip()
        module = data.get("module")
        if not slot_id:
            return jsonify({"error": "slot_id is required"}), 400
        if not isinstance(module, dict):
            return jsonify({"error": "module must be an object"}), 400
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_board", actor_role="owner"),
            resource=ResourceMeta(
                id=slot_id,
                type=ResourceType.MEMORY,
                category="memory_board_install",
                sensitivity=9,
            ),
            action=Action.UPDATE_MEMORY,
            details={
                "route": "/api/jarvis/memory/board/install",
                "slot_id": slot_id,
                "module_id": str(module.get("module_id") or "").strip(),
            },
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        result = jarvis_operator.memory_enforcer.install_memory_module(
            slot_id,
            module,
            runtime_context="operator_runtime",
        )
        return jsonify({"result": _serialize_api_payload(result)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory board install blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error installing Jarvis memory board module: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory/board/swap", methods=["POST"])
def swap_jarvis_memory_board_module():
    """Swap a memory-board module only through the protected operator surface."""
    try:
        data = request.json or {}
        slot_id = str(data.get("slot_id") or "").strip()
        module = data.get("module")
        migration_records = data.get("migration_records")
        if not slot_id:
            return jsonify({"error": "slot_id is required"}), 400
        if not isinstance(module, dict):
            return jsonify({"error": "module must be an object"}), 400
        if migration_records is not None and not isinstance(migration_records, list):
            return jsonify({"error": "migration_records must be a list"}), 400
        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="memory_board", actor_role="owner"),
            resource=ResourceMeta(
                id=slot_id,
                type=ResourceType.MEMORY,
                category="memory_board_swap",
                sensitivity=9,
            ),
            action=Action.UPDATE_MEMORY,
            details={
                "route": "/api/jarvis/memory/board/swap",
                "slot_id": slot_id,
                "module_id": str(module.get("module_id") or "").strip(),
                "migration_count": len(migration_records or []),
            },
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)
        result = jarvis_operator.memory_enforcer.swap_memory_module(
            slot_id,
            module,
            migration_records=migration_records,
            runtime_context="operator_runtime",
        )
        return jsonify({"result": _serialize_api_payload(result)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Memory board swap blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error swapping Jarvis memory board module: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/capability-bridge", methods=["GET"])
@app.route("/api/jarvis/capability-bridge/status", methods=["GET"])
def get_capability_bridge():
    """Expose the governed capability bridge registry and recent audit events."""
    try:
        snapshot = jarvis_operator.capability_bridge_snapshot()
        return jsonify(
            {
                **snapshot,
                "capability_service_bridge": to_bridge_envelope(snapshot),
            }
        )
    except Exception as e:
        logger.error(f"Error reading capability bridge snapshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/pipeline/<turn_id>", methods=["GET"])
def get_governed_pipeline_inspect(turn_id: str):
    """Return a schema-shaped governed pipeline trace for one turn."""
    try:
        session_id = str(request.args.get("session_id") or "").strip()
        if not session_id:
            return (
                jsonify(
                    {
                        "error": "session_id query parameter is required",
                        "claim_label": "asserted",
                    }
                ),
                400,
            )
        session = conversation_memory.get_session(session_id)
        if session is None:
            return (
                jsonify(
                    {
                        "error": "session not found",
                        "claim_label": "asserted",
                    }
                ),
                404,
            )
        response_trace = dict(session.metadata.get("response_trace") or {})
        governed_pipeline = dict(response_trace.get("governed_pipeline") or {})
        normalized_turn = str(turn_id or "").strip().lower()
        if normalized_turn in {"latest", "current", "last"}:
            pipeline_trace = governed_pipeline
        elif str(governed_pipeline.get("pipeline_id") or "") == turn_id:
            pipeline_trace = governed_pipeline
        else:
            history = list(session.metadata.get("governed_pipeline_history") or [])
            pipeline_trace = next(
                (
                    dict(entry)
                    for entry in history
                    if str(entry.get("pipeline_id") or "") == turn_id
                ),
                {},
            )
        if not pipeline_trace:
            return (
                jsonify(
                    {
                        "error": "governed pipeline trace not found for turn",
                        "turn_id": turn_id,
                        "claim_label": "asserted",
                    }
                ),
                404,
            )
        return jsonify(
            {
                "governed_pipeline": pipeline_trace,
                "governed_direct_pipeline": to_pipeline_envelope(pipeline_trace),
                "session_id": session_id,
                "turn_id": str(pipeline_trace.get("pipeline_id") or turn_id),
            }
        )
    except Exception as e:
        logger.error(f"Error reading governed pipeline trace: {e}")
        return jsonify({"error": str(e)}), 500


def _phase_gate_http_status(result: dict | None) -> int:
    phase_gate = dict((result or {}).get("phase_gate") or {})
    if phase_gate.get("decision") == "BLOCK":
        return 403
    return 200


def _build_memory_enforcer_block_response(exc: MemoryBoardEnforcerError):
    return (
        jsonify(
            {
                "error": str(exc),
                "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
            }
        ),
        403,
    )


def _build_chat_memory_enforcer_block_payload(session, session_id, exc: MemoryBoardEnforcerError):
    """Build a governed chat block payload when memory containment interrupts a turn."""
    return {
        "error": str(exc),
        "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
        **_build_chat_runtime_payload(session, session_id),
    }


@app.route("/api/jarvis/capability-bridge/execute", methods=["POST"])
def execute_capability_bridge_selection():
    """Execute one capability selection through the governed capability bridge."""
    try:
        data = request.json or {}
        if not isinstance(data, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        capability_id = str(data.get("capability") or "").strip().lower()
        action_id = str(data.get("action") or "").strip().lower()
        if not capability_id or not action_id:
            return jsonify({"error": "capability and action are required"}), 400

        args = data.get("args") or {}
        if not isinstance(args, dict):
            return jsonify({"error": "args must be a JSON object"}), 400

        execution_profile = data.get("execution_profile") or {}
        if not isinstance(execution_profile, dict):
            return jsonify({"error": "execution_profile must be a JSON object"}), 400

        result = jarvis_operator.capability_bridge.execute_selection(
            capability_id,
            action_id,
            args=args,
            execution_profile=execution_profile,
            runtime_context="operator_runtime",
        )
        trace = _build_tool_response_trace(
            "operator",
            tool_result=result.get("tool_result"),
            turn_contract={"contract_label": "direct_tool"},
            runtime_context="operator_runtime",
        )
        # Append contractor usage to the main Jarvis response trace for non-OTEM capability flows
        tool_res = result.get("tool_result") or {}
        if tool_res.get("via") and "live_" in str(tool_res.get("via")):
            _append_response_trace_step(
                trace,
                f"Contractor: {tool_res.get('via')} result attached (job info in tool_result)."
            )
        result["response_trace"] = trace
        result["capability_bridge"] = jarvis_operator.capability_bridge_snapshot()
        return jsonify(attach_ul_substrate(result)), _phase_gate_http_status(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error executing capability bridge selection: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workspace/projects", methods=["GET"])
def list_workspace_projects():
    """List top-level projects inside the operator workspace."""
    try:
        limit = max(1, min(int(request.args.get("limit", 12)), 50))
        projects = jarvis_operator.workspace_tools.list_projects(limit=limit)
        return jsonify({"projects": projects})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing workspace projects: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workspace/search", methods=["POST"])
def search_workspace():
    """Search file names and text content inside the local workspace."""
    try:
        data = request.json or {}
        query = data.get("query")
        limit = max(1, min(int(data.get("limit", 12)), 50))
        result = jarvis_operator.workspace_tools.search(query=query, limit=limit)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error searching workspace: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workspace/file", methods=["GET"])
def read_workspace_file():
    """Read a bounded preview of a workspace file."""
    try:
        relative_path = request.args.get("path")
        if not relative_path:
            return jsonify({"error": "Path is required"}), 400

        max_chars = max(200, min(int(request.args.get("max_chars", 4000)), 12000))
        file_payload = jarvis_operator.workspace_tools.read_file(
            relative_path,
            max_chars=max_chars,
        )
        return jsonify(file_payload)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error reading workspace file: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workspace/profile", methods=["GET"])
def get_workspace_profile():
    """Detect the active project profile using the evolving workbench layer."""
    try:
        path_prefix = request.args.get("path_prefix")
        return jsonify(jarvis_operator.detect_workspace_profile(path_prefix=path_prefix))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error detecting workspace profile: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workspace/symbols", methods=["POST"])
def list_workspace_symbols():
    """List code symbols using the evolving workbench layer."""
    try:
        data = request.json or {}
        query = data.get("query")
        limit = max(1, min(int(data.get("limit", 16)), 40))
        path_prefix = data.get("path_prefix")
        return jsonify(
            jarvis_operator.list_workspace_symbols(
                query=query,
                limit=limit,
                path_prefix=path_prefix,
            )
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing workspace symbols: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workspace/symbol", methods=["GET"])
def read_workspace_symbol():
    """Read one symbol body using the evolving workbench layer."""
    try:
        symbol = request.args.get("symbol")
        if not symbol:
            return jsonify({"error": "Symbol is required"}), 400
        path = request.args.get("path")
        path_prefix = request.args.get("path_prefix")
        return jsonify(
            jarvis_operator.read_workspace_symbol(
                symbol=symbol,
                path=path,
                path_prefix=path_prefix,
            )
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error reading workspace symbol: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workspace/repo-map", methods=["POST"])
def inspect_workspace_repo_map():
    """Inspect a focused repo map using the evolving workbench layer."""
    try:
        data = request.json or {}
        goal = data.get("goal")
        focus_path = data.get("focus_path")
        symbol = data.get("symbol")
        limit = max(4, min(int(data.get("limit", 12)), 18))
        path_prefix = data.get("path_prefix")
        return jsonify(
            jarvis_operator.inspect_workspace_repo_map(
                goal=goal,
                focus_path=focus_path,
                symbol=symbol,
                limit=limit,
                path_prefix=path_prefix,
            )
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error inspecting workspace repo map: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/runs", methods=["GET", "POST"])
def manage_run_ledger():
    """Create or list durable Jarvis runs."""
    try:
        if request.method == "POST":
            data = request.json or {}
            session_id = str(data.get("session_id") or "").strip()
            title = str(data.get("title") or "").strip()
            kind = str(data.get("kind") or "operator").strip() or "operator"
            if not session_id or not title:
                return jsonify({"error": "session_id and title are required"}), 400
            run = jarvis_operator.create_run(
                session_id=session_id,
                title=title,
                kind=kind,
                meta={
                    **dict(data.get("meta") or {}),
                    "cisiv_stage": data.get("cisiv_stage"),
                    "state_class": data.get("state_class"),
                    "truth_status": data.get("truth_status"),
                },
            )
            return jsonify(attach_ul_substrate({"run": run})), 201

        session_id = request.args.get("session_id")
        limit = max(1, min(int(request.args.get("limit", 20)), 100))
        truth_scope = normalize_truth_scope(request.args.get("truth_scope"), default="live")
        return jsonify(
            attach_ul_substrate(
                {
                    "runs": jarvis_operator.list_runs(session_id=session_id, limit=limit, truth_scope=truth_scope),
                    "truth_scope": truth_scope,
                }
            )
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error managing run ledger: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/runs/<run_id>", methods=["GET"])
def get_run_ledger_record(run_id):
    """Return one durable Jarvis run record."""
    try:
        run = jarvis_operator.get_run(run_id)
        if not run:
            return jsonify({"error": "Run not found"}), 404
        return jsonify(attach_ul_substrate({"run": run}))
    except Exception as e:
        logger.error(f"Error reading run ledger record: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/change-scope", methods=["POST"])
def analyze_change_scope():
    """Estimate blast radius and likely test impact for a change target."""
    try:
        data = request.json or {}
        impact = jarvis_operator.analyze_change_scope(
            file_path=data.get("file_path") or data.get("focus_path"),
            symbol=data.get("symbol"),
            goal=data.get("goal"),
            path_prefix=data.get("path_prefix"),
        )
        return jsonify(impact)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error analyzing change scope: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/tests/plan", methods=["POST"])
def build_test_oracle_plan():
    """Build a minimal verification plan for a proposed change."""
    try:
        data = request.json or {}
        change_impact = data.get("change_impact")
        if not isinstance(change_impact, dict):
            change_impact = jarvis_operator.analyze_change_scope(
                file_path=data.get("file_path") or data.get("focus_path"),
                symbol=data.get("symbol"),
                goal=data.get("goal"),
                path_prefix=data.get("path_prefix"),
            )
        workspace_context = data.get("workspace_context")
        if not isinstance(workspace_context, dict):
            workspace_context = jarvis_operator.build_workspace_context(
                str(data.get("goal") or data.get("file_path") or data.get("symbol") or "").strip(),
                force=True,
                reason="operator_request",
                auto_attached=False,
            )
        return jsonify(jarvis_operator.suggest_test_plan(change_impact, workspace_context=workspace_context))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error building test plan: {e}")
        return jsonify({"error": str(e)}), 500


def _summarize_forge_result(result: dict | None) -> dict:
    """Reduce Forge contractor output to an operator-safe summary."""

    payload = dict(result or {})
    result_body = dict(payload.get("result") or {})
    diffs = list(result_body.get("diffs") or [])
    paths = [str(item.get("path") or "").strip() for item in diffs if str(item.get("path") or "").strip()]
    if payload.get("ok") is False:
        error = dict(payload.get("error") or {})
        return {
            "ok": False,
            "code": error.get("code") or "contractor_error",
            "message": _sanitize_operator_surface_text(
                error.get("message") or "Forge contractor returned an error.",
                fallback_text="Forge contractor returned an error.",
            ),
        }
    return {
        "ok": True,
        "diff_count": len(diffs),
        "paths": paths[:6],
        "summary": f"Forge contractor returned {len(diffs)} bounded diff candidate(s).",
    }


def _summarize_forge_evaluation(result: dict | None) -> dict:
    """Reduce ForgeEval output to an operator-safe summary."""

    payload = dict(result or {})
    if payload.get("ok") is False:
        error = dict(payload.get("error") or {})
        return {
            "ok": False,
            "code": error.get("code") or "evaluation_error",
            "message": _sanitize_operator_surface_text(
                error.get("message") or "ForgeEval returned an error.",
                fallback_text="ForgeEval returned an error.",
            ),
        }
    result_body = dict(payload.get("result") or {})
    return {
        "ok": True,
        "score": result_body.get("score"),
        "summary": "ForgeEval returned a bounded evaluator result.",
        "details": dict(result_body.get("details") or {}),
    }


def _store_forge_session_summary(
    session,
    *,
    code_summary: dict | None = None,
    evaluation_summary: dict | None = None,
) -> None:
    """Attach the latest Forge summaries to the active session without storing raw artifacts."""

    if code_summary is not None:
        session.metadata["forge_last_code"] = dict(code_summary or {})
    if evaluation_summary is not None:
        session.metadata["forge_last_evaluation"] = dict(evaluation_summary or {})


def _build_forge_operator_snapshot(session_id: str | None = None) -> dict:
    """Expose Forge contractor/evaluator boundaries for the operator panel."""

    session = conversation_memory.get_session(session_id) if session_id else None
    return {
        "contractor": {
            "route": "/api/jarvis/forge/code",
            "repo_manager_route": "/api/jarvis/forge/repo-manager",
            "base_url": forge_client.base_url,
            "kinds": sorted(FORGE_VALID_KINDS),
            "boundary": "isolated contractor, review-gated, foundation-law envelope, no test execution, no patch apply",
            "review_gated": True,
            "contract_version": FORGE_LAW_CONTRACT_VERSION,
            "foundation_laws": list(FORGE_FOUNDATION_LAW_IDS),
            "latest": dict((session.metadata.get("forge_last_code") or {})) if session else None,
        },
        "evaluator": {
            "route": "/api/jarvis/forge/evaluate",
            "base_url": forge_eval_client.base_url,
            "modes": sorted(FORGE_EVAL_VALID_MODES),
            "boundary": "isolated evaluator, read-only scoring lane, no runtime mutation",
            "latest": dict((session.metadata.get("forge_last_evaluation") or {})) if session else None,
        },
    }


def _summarize_evolve_result(result: dict | None) -> dict:
    """Reduce EvolveEngine output to an operator-safe summary."""

    payload = dict(result or {})
    if payload.get("ok") is False:
        error = dict(payload.get("error") or {})
        return {
            "ok": False,
            "code": error.get("code") or "evolve_error",
            "message": _sanitize_operator_surface_text(
                error.get("message") or "EvolveEngine returned an error.",
                fallback_text="EvolveEngine returned an error.",
            ),
        }
    result_body = dict(payload.get("result") or {})
    history = list(result_body.get("history") or [])
    return {
        "ok": True,
        "best_score": result_body.get("best_score"),
        "generations_run": result_body.get("generations_run"),
        "evaluations": result_body.get("evaluations"),
        "hall_of_fame_count": result_body.get("hall_of_fame_count", 0),
        "hall_of_shame_count": result_body.get("hall_of_shame_count", 0),
        "summary": f"EvolveEngine completed {len(history)} generation(s) in the bounded evolve lane.",
    }


def _store_evolve_session_summary(session, evolve_summary: dict | None = None) -> None:
    """Attach the latest evolve summary to the active session without storing raw mutation blobs."""

    if evolve_summary is not None:
        session.metadata["evolve_last_job"] = dict(evolve_summary or {})


def _build_evolve_operator_snapshot(session_id: str | None = None) -> dict:
    """Expose EvolveEngine boundaries, traces, and mutation halls for the operator panel."""

    session = conversation_memory.get_session(session_id) if session_id else None
    return {
        "route": "/api/jarvis/evolve/run",
        "base_url": evolve_client.base_url,
        "evaluation_modes": sorted(EVOLVE_VALID_EVALUATION_MODES),
        "presets": jarvis_operator.list_evolution_presets(),
        "boundary": "isolated evolution lane, Jarvis-authorized, ForgeEval-scored, no direct patch authority",
        "trace_routes": {
            "job": "/api/jarvis/evolve/jobs/<job_id>",
            "job_evaluations": "/api/jarvis/evolve/jobs/<job_id>/evaluations",
            "run": "/api/jarvis/evolve/runs/<jarvis_run_id>",
            "hall_of_fame": "/api/jarvis/evolve/hall-of-fame",
            "hall_of_shame": "/api/jarvis/evolve/hall-of-shame",
            "forge_handoff": "/api/jarvis/evolve/jobs/<job_id>/handoff/forge",
        },
        "latest": dict((session.metadata.get("evolve_last_job") or {})) if session else None,
    }


@app.route("/api/jarvis/forge/code", methods=["POST"])
def run_forge_code():
    """Send one coding task through the isolated Forge contractor boundary."""
    try:
        data = request.json or {}
        task = str(data.get("task") or data.get("goal") or data.get("request") or "").strip()
        kind = str(data.get("kind") or "generate_diff").strip() or "generate_diff"
        session_id = str(data.get("session_id") or "").strip() or None
        session = None
        if not task:
            return jsonify({"error": "task is required"}), 400
        if session_id:
            session = conversation_memory.get_session(session_id)
            if session is None:
                return jsonify({"error": "session not found"}), 404

        workspace_context = data.get("workspace_context")
        if not isinstance(workspace_context, dict):
            workspace_context = jarvis_operator.build_workspace_context(
                task,
                result_limit=max(4, min(int(data.get("result_limit", 6)), 12)),
                file_limit=max(1, min(int(data.get("file_limit", 4)), 8)),
                file_chars=max(400, min(int(data.get("file_chars", 1800)), 5000)),
                reason="forge_request",
                auto_attached=False,
                force=True,
                query_hint=data.get("query_hint"),
            )

        forge_payload = jarvis_operator.request_forge_code(
            task,
            kind=kind,
            workspace_context=workspace_context,
            constraints=data.get("constraints"),
            style=data.get("style"),
            language=data.get("language"),
            target_scope=data.get("target_scope"),
            focus_files=data.get("focus_files"),
            excluded_files=data.get("excluded_files"),
            change_intent=data.get("change_intent"),
            max_change_budget=data.get("max_change_budget"),
        )
        forge_context_summary = jarvis_operator.summarize_forge_context(
            forge_payload.get("forge_context")
        )
        if session is not None:
            _store_forge_session_summary(
                session,
                code_summary={
                    "task_id": forge_payload["task_id"],
                    "task": forge_payload["task"],
                    "kind": forge_payload["kind"],
                    "auto_approve": forge_payload["auto_approve"],
                    "forge_context": forge_context_summary,
                    "result": _summarize_forge_result(forge_payload.get("result")),
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
        return jsonify(
            attach_ul_substrate(
                {
                    "task_id": forge_payload["task_id"],
                    "task": forge_payload["task"],
                    "kind": forge_payload["kind"],
                    "result": forge_payload["result"],
                    "auto_approve": forge_payload["auto_approve"],
                    "law_enforcement": dict(
                        forge_payload.get("law_enforcement")
                        or (forge_payload.get("result") or {}).get("law_enforcement")
                        or {}
                    ),
                    "ul_snapshot": dict(
                        forge_payload.get("ul_snapshot")
                        or (forge_payload.get("result") or {}).get("ul_snapshot")
                        or {}
                    ),
                    "workspace_context": workspace_context,
                    "forge_context": forge_context_summary,
                    "ul_substrate": forge_payload.get("ul_substrate"),
                    "ul_trace": forge_payload.get("ul_trace"),
                }
            )
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Forge contractor call failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error running Forge contractor: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/forge/repo-manager", methods=["POST"])
def run_forge_repo_manager():
    """Send one repo-manager request through the isolated Forge contractor boundary."""
    try:
        data = request.json or {}
        task = str(data.get("task") or data.get("goal") or data.get("request") or "").strip()
        session_id = str(data.get("session_id") or "").strip() or None
        session = None
        if not task:
            return jsonify({"error": "task is required"}), 400
        if session_id:
            session = conversation_memory.get_session(session_id)
            if session is None:
                return jsonify({"error": "session not found"}), 404

        workspace_context = data.get("workspace_context")
        requested_max_files = data.get("max_files_to_inspect")
        resolved_file_limit = (
            max(1, min(int(requested_max_files), 12))
            if requested_max_files not in ("", None)
            else max(1, min(int(data.get("file_limit", 6)), 12))
        )
        if not isinstance(workspace_context, dict):
            workspace_context = jarvis_operator.build_workspace_context(
                task,
                result_limit=max(4, resolved_file_limit),
                file_limit=resolved_file_limit,
                file_chars=max(400, min(int(data.get("file_chars", 1800)), 5000)),
                reason="forge_repo_manager",
                auto_attached=False,
                force=True,
                query_hint=data.get("query_hint"),
            )

        forge_payload = jarvis_operator.request_forge_repo_manager(
            task,
            workspace_context=workspace_context,
            constraints=data.get("constraints"),
            style=data.get("style"),
            language=data.get("language"),
            target_scope=data.get("target_scope"),
            focus_files=data.get("focus_files"),
            excluded_files=data.get("excluded_files"),
            change_intent=data.get("change_intent"),
            max_change_budget=data.get("max_change_budget"),
            validation_target=data.get("validation_target"),
            operation_mode=data.get("operation_mode"),
            max_files_to_inspect=data.get("max_files_to_inspect"),
            max_directory_depth=data.get("max_directory_depth"),
            file_path_allowlist=data.get("file_path_allowlist"),
            explicit_denylist=data.get("explicit_denylist"),
            no_execution_without_handoff=bool(data.get("no_execution_without_handoff", True)),
        )
        forge_context_summary = jarvis_operator.summarize_forge_context(
            forge_payload.get("forge_context")
        )
        if session is not None:
            _store_forge_session_summary(
                session,
                code_summary={
                    "task_id": forge_payload["task_id"],
                    "task": forge_payload["task"],
                    "kind": forge_payload["kind"],
                    "auto_approve": forge_payload["auto_approve"],
                    "forge_context": forge_context_summary,
                    "result": _summarize_forge_result(forge_payload.get("result")),
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
        return jsonify(
            attach_ul_substrate(
                {
                    "task_id": forge_payload["task_id"],
                    "task": forge_payload["task"],
                    "kind": forge_payload["kind"],
                    "result": forge_payload["result"],
                    "auto_approve": forge_payload["auto_approve"],
                    "law_enforcement": dict(
                        forge_payload.get("law_enforcement")
                        or (forge_payload.get("result") or {}).get("law_enforcement")
                        or {}
                    ),
                    "ul_snapshot": dict(
                        forge_payload.get("ul_snapshot")
                        or (forge_payload.get("result") or {}).get("ul_snapshot")
                        or {}
                    ),
                    "workspace_context": workspace_context,
                    "forge_context": forge_context_summary,
                    "ul_substrate": forge_payload.get("ul_substrate"),
                    "ul_trace": forge_payload.get("ul_trace"),
                }
            )
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Forge repo manager call failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error running Forge repo manager: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/forge/evaluate", methods=["POST"])
def run_forge_evaluation():
    """Send one evaluator request through the isolated ForgeEval boundary."""
    try:
        data = request.json or {}
        mode = str(data.get("mode") or "").strip()
        session_id = str(data.get("session_id") or "").strip() or None
        session = None
        if not mode:
            return jsonify({"error": "mode is required"}), 400
        if session_id:
            session = conversation_memory.get_session(session_id)
            if session is None:
                return jsonify({"error": "session not found"}), 404

        payload = data.get("payload")
        if not isinstance(payload, dict):
            payload = {
                key: data.get(key)
                for key in ("program", "patch", "repo", "config")
                if data.get(key) is not None
            }

        evaluation = jarvis_operator.request_forge_evaluation(
            mode,
            payload=payload,
            task_id=data.get("task_id"),
        )
        if session is not None:
            _store_forge_session_summary(
                session,
                evaluation_summary={
                    "task_id": evaluation["task_id"],
                    "mode": evaluation["mode"],
                    "result": _summarize_forge_evaluation(evaluation),
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
        return jsonify(attach_ul_substrate(evaluation))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"ForgeEval call failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error running ForgeEval: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/evolve/run", methods=["POST"])
def run_evolve_job():
    """Send one bounded evolution request through the isolated EvolveEngine lane."""

    try:
        data = request.json or {}
        task = str(data.get("task") or data.get("goal") or data.get("request") or "").strip()
        session_id = str(data.get("session_id") or "").strip() or None
        session = None
        if not task:
            return jsonify({"error": "task is required"}), 400
        if session_id:
            session = conversation_memory.get_session(session_id)
            if session is None:
                return jsonify({"error": "session not found"}), 404

        evolve_payload = jarvis_operator.request_evolution_job(
            task,
            preset=data.get("preset"),
            config=data.get("config"),
            evaluation=data.get("evaluation"),
            constraints=data.get("constraints"),
            job_id=data.get("job_id"),
            jarvis_run_id=data.get("jarvis_run_id"),
        )
        if session is not None:
            _store_evolve_session_summary(
                session,
                {
                    "job_id": evolve_payload["job_id"],
                    "task": evolve_payload["task"],
                    "preset": evolve_payload.get("preset"),
                    "evaluation": dict(evolve_payload.get("evaluation") or {}),
                    "constraints": dict(evolve_payload.get("constraints") or {}),
                    "result": _summarize_evolve_result(evolve_payload.get("result")),
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
        return jsonify(attach_ul_substrate(evolve_payload))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"EvolveEngine call failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error running EvolveEngine: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/evolve/presets", methods=["GET"])
def get_evolve_presets():
    """Expose the bounded evolve presets Jarvis can authorize."""

    try:
        return jsonify({"presets": jarvis_operator.list_evolution_presets()})
    except Exception as e:
        logger.error(f"Error reading evolve presets: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/evolve/jobs/<job_id>", methods=["GET"])
def get_evolve_job_trace(job_id: str):
    """Return one evolve job trace through the AAIS operator surface."""

    try:
        payload = jarvis_operator.get_evolution_job_trace(job_id)
        return jsonify(payload)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"EvolveEngine trace call failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error reading evolve job trace: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/evolve/jobs/<job_id>/evaluations", methods=["GET"])
def get_evolve_job_evaluations(job_id: str):
    """Return one evolve job's evaluation ledger through AAIS."""

    try:
        limit = max(1, min(int(request.args.get("limit", 200)), 1000))
        payload = jarvis_operator.get_evolution_job_evaluations(job_id, limit=limit)
        return jsonify(payload)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"EvolveEngine evaluation trace call failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error reading evolve job evaluations: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/evolve/runs/<jarvis_run_id>", methods=["GET"])
def get_evolve_run_trace(jarvis_run_id: str):
    """Return evolve jobs linked to one Jarvis run trace."""

    try:
        payload = jarvis_operator.get_evolution_run_trace(jarvis_run_id)
        return jsonify(payload)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"EvolveEngine run trace call failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error reading evolve run trace: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/evolve/jobs/<job_id>/handoff/forge", methods=["POST"])
def handoff_evolve_job_to_forge(job_id: str):
    """Route one evolve winner into Forge as a review-first contractor handoff."""

    try:
        data = request.json or {}
        session_id = str(data.get("session_id") or "").strip() or None
        session = None
        if session_id:
            session = conversation_memory.get_session(session_id)
            if session is None:
                return jsonify({"error": "session not found"}), 404

        payload = jarvis_operator.handoff_evolution_job_to_forge(
            job_id,
            task=data.get("task"),
            kind=str(data.get("kind") or "analyze").strip() or "analyze",
        )
        forge_payload = dict(payload.get("forge") or {})
        forge_result = dict(forge_payload.get("result") or {})
        forge_result_body = dict(forge_result.get("result") or {})
        analysis = dict(forge_result_body.get("analysis") or {})
        analysis_summary = str(analysis.get("summary") or "").strip()
        if analysis_summary:
            forge_payload["operator_safe_analysis_summary"] = _sanitize_operator_surface_text(
                analysis_summary,
                fallback_text="Forge analysis summary unavailable.",
            )
            payload["forge"] = forge_payload
        if session is not None:
            _store_forge_session_summary(
                session,
                code_summary={
                    "task_id": payload["forge"]["task_id"],
                    "task": payload["forge"]["task"],
                    "kind": payload["forge"]["kind"],
                    "auto_approve": payload["forge"]["auto_approve"],
                    "forge_context": jarvis_operator.summarize_forge_context(
                        payload["forge"].get("forge_context")
                    ),
                    "result": _summarize_forge_result(payload["forge"].get("result")),
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
        return jsonify(payload)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"EvolveEngine Forge handoff failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error handing evolve winner to Forge: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/evolve/hall-of-fame", methods=["GET"])
def get_evolve_hall_of_fame():
    """Return the latest successful mutations through AAIS."""

    try:
        limit = max(1, min(int(request.args.get("limit", 20)), 200))
        payload = jarvis_operator.list_evolution_hall_of_fame(limit=limit)
        return jsonify(payload)
    except RuntimeError as e:
        logger.error(f"EvolveEngine hall-of-fame call failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error reading evolve hall of fame: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/evolve/hall-of-shame", methods=["GET"])
def get_evolve_hall_of_shame():
    """Return the latest failed mutations through AAIS."""

    try:
        limit = max(1, min(int(request.args.get("limit", 20)), 200))
        payload = jarvis_operator.list_evolution_hall_of_shame(limit=limit)
        return jsonify(payload)
    except RuntimeError as e:
        logger.error(f"EvolveEngine hall-of-shame call failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error reading evolve hall of shame: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/evolve/maintenance/prune", methods=["POST"])
def prune_evolve_retention():
    """Prune retained evolve traces and mutation halls through AAIS."""

    try:
        data = request.json or {}
        payload = jarvis_operator.prune_evolution_retention(
            max_jobs=data.get("max_jobs"),
            max_hall_entries=data.get("max_hall_entries"),
            max_evaluations=data.get("max_evaluations"),
        )
        return jsonify(payload)
    except RuntimeError as e:
        logger.error(f"EvolveEngine prune call failed: {e}")
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Error pruning evolve retention: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/patch/plan", methods=["POST"])
def build_patchforge_plan():
    """Build a review-first patch plan from Jarvis workspace context."""
    try:
        data = request.json or {}
        goal = str(data.get("goal") or data.get("request") or "").strip()
        if not goal:
            return jsonify({"error": "goal is required"}), 400
        change_impact = data.get("change_impact")
        if not isinstance(change_impact, dict):
            change_impact = jarvis_operator.analyze_change_scope(
                file_path=data.get("file_path") or data.get("focus_path"),
                symbol=data.get("symbol"),
                goal=goal,
                path_prefix=data.get("path_prefix"),
            )
        workspace_context = data.get("workspace_context")
        if not isinstance(workspace_context, dict):
            workspace_context = jarvis_operator.build_workspace_context(
                " ".join(
                    piece
                    for piece in [
                        goal,
                        str(data.get("file_path") or data.get("focus_path") or "").strip(),
                        str(data.get("symbol") or "").strip(),
                    ]
                    if piece
                ),
                force=True,
                reason="builder_request",
                auto_attached=False,
            ) or {}
        test_plan = data.get("test_plan")
        if not isinstance(test_plan, dict):
            test_plan = jarvis_operator.suggest_test_plan(change_impact, workspace_context=workspace_context)
        plan = jarvis_operator.build_patch_plan(
            goal,
            workspace_context,
            change_impact=change_impact,
            test_plan=test_plan,
        )
        plan.update(_extract_external_suggestion_details(data))
        if data.get("state_class"):
            plan["state_class"] = data.get("state_class")
        if data.get("truth_status"):
            plan["truth_status"] = data.get("truth_status")
        review = jarvis_operator.create_patch_review(
            session_id=str(data.get("session_id") or "").strip() or None,
            patch_plan=plan,
        )
        return jsonify(
            attach_ul_substrate(
                {
                    "patch_plan": plan,
                    "summary": jarvis_operator.patchforge.summarize_patch(plan),
                    "patch_review": review,
                    "ul_substrate": review.get("ul_substrate"),
                    "ul_trace": review.get("ul_trace"),
                }
            )
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error building patch plan: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/patch/preview", methods=["POST"])
def preview_patchforge_plan():
    """Preview whether a PatchForge proposal still aligns with the current workspace."""
    try:
        data = request.json or {}
        patch_plan = data.get("patch_plan")
        if not isinstance(patch_plan, dict):
            review_id = str(data.get("review_id") or "").strip()
            if not review_id:
                return jsonify({"error": "patch_plan or review_id is required"}), 400
            review = jarvis_operator.get_patch_review(review_id)
            if not review:
                return jsonify({"error": "Patch review not found"}), 404
            patch_plan = dict(review.get("patch_plan") or {})
        return jsonify(attach_ul_substrate({"preview": jarvis_operator.preview_patch_plan(patch_plan)}))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error previewing patch plan: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/patch/reviews", methods=["GET"])
def list_patch_reviews():
    """List persisted PatchForge review records."""
    try:
        session_id = str(request.args.get("session_id") or "").strip() or None
        limit = max(1, min(int(request.args.get("limit", 20)), 100))
        truth_scope = normalize_truth_scope(request.args.get("truth_scope"), default="live")
        return jsonify(
            attach_ul_substrate(
                {
                    "reviews": jarvis_operator.list_patch_reviews(
                        session_id=session_id,
                        limit=limit,
                        truth_scope=truth_scope,
                    ),
                    "truth_scope": truth_scope,
                }
            )
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing patch reviews: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/patch/reviews/<review_id>", methods=["GET"])
def get_patch_review(review_id):
    """Return one persisted PatchForge review record."""
    try:
        review = jarvis_operator.get_patch_review(review_id)
        if not review:
            return jsonify({"error": "Patch review not found"}), 404
        return jsonify(attach_ul_substrate({"review": review}))
    except Exception as e:
        logger.error(f"Error reading patch review: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/patch/reviews/<review_id>/decision", methods=["POST"])
def decide_patch_review(review_id):
    """Record one patch review decision without applying workspace edits."""
    try:
        data = request.json or {}
        review = jarvis_operator.record_patch_review_decision(
            review_id,
            decision=data.get("decision"),
            note=data.get("note"),
            target_kind=data.get("target_kind") or "plan",
            target_index=data.get("target_index"),
        )
        if not review:
            return jsonify({"error": "Patch review not found"}), 404
        return jsonify(attach_ul_substrate({"review": review}))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error recording patch review decision: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/patch/reviews/<review_id>/apply", methods=["POST"])
def apply_patch_review_route(review_id):
    """Apply one accepted patch review and record it in the run ledger."""
    try:
        data = request.json or {}
        external_suggestion_details = _extract_external_suggestion_details(data)
        review = jarvis_operator.get_patch_review(review_id)
        if not review:
            return jsonify({"error": "Patch review not found"}), 404
        force_rerun = bool(data.get("force", False))

        security_result = _run_security_check(
            caller=_build_caller_context(actor_id="patch_apply", actor_role="owner"),
            resource=ResourceMeta(
                id=review_id,
                type=ResourceType.SYSTEM,
                category="patch_apply",
                sensitivity=9,
            ),
            action=Action.ACCESS_FILESYSTEM,
            details={"route": f"/api/jarvis/patch/reviews/{review_id}/apply"},
        )
        if not security_result["decision"]["allowed"]:
            return _build_security_block_response(security_result)

        latest_apply_run = jarvis_operator.get_latest_patch_apply_run(review_id)
        if (
            latest_apply_run
            and str(latest_apply_run.get("status") or "").strip().lower()
            in {"completed", "awaiting_verification", "rejected_no_admission"}
            and not force_rerun
        ):
            return jsonify(
                {
                    "error": "This review already has a governed apply run. Inspect the latest run before forcing a rerun.",
                    "review": review,
                    "run": latest_apply_run,
                }
            ), 409

        session_id = (
            str(data.get("session_id") or "").strip()
            or str(review.get("session_id") or "").strip()
            or "workbench"
        )
        result = jarvis_operator.apply_patch_review(
            review_id,
            session_id=session_id,
            verification_evidence=data.get("verification_evidence"),
            external_suggestion_details=external_suggestion_details,
        )
        return jsonify(
            {
                "review": jarvis_operator.get_patch_review(review_id),
                "preview": result.get("preview"),
                "result": result,
                "verification": result.get("verification"),
                "run": result.get("run"),
                "law_enforcement": result.get("law_enforcement"),
                "ul_snapshot": result.get("ul_snapshot"),
                "law_event_log": result.get("law_event_log"),
                "judgment_log": result.get("judgment_log"),
            }
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error applying patch review {review_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory-smith/review", methods=["POST"])
def review_memory_candidates():
    """Run a MemorySmith curation pass."""
    try:
        data = request.json or {}
        return jsonify(jarvis_operator.review_memory_candidates(data))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error reviewing memory candidates: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/provider-mind/choose", methods=["POST"])
def choose_provider_mind_path():
    """Choose the high-level Jarvis engine path for a request."""
    try:
        data = request.json or {}
        message = str(data.get("message") or "").strip()
        if not message:
            return jsonify({"error": "message is required"}), 400
        workspace_context = data.get("workspace_context")
        if not isinstance(workspace_context, dict) and data.get("goal"):
            workspace_context = jarvis_operator.build_workspace_context(
                str(data.get("goal") or message),
                force=True,
                reason="operator_request",
                auto_attached=False,
            )
        requested_mode = normalize_response_mode(data.get("response_mode"))
        selector = resolve_debug_selector(message)
        decision = jarvis_operator.choose_provider_path(
            message,
            response_mode=requested_mode,
            mode_scope="debugging" if requested_mode == "debug" else selector.get("scope"),
            workspace_context=workspace_context,
            preferred_provider=data.get("preferred_provider"),
        )
        return jsonify({"decision": decision})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error choosing provider mind path: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/security", methods=["GET"])
def get_security_protocol_snapshot():
    """Expose the unified security protocol posture and recent decisions."""
    try:
        return jsonify({"security_protocol": security_protocol_core.snapshot(limit_events=12)})
    except Exception as e:
        logger.error(f"Error reading security protocol snapshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/security/events", methods=["GET"])
def list_security_protocol_events():
    """Expose recent unified security events for the operator console."""
    try:
        limit = max(1, min(int(request.args.get("limit", 25)), 100))
        decision = request.args.get("decision")
        return jsonify({"events": security_protocol_core.list_events(limit=limit, decision=decision)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing security protocol events: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/immune", methods=["GET"])
def get_immune_snapshot():
    """Expose the current immune posture, incidents, and recent events."""
    try:
        return jsonify({"immune_system": immune_system.snapshot(limit_events=12, limit_incidents=6)})
    except Exception as e:
        logger.error(f"Error reading immune snapshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/immune/events", methods=["GET"])
def list_immune_events():
    """Expose recent immune reactions."""
    try:
        limit = max(1, min(int(request.args.get("limit", 25)), 100))
        return jsonify({"events": immune_system.list_events(limit=limit)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing immune events: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/immune/incidents", methods=["GET"])
def list_immune_incidents():
    """Expose open and recent immune incidents."""
    try:
        limit = max(1, min(int(request.args.get("limit", 10)), 50))
        return jsonify({"incidents": immune_system.list_incidents(limit=limit)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing immune incidents: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/immune/resilience", methods=["GET"])
def get_immune_resilience_status():
    """Expose defend-heal-harden resilience posture."""
    try:
        from src.immune_resilience_organ import build_immune_resilience_status

        return jsonify({"immune_resilience": build_immune_resilience_status()})
    except Exception as e:
        logger.error(f"Error reading immune resilience status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/immune/heal", methods=["POST"])
def trigger_immune_heal():
    """Operator-triggered immune heal (audited, bounded)."""
    try:
        data = request.json or {}
        reason = str(data.get("reason") or "operator_heal_request").strip() or "operator_heal_request"
        healed_by = str(data.get("actor_id") or "operator").strip() or "operator"
        result = immune_system.attempt_heal(reason=reason, healed_by=healed_by)
        return jsonify(
            {
                "heal_result": result,
                "immune_system": immune_system.snapshot(limit_events=6, limit_incidents=6),
            }
        )
    except Exception as e:
        logger.error(f"Error triggering immune heal: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/governance", methods=["GET"])
def get_governance_snapshot():
    """Expose governance posture, policy requests, and break-glass state."""
    try:
        truth_scope = normalize_truth_scope(request.args.get("truth_scope"), default="live")
        return jsonify(
            {
                "governance": governance_layer.snapshot_with_scope(
                    limit_events=12,
                    limit_requests=8,
                    truth_scope=truth_scope,
                ),
                "truth_scope": truth_scope,
            }
        )
    except Exception as e:
        logger.error(f"Error reading governance snapshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/governance/policy-requests", methods=["GET", "POST"])
def manage_policy_requests():
    """List or submit governance-layer policy promotion requests."""
    try:
        if request.method == "GET":
            limit = max(1, min(int(request.args.get("limit", 20)), 100))
            status = request.args.get("status")
            truth_scope = normalize_truth_scope(request.args.get("truth_scope"), default="live")
            return jsonify(
                {
                    "requests": governance_layer.list_policy_requests(
                        status=status,
                        limit=limit,
                        truth_scope=truth_scope,
                    ),
                    "truth_scope": truth_scope,
                }
            )

        data = request.json or {}
        payload = governance_layer.submit_policy_request(
            title=str(data.get("title") or "").strip() or "Untitled policy change",
            actor_id=str(data.get("actor_id") or "security_local"),
            actor_role=str(data.get("actor_role") or "security_engineer").strip().lower(),
            dsl_text=str(data.get("dsl_text") or data.get("policy_text") or ""),
            risk_score=data.get("risk_score"),
            changelog=data.get("changelog"),
            diff_summary=data.get("diff_summary"),
            shadow_divergence=data.get("shadow_divergence"),
            unit_tests_passed=data.get("unit_tests_passed"),
            state_class=data.get("state_class"),
            truth_status=data.get("truth_status"),
        )
        return jsonify({"policy_request": payload}), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        logger.error(f"Error managing governance policy requests: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/governance/policy-requests/<request_id>/promote", methods=["POST"])
def promote_policy_request(request_id):
    """Approve and promote a staged policy request."""
    try:
        data = request.json or {}
        payload = governance_layer.promote_policy_request(
            request_id,
            actor_id=str(data.get("actor_id") or "owner_local"),
            actor_role=str(data.get("actor_role") or "owner").strip().lower(),
            rollout_strategy=str(data.get("rollout_strategy") or "full"),
        )
        return jsonify({"policy_request": payload, "governance": governance_layer.snapshot(limit_events=6, limit_requests=6)})
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error promoting policy request: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/governance/policy-requests/<request_id>/reject", methods=["POST"])
def reject_policy_request(request_id):
    """Reject a policy request with an explicit governance reason."""
    try:
        data = request.json or {}
        payload = governance_layer.reject_policy_request(
            request_id,
            actor_id=str(data.get("actor_id") or "security_local"),
            actor_role=str(data.get("actor_role") or "security_engineer").strip().lower(),
            reason=str(data.get("reason") or "Policy request rejected."),
        )
        return jsonify({"policy_request": payload, "governance": governance_layer.snapshot(limit_events=6, limit_requests=6)})
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error rejecting policy request: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/governance/break-glass", methods=["POST"])
def update_break_glass():
    """Activate or clear break-glass access."""
    try:
        data = request.json or {}
        action = str(data.get("action") or "activate").strip().lower().replace("-", "_")
        if action in {"clear", "revoke", "disable"}:
            payload = governance_layer.clear_break_glass(
                actor_id=str(data.get("actor_id") or "owner_local"),
                actor_role=str(data.get("actor_role") or "owner").strip().lower(),
                reason=str(data.get("reason") or "Owner cleared break-glass."),
            )
        else:
            payload = governance_layer.activate_break_glass(
                actor_id=str(data.get("actor_id") or "owner_local"),
                actor_role=str(data.get("actor_role") or "owner").strip().lower(),
                scope=str(data.get("scope") or "high_sensitivity_access"),
                duration_minutes=int(data.get("duration_minutes") or 10),
                reason=str(data.get("reason") or "Critical operational need during crisis mode."),
            )
        return jsonify({"break_glass": payload, "governance": governance_layer.snapshot(limit_events=6, limit_requests=6)})
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        logger.error(f"Error updating break-glass state: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/module-governance", methods=["GET"])
def get_module_governance_snapshot():
    """Expose the AAIS module governance protocol snapshot."""
    try:
        limit_events = max(1, min(int(request.args.get("limit_events", 12)), 50))
        limit_modules = max(1, min(int(request.args.get("limit_modules", 12)), 50))
        return jsonify(
            {
                "module_governance": module_governance.snapshot(
                    limit_events=limit_events,
                    limit_modules=limit_modules,
                )
            }
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error reading module governance snapshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/module-governance/modules", methods=["GET"])
def list_governed_modules():
    """List admitted, rejected, quarantined, or blacklisted modules."""
    try:
        limit = max(1, min(int(request.args.get("limit", 25)), 100))
        status = request.args.get("status")
        return jsonify({"modules": module_governance.list_modules(status=status, limit=limit)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing governed modules: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/module-governance/modules/admit", methods=["POST"])
def admit_governed_module():
    """Run the non-negotiable admission gate for a candidate AAIS module."""
    try:
        data = request.json or {}
        payload = module_governance.admit_module(
            data,
            actor_id=str(data.get("actor_id") or "security_local"),
            actor_role=str(data.get("actor_role") or "security_engineer").strip().lower(),
        )
        status_code = 201 if payload.get("installable") else 400
        return jsonify(
            {
                "module": payload["module"],
                "evaluation": payload["evaluation"],
                "event": payload["event"],
                "module_governance": module_governance.snapshot(limit_events=6, limit_modules=6),
            }
        ), status_code
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        logger.error(f"Error admitting governed module: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/module-governance/modules/<module_id>/signals", methods=["POST"])
def report_governed_module_signal(module_id):
    """Report a runtime module signal so the immune system can react."""
    try:
        data = request.json or {}
        payload = module_governance.report_runtime_signal(
            module_id,
            signal_type=str(data.get("signal_type") or data.get("signal") or "boundary_violation"),
            reason=str(data.get("reason") or "Module governance violation detected."),
            details=dict(data.get("details") or {}),
            actor_id=str(data.get("actor_id") or "immune_system"),
            actor_role=str(data.get("actor_role") or "system").strip().lower(),
        )
        return jsonify(
            {
                "module": payload["module"],
                "event": payload["event"],
                "immune_update": payload["immune_update"],
                "severity": payload["severity"],
                "resolution": payload["resolution"],
                "immune_system": immune_system.snapshot(limit_events=6, limit_incidents=6),
                "module_governance": module_governance.snapshot(limit_events=6, limit_modules=6),
            }
        )
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error reporting governed module signal: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/module-governance/modules/<module_id>/resolve", methods=["POST"])
def resolve_governed_module(module_id):
    """Resolve a module incident by correction, quarantine, or blacklist action."""
    try:
        data = request.json or {}
        payload = module_governance.resolve_module(
            module_id,
            action=str(data.get("action") or "correct"),
            reason=str(data.get("reason") or "Module incident resolved."),
            actor_id=str(data.get("actor_id") or "security_local"),
            actor_role=str(data.get("actor_role") or "security_engineer").strip().lower(),
        )
        return jsonify(
            {
                "module": payload["module"],
                "event": payload["event"],
                "immune_update": payload["immune_update"],
                "immune_system": immune_system.snapshot(limit_events=6, limit_incidents=6),
                "module_governance": module_governance.snapshot(limit_events=6, limit_modules=6),
            }
        )
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error resolving governed module: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/reasoning/evaluate", methods=["POST"])
def evaluate_reasoning_exchange_packet():
    """Admit or reject one neutral reasoning packet under local AAIS law."""
    protocol = ReasoningExchangeProtocol()
    runtime_context = request.args.get("runtime_context") or "live_runtime"
    try:
        raw_packet = request.get_json(silent=True)
        bridge_result = _route_reasoning_ingress_to_bridge(raw_packet, runtime_context=runtime_context)
        if bridge_result.get("decision") == "BLOCK":
            return jsonify(
                {
                    "status": "REJECT",
                    "reason": _cognitive_bridge_reject_reason(bridge_result),
                    "cognitive_bridge": bridge_result,
                    "immune_system": protocol.immune_controller.snapshot(limit_events=6, limit_incidents=3),
                }
            ), 403
        normalized_packet = normalize_reasoning_exchange_packet(raw_packet)
        if normalized_packet["version"] != REASONING_EXCHANGE_PROTOCOL_VERSION:
            payload = build_reasoning_exchange_reject_response(
                normalized_packet,
                reason="unsupported_version",
                notes=["Supported version is 1.0."],
            )
            payload["cognitive_bridge"] = bridge_result
            payload["immune_update"] = protocol.observe_boundary_signal(
                signal_type="unsupported_version",
                severity="medium",
                reason="Reasoning packet used an unsupported protocol version.",
                runtime_context=runtime_context,
                packet=normalized_packet,
                decision="REJECT",
            )
            payload["immune_system"] = protocol.immune_controller.snapshot(limit_events=6, limit_incidents=3)
            return jsonify(payload)
        if normalized_packet["type"] != REASONING_EXCHANGE_PACKET_TYPE:
            payload = build_reasoning_exchange_reject_response(
                normalized_packet,
                reason="unsupported_packet_type",
                notes=["Only reasoning_packet is supported."],
            )
            payload["cognitive_bridge"] = bridge_result
            payload["immune_update"] = protocol.observe_boundary_signal(
                signal_type="unsupported_packet_type",
                severity="medium",
                reason="Reasoning packet used an unsupported packet type.",
                runtime_context=runtime_context,
                packet=normalized_packet,
                decision="REJECT",
            )
            payload["immune_system"] = protocol.immune_controller.snapshot(limit_events=6, limit_incidents=3)
            return jsonify(payload)

        from src.mesh.evaluate_hooks import (
            apply_mesh_trust_penalty,
            check_mesh_peer_allowed,
            get_mesh_peer_id,
            record_mesh_evaluate_outcome,
        )

        mesh_peer_id = get_mesh_peer_id(request)
        mesh_allowed, mesh_deny_reason = check_mesh_peer_allowed(mesh_peer_id)
        if not mesh_allowed:
            return jsonify(
                {
                    "status": "REJECT",
                    "reason": mesh_deny_reason,
                    "source": "mesh",
                    "cognitive_bridge": bridge_result,
                }
            ), 403

        normalized_packet = apply_mesh_trust_penalty(normalized_packet, mesh_peer_id)

        payload = protocol.evaluate_normalized_packet(
            normalized_packet,
            runtime_context=runtime_context,
        )
        record_mesh_evaluate_outcome(mesh_peer_id, payload, normalized_packet)
        payload["cognitive_bridge"] = bridge_result
        status_code = 200
        if payload.get("phase_gate", {}).get("decision") == "BLOCK":
            status_code = 403
        elif payload.get("module_governance", {}).get("decision") == "BLOCK":
            status_code = 403
        elif payload.get("status") == "REJECT" and payload.get("reason") == "rls_rejected":
            status_code = 403
        elif "rls_epistemic_reject" in list(bridge_result.get("reason_codes") or []):
            status_code = 403
        return jsonify(payload), status_code
    except ReasoningExchangeValidationError as e:
        payload = {
            "status": "INVALID",
            "reason": str(e),
            "cognitive_bridge": _route_reasoning_ingress_to_bridge(
                request.get_json(silent=True),
                runtime_context=runtime_context,
            ),
            "immune_update": protocol.observe_boundary_signal(
                signal_type="invalid_packet_structure",
                severity="medium",
                reason=str(e),
                runtime_context=runtime_context,
                raw_packet=request.get_json(silent=True),
                decision="INVALID",
            ),
            "immune_system": protocol.immune_controller.snapshot(limit_events=6, limit_incidents=3),
        }
        return jsonify(payload), 400
    except Exception as e:
        logger.error(f"Error evaluating reasoning exchange packet: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/continuity/profile", methods=["GET", "PATCH"])
def manage_continuity_profile():
    """Expose and update Jarvis continuity profile state."""
    try:
        user_id = str(request.args.get("user_id") or "operator").strip().lower().replace(" ", "_") or "operator"
        if request.method == "GET":
            profile = continuity_profile_store.get_profile(tenant_id="local", user_id=user_id)
            return jsonify({"continuity_profile": profile.to_dict()})

        data = request.json or {}
        profile = continuity_profile_store.update_profile(
            tenant_id="local",
            user_id=user_id,
            tone=data.get("tone"),
            formatting_preferences=data.get("formatting_preferences"),
            refusal_style=data.get("refusal_style"),
            explanation_style=data.get("explanation_style"),
            known_projects=data.get("known_projects"),
            preferred_tools=data.get("preferred_tools"),
            self_description=data.get("self_description"),
            continuity_rules=data.get("continuity_rules"),
        )
        return jsonify({"continuity_profile": profile})
    except Exception as e:
        logger.error(f"Error managing continuity profile: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/otem/run", methods=["POST"])
def run_otem_reasoning():
    """Build a deterministic OTEM plan through the normal Jarvis turn-contract path."""
    try:
        data = request.json or {}
        raw_task = " ".join(str(data.get("task") or data.get("message") or "").split()).strip()
        if not raw_task:
            return jsonify({"error": "task is required"}), 400
        if not detect_otem(raw_task):
            return jsonify({"error": "task must explicitly trigger OTEM"}), 400

        session_id = str(data.get("session_id") or "").strip()
        if not session_id:
            otem_result = _build_otem_result(raw_task)
            transient_contract = {
                "requested_mode": "operator",
                "resolved_mode": "operator",
                "resolved_scope": "operator_task",
                "resolved_voice": "jarvis",
                "contract_label": "otem",
                "provider_fallback": False,
                "otem_enabled": True,
                "otem_task": otem_result.get("restated_task"),
                "otem_scope": otem_result.get("scope"),
                "otem_plan": [dict(step or {}) for step in list(otem_result.get("plan") or [])],
                "otem_status": otem_result.get("status"),
                "otem_rejection_reason": otem_result.get("rejection_reason"),
                "otem_allowed_alternative": otem_result.get("allowed_alternative"),
                "otem": dict(otem_result),
            }
            completion_text, completion_report = guard_output_completion(
                otem_result["answer"],
                stop_reason="direct_tool",
                finish_reason="direct_tool",
            )
            response_trace = _build_tool_response_trace(
                "operator",
                tool_result={"type": "otem", "otem": otem_result},
                turn_contract=transient_contract,
                session=None,
            )
            _record_output_completion_trace(response_trace, completion_report.to_dict())
            response_trace["otem_boundary"] = _build_otem_boundary_snapshot(
                user_message=raw_task,
                otem_payload=otem_result,
                raw_response_text=otem_result["answer"],
                final_response_text=completion_text,
                completion_trace=completion_report.to_dict(),
            )
            _sync_otem_visible_answer(
                completion_text,
                otem_payload=otem_result,
                turn_contract=transient_contract,
            )
            return jsonify(
                {
                    "response": completion_text,
                    "otem": otem_result,
                    "turn_contract": transient_contract,
                    "response_trace": response_trace,
                }
            )

        session = conversation_memory.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found or expired"}), 404
        prior_otem_state = dict(session.metadata.get("otem_state") or {})
        otem_result = _build_otem_result(
            raw_task,
            session_id=session_id,
            prior_state=prior_otem_state,
        )

        _set_session_response_mode(session, "operator")
        _attach_session_mission_context(session)
        _clear_turn_context(session)
        requested_mode, response_mode, mode_guidance = _resolve_turn_mode_guidance(
            session,
            user_message=raw_task,
            requested_mode="operator",
            use_research=False,
        )
        _resolve_provider_mind(session, raw_task, response_mode)
        _set_turn_contract(
            session,
            requested_mode=requested_mode,
            resolved_mode=response_mode,
            resolved_scope="operator_task",
            resolved_voice="jarvis",
            otem=otem_result,
            provider_fallback=False,
            contract_label="otem",
        )
        session.metadata["otem_state"] = dict(otem_result)
        session.metadata["response_trace"] = _build_tool_response_trace(
            response_mode,
            tool_result={"type": "otem", "otem": otem_result},
            provider_mind=session.metadata.get("provider_mind"),
            turn_contract=session.metadata.get("turn_contract"),
            session=session,
        )
        response_text = _finalize_visible_response(
            session,
            raw_task,
            otem_result["answer"],
            response_trace=session.metadata.get("response_trace"),
            generation_metadata={
                "stop_reason": "direct_tool",
                "finish_reason": "direct_tool",
            },
        )
        _sync_otem_visible_answer(
            response_text,
            otem_payload=otem_result,
            turn_contract=session.metadata.get("turn_contract"),
            session=session,
        )
        _record_otem_boundary_trace(
            session,
            session.metadata.get("response_trace"),
            user_message=raw_task,
            otem_payload=otem_result,
            raw_response_text=otem_result["answer"],
            final_response_text=response_text,
            completion_trace=session.metadata.get("output_completion_trace"),
        )

        return jsonify(
            {
                "response": response_text,
                "otem": otem_result,
                "turn_contract": session.metadata.get("turn_contract"),
                "mode_guidance": mode_guidance,
                **_build_chat_runtime_payload(session, session.session_id),
            }
        )
    except Exception as e:
        logger.error(f"Error running OTEM plan: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/research", methods=["POST"])
def run_live_research():
    """Search the live web and return source cards for the UI."""
    try:
        data = request.json or {}
        query = data.get("query")
        result = web_researcher.research(query)
        if result is None:
            return jsonify({"query": query, "sources": [], "summary": "No live sources found."})
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in live research: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/actions", methods=["GET"])
def list_safe_local_actions():
    """List safe local actions available to the Jarvis console."""
    try:
        return jsonify({"actions": jarvis_operator.list_actions()})
    except Exception as e:
        logger.error(f"Error listing safe local actions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/spatial-reason", methods=["POST"])
def run_spatial_reason():
    """Run one structured spatial reasoning tool call."""
    try:
        data = request.json or {}
        if not isinstance(data, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        tool_name = str(data.get("tool") or "spatial_reason").strip().lower()
        args = data.get("args") if "args" in data else {
            key: value for key, value in data.items() if key != "tool"
        }

        if tool_name != "spatial_reason":
            return jsonify({"error": "tool must be 'spatial_reason'"}), 400
        if not isinstance(args, dict):
            return jsonify({"error": "args must be a JSON object"}), 400

        result = jarvis_operator.handle_tool_request(
            tool_name,
            args,
            runtime_context="operator_runtime",
        )
        if not result:
            return jsonify({"error": "Unsupported tool request"}), 400

        return jsonify(attach_ul_substrate(result)), _phase_gate_http_status(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error running spatial reasoning tool: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/mystic-read", methods=["POST"])
def run_mystic_read():
    """Run one structured Mystic reading tool call."""
    try:
        data = request.json or {}
        if not isinstance(data, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        tool_name = str(data.get("tool") or "mystic_reading").strip().lower()
        args = data.get("args") if "args" in data else {
            key: value for key, value in data.items() if key != "tool"
        }

        if tool_name not in {"mystic_reading", "mythic_reading", "mystic", "mythic"}:
            return jsonify(
                {
                    "error": (
                        "tool must be one of 'mystic_reading', 'mythic_reading', "
                        "'mystic', or 'mythic'"
                    )
                }
            ), 400
        if not isinstance(args, dict):
            return jsonify({"error": "args must be a JSON object"}), 400

        result = jarvis_operator.handle_tool_request(
            tool_name,
            args,
            runtime_context="operator_runtime",
        )
        if not result:
            return jsonify({"error": "Unsupported tool request"}), 400

        return jsonify(attach_ul_substrate(result)), _phase_gate_http_status(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error running Mystic reading tool: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v9-core", methods=["POST"])
def run_v9_core():
    """Run one structured V9 Core tool call."""
    try:
        data = request.json or {}
        if not isinstance(data, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        tool_name = str(data.get("tool") or "v9_core").strip().lower()
        args = data.get("args") if "args" in data else {
            key: value for key, value in data.items() if key != "tool"
        }

        if tool_name not in {"v9_core", "v9", "divine_core", "god_engine"}:
            return jsonify(
                {
                    "error": (
                        "tool must be one of 'v9_core', 'v9', 'divine_core', or 'god_engine'"
                    )
                }
            ), 400
        if not isinstance(args, dict):
            return jsonify({"error": "args must be a JSON object"}), 400

        result = jarvis_operator.handle_tool_request(
            tool_name,
            args,
            runtime_context="operator_runtime",
        )
        if not result:
            return jsonify({"error": "Unsupported tool request"}), 400

        return jsonify(attach_ul_substrate(result)), _phase_gate_http_status(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error running V9 Core tool: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v10-core", methods=["POST"])
def run_v10_core():
    """Run one structured V10 Core tool call."""
    try:
        data = request.json or {}
        if not isinstance(data, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        tool_name = str(data.get("tool") or "v10_core").strip().lower()
        args = data.get("args") if "args" in data else {
            key: value for key, value in data.items() if key != "tool"
        }

        if tool_name not in {"v10_core", "v10", "core_v10"}:
            return jsonify(
                {
                    "error": (
                        "tool must be one of 'v10_core', 'v10', or 'core_v10'"
                    )
                }
            ), 400
        if not isinstance(args, dict):
            return jsonify({"error": "args must be a JSON object"}), 400

        result = jarvis_operator.handle_tool_request(
            tool_name,
            args,
            runtime_context="operator_runtime",
        )
        if not result:
            return jsonify({"error": "Unsupported tool request"}), 400

        return jsonify(attach_ul_substrate(result)), _phase_gate_http_status(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error running V10 Core tool: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v9-runtime", methods=["GET"])
def get_v9_runtime():
    """Return the inspectable V9 runtime state."""
    try:
        return jsonify(v9_runtime.snapshot(limit=12))
    except Exception as e:
        logger.error(f"Error loading V9 runtime: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v9-runtime/events", methods=["GET"])
def get_v9_runtime_events():
    """Return the recent V9 runtime events."""
    try:
        limit = request.args.get("limit", type=int) or 20
        return jsonify({"events": v9_runtime.list_events(limit=limit)})
    except Exception as e:
        logger.error(f"Error loading V9 runtime events: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v10-runtime", methods=["GET"])
def get_v10_runtime():
    """Return the inspectable V10 runtime state."""
    try:
        return jsonify(v10_runtime.snapshot(limit=12))
    except Exception as e:
        logger.error(f"Error loading V10 runtime: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v10-runtime/events", methods=["GET"])
def get_v10_runtime_events():
    """Return the recent V10 runtime events."""
    try:
        limit = request.args.get("limit", type=int) or 20
        return jsonify({"events": v10_runtime.list_events(limit=limit)})
    except Exception as e:
        logger.error(f"Error loading V10 runtime events: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workbench", methods=["GET"])
def get_jarvis_workbench():
    """Return one aggregate operator snapshot for the Jarvis Workbench."""
    try:
        session_id = str(request.args.get("session_id") or "").strip() or None
        truth_scope = normalize_truth_scope(request.args.get("truth_scope"), default="live")
        memory_limit = max(4, min(int(request.args.get("memory_limit", 18)), 40))
        review_limit = max(4, min(int(request.args.get("review_limit", 12)), 30))
        run_limit = max(4, min(int(request.args.get("run_limit", 12)), 30))
        path_prefix = request.args.get("path_prefix")

        memories = jarvis_operator.memory_enforcer.list_memories(
            limit=memory_limit,
            sort="updated",
            truth_scope=truth_scope,
            runtime_context="operator_runtime",
        )
        reviews = jarvis_operator.list_patch_reviews(
            session_id=session_id,
            limit=review_limit,
            truth_scope=truth_scope,
        )
        runs = jarvis_operator.list_runs(session_id=session_id, limit=run_limit, truth_scope=truth_scope)
        recent_apply_runs = jarvis_operator.list_patch_apply_runs(limit=6, truth_scope=truth_scope)
        workspace_profile = jarvis_operator.detect_workspace_profile(path_prefix=path_prefix)
        projects = jarvis_operator.workspace_tools.list_projects(limit=8)
        otem_catalog = jarvis_operator.build_otem_catalog()
        mission_snapshot = mission_board.snapshot(session_id=session_id)
        knowledge_snapshot = _build_knowledge_snapshot(
            session_id=session_id,
            query=request.args.get("query"),
            limit=6,
            path_prefix=path_prefix,
        )
        governance_snapshot = governance_layer.snapshot_with_scope(
            limit_events=8,
            limit_requests=8,
            truth_scope=truth_scope,
        )
        forge_snapshot = _build_forge_operator_snapshot(session_id=session_id)
        evolve_snapshot = _build_evolve_operator_snapshot(session_id=session_id)

        execution_cockpit = {
            "ready_review_count": sum(
                1 for review in reviews if (review.get("apply_gate") or {}).get("ready")
            ),
            "open_run_count": sum(1 for run in runs if run.get("status") == "open"),
            "latest_review_id": reviews[0]["id"] if reviews else None,
            "latest_run_id": runs[0]["id"] if runs else None,
            "latest_focus_mission": mission_snapshot.get("focus_mission"),
            "truth_scope": truth_scope,
            "recent_apply_runs": [
                {
                    "id": run.get("id"),
                    "title": run.get("title"),
                    "status": run.get("status"),
                    "updated_at": run.get("updated_at"),
                    "summary": run.get("summary"),
                    "review_id": (run.get("meta") or {}).get("review_id"),
                }
                for run in recent_apply_runs
            ],
        }

        payload = {
            "health": {
                "requested_model_mode": _get_model_mode(),
                "active_model_mode": ai_mode,
                "ai_status": "initialized" if ai_model is not None else "not_initialized",
            },
            "truth_scope": truth_scope,
            "mission_board": mission_snapshot,
            "memory_bank": {
                "summary": jarvis_operator.memory_enforcer.build_summary(
                    truth_scope=truth_scope,
                    runtime_context="operator_runtime",
                ),
                "memories": memories,
                "governance": jarvis_operator.memory_enforcer.build_governance_snapshot(
                    limit=6,
                    runtime_context="operator_runtime",
                ),
            },
            "patch_reviews": reviews,
            "runs": runs,
            "execution_cockpit": execution_cockpit,
            "governance": governance_snapshot,
            "workspace_lane": {
                "profile": workspace_profile,
                "projects": projects,
            },
            "otem": otem_catalog,
            "forge": forge_snapshot,
            "evolve": evolve_snapshot,
            "knowledge_authority": knowledge_snapshot,
            "state_hygiene": {
                "truth_scope": truth_scope,
                "memory": jarvis_operator.memory_enforcer.build_summary(
                    truth_scope="all",
                    runtime_context="operator_runtime",
                ).get("state_hygiene"),
                "reviews": {
                    "visible": len(reviews),
                },
                "runs": {
                    "visible": len(runs),
                    "open": sum(1 for run in runs if run.get("status") == "open"),
                },
                "governance": governance_snapshot.get("state_hygiene"),
            },
            "v9_runtime": v9_runtime.snapshot(limit=4),
            "v10_runtime": v10_runtime.snapshot(limit=4),
            "operator_console": build_operator_console_snapshot(runtime=ugr_runtime),
        }
        return jsonify(payload)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Jarvis Workbench blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error building Jarvis Workbench snapshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/state-hygiene", methods=["GET"])
def get_state_hygiene_snapshot():
    """Return the shared state hygiene posture across operator stores."""
    try:
        truth_scope = normalize_truth_scope(request.args.get("truth_scope"), default="live")
        review_limit = max(4, min(int(request.args.get("review_limit", 40)), 80))
        run_limit = max(4, min(int(request.args.get("run_limit", 40)), 80))
        snapshot = {
            "truth_scope": truth_scope,
            "memory": jarvis_operator.memory_enforcer.build_summary(
                truth_scope="all",
                runtime_context="operator_runtime",
            ),
            "reviews": {
                "total": len(jarvis_operator.list_patch_reviews(limit=review_limit, truth_scope="all")),
                "visible": len(jarvis_operator.list_patch_reviews(limit=review_limit, truth_scope=truth_scope)),
            },
            "runs": {
                "total": len(jarvis_operator.list_runs(limit=run_limit, truth_scope="all")),
                "visible": len(jarvis_operator.list_runs(limit=run_limit, truth_scope=truth_scope)),
            },
            "governance": governance_layer.snapshot_with_scope(
                limit_events=12,
                limit_requests=12,
                truth_scope=truth_scope,
            ).get("state_hygiene"),
        }
        return jsonify({"state_hygiene": snapshot})
    except MemoryBoardEnforcerError as e:
        logger.warning(f"State hygiene snapshot blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error reading state hygiene snapshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/state-hygiene/compact", methods=["POST"])
def compact_state_hygiene():
    """Archive or expire non-live records so operator surfaces stay clean."""
    try:
        memory_result = jarvis_operator.memory_enforcer.compact_state(runtime_context="operator_runtime")
        run_result = jarvis_operator.run_ledger.compact_runs()
        review_result = jarvis_operator.patch_reviews.compact_reviews()
        governance_result = governance_layer.compact_history()
        return jsonify(
            {
                "state_hygiene": {
                    "memory": memory_result,
                    "runs": run_result,
                    "reviews": review_result,
                    "governance": governance_result,
                }
            }
        )
    except MemoryBoardEnforcerError as e:
        logger.warning(f"State hygiene compaction blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error compacting state hygiene: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/knowledge", methods=["GET"])
def get_knowledge_authority_snapshot():
    """Return the canonical AAIS knowledge authority snapshot."""
    try:
        session_id = str(request.args.get("session_id") or "").strip() or None
        query = str(request.args.get("query") or "").strip() or None
        limit = max(2, min(int(request.args.get("limit", 6)), 20))
        path_prefix = request.args.get("path_prefix")
        return jsonify(
            attach_ul_substrate(
                {
                    "knowledge_authority": _build_knowledge_snapshot(
                        session_id=session_id,
                        query=query,
                        limit=limit,
                        path_prefix=path_prefix,
                    )
                }
            )
        )
    except MemoryBoardEnforcerError as e:
        logger.warning(f"Knowledge authority snapshot blocked by governance gateway: {e}")
        return _build_memory_enforcer_block_response(e)
    except Exception as e:
        logger.error(f"Error building knowledge authority snapshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/operator/knowledge/promote-from-urg", methods=["POST"])
def promote_operator_knowledge_from_urg():
    """Promote a proven URG discovery receipt into governed operator knowledge."""
    try:
        data = request.get_json(silent=True) or {}
        contribution_id = str(data.get("contribution_id") or "").strip()
        operator_id = str(data.get("operator_id") or "").strip()
        tenant_id = str(data.get("tenant_id") or "global").strip() or "global"
        if not contribution_id:
            return jsonify({"error": "contribution_id is required"}), 400
        if not operator_id:
            return jsonify({"error": "operator_id is required"}), 400

        from src.ugr.discovery.contribution_store import ContributionDiscoveryStore

        store = ContributionDiscoveryStore(tenant_id=tenant_id)
        receipt = store.get_by_contribution_id(contribution_id)
        if not receipt:
            return jsonify(
                {
                    "error": "contribution not found",
                    "contribution_id": contribution_id,
                    "tenant_id": tenant_id,
                }
            ), 404

        result = promote_from_receipt(
            receipt,
            operator_id=operator_id,
            tenant_id=tenant_id,
        )
        return jsonify({"promotion": result})
    except Exception as e:
        logger.error(f"Error promoting URG knowledge: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/specialists", methods=["GET"])
def list_specialists():
    """List logical Jarvis specialists grouped by domain for manual selection in the UI."""
    try:
        return jsonify(
            attach_ul_substrate(
                {"domains": list_specialist_catalog(), "presets": list_specialist_presets()}
            )
        )
    except Exception as e:
        logger.error(f"Error listing specialists: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/providers", methods=["GET"])
def list_providers():
    """List available local and optional remote providers for Jarvis routing."""
    try:
        provider_registry.refresh()
        return jsonify({"providers": provider_registry.list_status()})
    except Exception as e:
        logger.error(f"Error listing providers: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/protocol", methods=["GET"])
def get_jarvis_protocol():
    """Expose the canonical Jarvis protocol contract and optional session preview."""
    try:
        payload = {"protocol": protocol_spec()}
        session_id = request.args.get("session_id")
        if session_id:
            session = conversation_memory.get_session(session_id)
            if not session:
                return jsonify({"error": "Session not found or expired"}), 404

            response_mode = normalize_response_mode(session.metadata.get("response_mode"))
            provider_defaults = RESPONSE_MODE_DEFAULTS[response_mode]
            envelope = session.build_protocol_envelope()
            modular_preview = build_modular_provider_preview(
                model=(
                    (session.metadata.get("model_route") or {}).get("provider_model")
                    or (session.metadata.get("model_route") or {}).get("id")
                    or "local-model"
                ),
                messages=envelope.get("messages"),
                stream=True,
                temperature=provider_defaults["temperature"],
                max_tokens=provider_defaults["max_tokens"],
                mode=response_mode,
                metadata={
                    "session_id": session_id,
                    "provider": (session.metadata.get("model_route") or {}).get("provider") or "local",
                    "current_goal": session.spiral_state.current_goal,
                    "model_route": session.metadata.get("model_route"),
                    "workspace_context": session.metadata.get("workspace_context"),
                    "action_lifecycle": session.metadata.get("action_lifecycle"),
                    "specialist_profile": session.metadata.get("specialist_profile"),
                },
            )
            payload["session"] = {
                "session_id": session_id,
                "summary": session.protocol_summary(),
                "envelope": envelope,
                "modules": modular_preview["modules"],
                "context_modules": modular_preview["context_modules"],
                "pipeline_mode": modular_preview["pipeline_mode"],
                "guardrail_state": modular_preview["guardrail_state"],
                "ul_trace": modular_preview["ul_trace"],
                "ul_substrate": modular_preview.get("ul_substrate"),
                "doctrine": modular_preview["doctrine"],
                "guardrail_evaluation": modular_preview["guardrail_evaluation"],
                "canonical_guardrail_evaluation": modular_preview["canonical_guardrail_evaluation"],
                "execution_outcome": modular_preview["execution_outcome"],
                "final_judgment": modular_preview["final_judgment"],
                "doctrine_posture": modular_preview["doctrine_posture"],
                "doctrine_summary": modular_preview["doctrine_summary"],
                "active_doctrine_tags": modular_preview["active_doctrine_tags"],
                "override_result": modular_preview["override_result"],
                "escalation_result": modular_preview["escalation_result"],
                "reasoning_protocol": modular_preview["reasoning_protocol"],
                "reasoning_packet": modular_preview["reasoning_packet"],
                "reasoning_summary": modular_preview["reasoning_summary"],
                "provider_messages": modular_preview["provider_messages"],
                "provider_preview": modular_preview["provider_payload"],
                "v9_runtime": v9_runtime.snapshot(limit=6),
                "v10_runtime": v10_runtime.snapshot(limit=6),
                "continuity_profile": session.metadata.get("continuity_profile"),
                "security_protocol": security_protocol_core.snapshot(limit_events=6),
                "immune_system": immune_system.snapshot(limit_events=6, limit_incidents=3),
                "governance": governance_layer.snapshot(limit_events=6, limit_requests=4),
                "module_governance": module_governance.snapshot(limit_events=6, limit_modules=6),
            }
        return jsonify(payload)
    except Exception as e:
        logger.error(f"Error building Jarvis protocol payload: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/ul-substrate/status", methods=["GET"])
def get_ul_substrate_status():
    """Expose the AAIS UL runtime substrate inventory for operator review."""
    try:
        return jsonify({"ul_substrate": substrate_status()})
    except Exception as e:
        logger.error(f"Error reading UL substrate status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/cognitive-bridge/detachment-guard", methods=["GET"])
def get_detachment_guard_status():
    """Expose the current Jarvis detachment-guard snapshot for operator review."""
    try:
        return jsonify(
            attach_ul_substrate(
                {"detachment_guard": cognitive_bridge_service.detachment_guard.snapshot()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading Jarvis detachment guard: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/cognitive-bridge/detachment-guard/review-holds/<source_id>/clear", methods=["POST"])
def clear_detachment_guard_review_hold(source_id):
    """Clear one detachment review hold through an explicit, governed operator action."""
    try:
        data = request.get_json(silent=True) or {}
        actor_id = str(data.get("actor_id") or "").strip()
        actor_role = str(data.get("actor_role") or "").strip()
        reason = str(data.get("reason") or "").strip()
        refreshed_attestation_required = bool(data.get("refreshed_attestation_required", True))

        if not actor_id:
            return jsonify({"error": "actor_id is required"}), 400
        if not actor_role:
            return jsonify({"error": "actor_role is required"}), 400
        if not reason:
            return jsonify({"error": "reason is required"}), 400

        result = cognitive_bridge_service.detachment_guard.clear_temporary_hold(
            source_id,
            actor_id=actor_id,
            actor_role=actor_role,
            reason=reason,
            refreshed_attestation_required=refreshed_attestation_required,
        )
        status_code = 200
        if not result.get("cleared"):
            status_code = 403 if result.get("review_required") else 404
        return jsonify(
            {
                "result": result,
                "detachment_guard": cognitive_bridge_service.detachment_guard.snapshot(),
            }
        ), status_code
    except Exception as e:
        logger.error(f"Error clearing Jarvis detachment review hold: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/federation/issue", methods=["POST"])
def ugr_federation_issue():
    """Issue a bilateral federation grant (pending until grantee accepts)."""
    try:
        from src.ugr.mission.federation_grants import FederationGrantStore

        data = request.get_json(silent=True) or {}
        issuer = str(data.get("issuer_tenant") or data.get("tenant_id") or "").strip()
        grantee = str(data.get("grantee_tenant") or data.get("target_tenant") or "").strip()
        operator_id = str(data.get("operator_id") or "").strip()
        if not issuer or not grantee or not operator_id:
            return jsonify({"error": "issuer_tenant, grantee_tenant, operator_id required"}), 400
        caps = list(data.get("capabilities") or ["route_step"])
        store = FederationGrantStore()
        grant = store.issue(
            issuer_tenant=issuer,
            grantee_tenant=grantee,
            capabilities=caps,
            operator_id=operator_id,
            expires_at=data.get("expires_at"),
        )
        return jsonify({"status": "ok", "grant": grant.to_dict()}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as e:
        logger.error(f"Error issuing URG federation grant: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/federation/accept", methods=["POST"])
def ugr_federation_accept():
    """Accept a pending federation grant (grantee only)."""
    try:
        from src.ugr.mission.federation_grants import FederationGrantStore

        data = request.get_json(silent=True) or {}
        grant_id = str(data.get("grant_id") or "").strip()
        accepting_tenant = str(data.get("accepting_tenant") or data.get("tenant_id") or "").strip()
        operator_id = str(data.get("operator_id") or "").strip()
        if not grant_id or not accepting_tenant or not operator_id:
            return jsonify({"error": "grant_id, accepting_tenant, operator_id required"}), 400
        store = FederationGrantStore()
        grant = store.accept(grant_id, accepting_tenant=accepting_tenant, operator_id=operator_id)
        return jsonify({"status": "ok", "grant": grant.to_dict()}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as e:
        logger.error(f"Error accepting URG federation grant: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/federation/grants", methods=["GET"])
def ugr_federation_grants_list():
    """List federation grants visible to a tenant."""
    try:
        from src.ugr.mission.federation_grants import FederationGrantStore

        tenant_id = request.args.get("tenant_id") or "global"
        store = FederationGrantStore()
        grants = [g.to_dict() for g in store.list_for_tenant(tenant_id)]
        return jsonify({"tenant_id": tenant_id, "grants": grants}), 200
    except Exception as e:
        logger.error(f"Error listing URG federation grants: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/mission/receipt/<mission_id>", methods=["GET"])
def ugr_mission_receipt_get(mission_id: str):
    """Retrieve persisted MissionReceipt by mission_id (tenant-scoped)."""
    try:
        from src.ugr.mission.mission_receipt_store import MissionReceiptStore, receipt_admin_enabled
        from src.ugr.platform.tenant_registry import normalize_tenant_id

        tenant_raw = request.args.get("tenant_id") or request.headers.get("X-URG-Tenant-Id")
        if not tenant_raw and not receipt_admin_enabled():
            return jsonify({"error": "tenant_id query parameter required"}), 400
        tenant_norm = normalize_tenant_id(tenant_raw or "global")
        record = MissionReceiptStore(tenant_id=tenant_norm).get_receipt(mission_id, tenant_id=tenant_norm)
        if not record:
            return jsonify({"error": "receipt_not_found", "mission_id": mission_id}), 404
        stored_tenant = normalize_tenant_id(record.get("tenant_id") or tenant_norm)
        if stored_tenant != tenant_norm and not receipt_admin_enabled():
            return jsonify({"error": "tenant_mismatch", "mission_id": mission_id}), 403
        return jsonify(record), 200
    except Exception as e:
        logger.error(f"Error fetching URG mission receipt: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/state/<mission_id>", methods=["GET"])
def ugr_constitutional_state_get(mission_id: str):
    """Current constitutional StateObject for a URG mission."""
    try:
        from src.ugr.state_runtime import CSR

        state = CSR.get_state(mission_id)
        return jsonify(json.loads(state.model_dump_json())), 200
    except KeyError:
        return jsonify({"error": "state_not_found", "mission_id": mission_id}), 404
    except Exception as e:
        logger.error(f"Error fetching URG constitutional state: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/state/<mission_id>/replay", methods=["GET"])
def ugr_constitutional_state_replay(mission_id: str):
    """CSR replay result for a URG mission."""
    try:
        from src.ugr.state_runtime import CSR

        CSR.get_state(mission_id)
        replay = CSR.replay(mission_id)
        return jsonify(json.loads(replay.model_dump_json())), 200
    except KeyError:
        return jsonify({"error": "state_not_found", "mission_id": mission_id}), 404
    except Exception as e:
        logger.error(f"Error replaying URG constitutional state: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/marketplace/organs", methods=["GET"])
def ugr_marketplace_organs_query():
    """Public organ catalog for a tenant (no auth)."""
    try:
        from src.ugr.mission.marketplace import query_organs

        tenant_id = request.args.get("tenant_id") or "global"
        include_suspended = request.args.get("include_suspended", "").lower() in {"1", "true", "yes"}
        return jsonify(query_organs(tenant_id=tenant_id, include_suspended=include_suspended)), 200
    except Exception as e:
        logger.error(f"Error querying URG marketplace organs: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/mission/governance", methods=["POST"])
def ugr_mission_governance():
    """Run a governance mutation mission under cloud_mutation law."""
    try:
        from src.ugr.mission.mission_runtime import build_mission_runtime

        data = request.get_json(silent=True) or {}
        mission_payload = dict(data.get("mission") or data)
        mission_payload["mission_kind"] = "governance_mutation"
        if not str(mission_payload.get("operator_id") or "").strip():
            return jsonify({"error": "operator_id is required"}), 400
        if not str(mission_payload.get("mutation_target") or "").strip():
            return jsonify({"error": "mutation_target is required"}), 400
        result = build_mission_runtime().run_mission(mission_payload)
        status_code = 200 if result.get("status") in {"ok", "blocked", "rejected"} else 500
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error running URG governance mission: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/mission/run", methods=["POST"])
def ugr_mission_run():
    """Run a URG mission — multi-step routing across provider organs under cloud invariants."""
    try:
        from src.ugr.mission.mission_runtime import build_mission_runtime

        data = request.get_json(silent=True) or {}
        mission_payload = dict(data.get("mission") or data)
        steps = list(mission_payload.get("steps") or [])
        if not steps:
            return jsonify({"error": "mission.steps is required (at least one step)"}), 400
        if not str(mission_payload.get("operator_id") or "").strip():
            return jsonify({"error": "operator_id is required"}), 400
        if not str(mission_payload.get("aais_instance_id") or "").strip():
            return jsonify({"error": "aais_instance_id is required"}), 400
        result = build_mission_runtime().run_mission(mission_payload)
        status_code = 200 if result.get("status") in {"ok", "blocked", "rejected"} else 500
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error running URG mission: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/deliberate", methods=["POST"])
def ugr_deliberate():
    """Run a governed multi-lane deliberation through the Unified Governed Runtime."""
    try:
        data = request.get_json(silent=True) or {}
        question = str(data.get("question") or "").strip()
        if not question:
            return jsonify({"error": "question is required"}), 400
        result = ugr_runtime.handle_request(
            {
                "question": question,
                "intent": data.get("intent") or "general_qa",
                "tenant_id": data.get("tenant_id") or "default",
                "context": dict(data.get("context") or {}),
                "lane_types": list(data.get("lane_types") or []),
            }
        )
        status_code = 200 if result.get("status") in {"ok", "blocked", "rejected"} else 500
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error running UGR deliberation: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/ingest", methods=["POST"])
def ugr_ingest():
    """Run governed curated ingestion for one configured source."""
    try:
        from src.ugr.ingestion.pipeline import GovernedIngestionPipeline

        data = request.get_json(silent=True) or {}
        source_id = str(data.get("source_id") or "").strip()
        if not source_id:
            return jsonify({"error": "source_id is required"}), 400
        pipeline = GovernedIngestionPipeline()
        result = pipeline.run_source(source_id, dry_run=bool(data.get("dry_run")))
        status_code = 200 if result.status in {"ok", "no_accepted_proposals", "quarantined"} else 400
        return jsonify(result.to_dict()), status_code
    except Exception as e:
        logger.error(f"Error running UGR ingestion: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/ingest/sources", methods=["GET"])
def ugr_ingest_sources():
    """List configured ingestion sources."""
    try:
        from src.ugr.ingestion.config import IngestionConfig

        config = IngestionConfig()
        return jsonify(
            {
                "sources": [source.to_dict() for source in config.sources.values()],
                "enabled": [source.source_id for source in config.enabled_sources()],
            }
        )
    except Exception as e:
        logger.error(f"Error listing UGR ingestion sources: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/platform/tenants", methods=["GET"])
def ugr_platform_tenants():
    """List configured UGR tenant overlays."""
    try:
        from src.ugr.platform.tenant_registry import TenantRegistry

        registry = TenantRegistry()
        return jsonify({"tenants": [tenant.to_dict() for tenant in registry.list_tenants()]})
    except Exception as e:
        logger.error(f"Error listing UGR platform tenants: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/platform/shadow-eval", methods=["POST"])
def ugr_platform_shadow_eval():
    """Compare prod vs shadow UGR deliberation for cognition CI/CD."""
    try:
        from src.ugr.platform.shadow_runtime import ShadowRuntimeEvaluator

        data = request.get_json(silent=True) or {}
        question = str(data.get("question") or "").strip()
        if not question:
            return jsonify({"error": "question is required"}), 400
        evaluator = ShadowRuntimeEvaluator()
        result = evaluator.evaluate(
            {
                "question": question,
                "intent": data.get("intent") or "general_qa",
                "tenant_id": data.get("tenant_id") or "default",
                "context": dict(data.get("context") or {}),
                "lane_types": list(data.get("lane_types") or []),
            }
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error running UGR shadow evaluation: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/platform/cicd/evaluate", methods=["POST"])
def ugr_platform_cicd_evaluate():
    """Run cognition CI/CD promotion decision for a deliberation request."""
    try:
        from src.ugr.platform.cognition_cicd import CognitionCICDPipeline

        data = request.get_json(silent=True) or {}
        pipeline = CognitionCICDPipeline()
        if data.get("comparison"):
            result = pipeline.evaluate_comparison(dict(data.get("comparison") or {}))
        else:
            question = str(data.get("question") or "").strip()
            if not question:
                return jsonify({"error": "question or comparison is required"}), 400
            result = pipeline.evaluate(
                {
                    "question": question,
                    "intent": data.get("intent") or "general_qa",
                    "tenant_id": data.get("tenant_id") or "default",
                    "context": dict(data.get("context") or {}),
                    "lane_types": list(data.get("lane_types") or []),
                }
            )
        status_code = 200 if result.get("status") == "ok" else 500
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error running UGR cognition CI/CD: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/graph/stats", methods=["GET"])
def ugr_graph_stats():
    """Return UGR graph index statistics when enabled."""
    try:
        from src.ugr.graph_index.store import graph_index_enabled

        stats = ugr_runtime.ledger.graph_index_stats() if hasattr(ugr_runtime, "ledger") else None
        return jsonify({"enabled": graph_index_enabled(), "stats": stats}), 200
    except Exception as e:
        logger.error(f"Error reading UGR graph index stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/graph/query", methods=["POST"])
def ugr_graph_query():
    """Query the UGR graph index (requires UGR_GRAPH_ENABLED=1)."""
    try:
        data = request.get_json(silent=True) or {}
        terms = list(data.get("terms") or [])
        subject = str(data.get("subject") or "").strip()
        tenant_scope = data.get("tenant_scope")
        limit = int(data.get("limit") or 20)
        ledger = ugr_runtime.ledger if hasattr(ugr_runtime, "ledger") else None
        if ledger is None:
            return jsonify({"error": "ugr runtime ledger unavailable"}), 500
        if subject:
            matches = ledger.query_by_subject(subject, tenant_scope=tenant_scope, limit=limit)
        else:
            if not terms:
                return jsonify({"error": "terms or subject is required"}), 400
            matches = ledger.query_related(terms, tenant_scope=tenant_scope, limit=limit)
        return jsonify({"matches": matches, "stats": ledger.graph_index_stats()}), 200
    except Exception as e:
        logger.error(f"Error querying UGR graph index: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/graph/rebuild", methods=["POST"])
def ugr_graph_rebuild():
    """Rebuild the in-memory graph index from canonical JSONL."""
    try:
        ledger = ugr_runtime.ledger if hasattr(ugr_runtime, "ledger") else None
        if ledger is None:
            return jsonify({"error": "ugr runtime ledger unavailable"}), 500
        result = ledger.rebuild_graph_index()
        if result is None:
            return jsonify({"error": "UGR_GRAPH_ENABLED is not active"}), 400
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error rebuilding UGR graph index: {e}")
        return jsonify({"error": str(e)}), 500


_embryo_gateway = None


def _get_embryo_gateway():
    global _embryo_gateway
    if _embryo_gateway is None:
        from src.ugr.embryo.gateway import UGREmbryoGateway

        _embryo_gateway = UGREmbryoGateway(runtime=ugr_runtime)
    return _embryo_gateway


@app.route("/api/ugr/v0/health", methods=["GET"])
def ugr_v0_health():
    """Embryo v0 component health snapshot."""
    try:
        return jsonify(_get_embryo_gateway().health()), 200
    except Exception as e:
        logger.error(f"Error reading UGR embryo v0 health: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/v0/deliberate", methods=["POST"])
def ugr_v0_deliberate():
    """Run governed deliberation through the embryo v0 gateway."""
    try:
        data = request.get_json(silent=True) or {}
        result = _get_embryo_gateway().deliberate(data)
        status_code = 200 if result.get("status") in {"ok", "blocked", "rejected"} else 500
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error running UGR embryo v0 deliberation: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/v0/ingest", methods=["POST"])
def ugr_v0_ingest():
    """Run governed ingestion through the embryo v0 gateway."""
    try:
        data = request.get_json(silent=True) or {}
        source_id = str(data.get("source_id") or "").strip()
        if not source_id:
            return jsonify({"error": "source_id is required"}), 400
        result = _get_embryo_gateway().ingest(source_id=source_id, dry_run=bool(data.get("dry_run")))
        status_code = 200 if result.get("status") in {"ok", "no_accepted_proposals", "quarantined"} else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error running UGR embryo v0 ingestion: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/v0/ingest/sources", methods=["GET"])
def ugr_v0_ingest_sources():
    """List ingestion sources via embryo v0 gateway."""
    try:
        return jsonify(_get_embryo_gateway().ingest_sources()), 200
    except Exception as e:
        logger.error(f"Error listing UGR embryo v0 ingestion sources: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/v0/graph/query", methods=["POST"])
def ugr_v0_graph_query():
    """Query pattern ledger via embryo v0 gateway."""
    try:
        data = request.get_json(silent=True) or {}
        terms = list(data.get("terms") or [])
        subject = str(data.get("subject") or "").strip()
        if not subject and not terms:
            return jsonify({"error": "terms or subject is required"}), 400
        result = _get_embryo_gateway().graph_query(
            terms=terms,
            subject=subject or None,
            tenant_scope=data.get("tenant_scope"),
            limit=int(data.get("limit") or 20),
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error querying UGR embryo v0 graph index: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/v0/shadow-eval", methods=["POST"])
def ugr_v0_shadow_eval():
    """Run shadow deliberation comparison via embryo v0 gateway."""
    try:
        data = request.get_json(silent=True) or {}
        result = _get_embryo_gateway().shadow_eval(data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error running UGR embryo v0 shadow eval: {e}")
        return jsonify({"error": str(e)}), 500


_embryo_v1_gateway = None


def _get_embryo_v1_gateway():
    global _embryo_v1_gateway
    if _embryo_v1_gateway is None:
        from src.ugr.embryo.gateway_v1 import UGREmbryoGatewayV1

        _embryo_v1_gateway = UGREmbryoGatewayV1(runtime=ugr_runtime)
    return _embryo_v1_gateway


@app.route("/api/ugr/v1/health", methods=["GET"])
def ugr_v1_health():
    """Embryo v1 component health snapshot."""
    try:
        return jsonify(_get_embryo_v1_gateway().health()), 200
    except Exception as e:
        logger.error(f"Error reading UGR embryo v1 health: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/v1/causal/query", methods=["POST"])
def ugr_v1_causal_query():
    """Walk causal graph from a claim via embryo v1 gateway."""
    try:
        data = request.get_json(silent=True) or {}
        claim_id = str(data.get("claim_id") or "").strip()
        if not claim_id:
            return jsonify({"error": "claim_id is required"}), 400
        result = _get_embryo_v1_gateway().causal_query(
            claim_id=claim_id,
            depth=data.get("depth"),
            tenant_scope=data.get("tenant_scope"),
            limit=int(data.get("limit") or 50),
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error querying UGR embryo v1 causal graph: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/v1/provenance", methods=["POST"])
def ugr_v1_provenance_query():
    """Query provenance edges for a claim via embryo v1 gateway."""
    try:
        data = request.get_json(silent=True) or {}
        claim_id = str(data.get("claim_id") or "").strip()
        if not claim_id:
            return jsonify({"error": "claim_id is required"}), 400
        result = _get_embryo_v1_gateway().provenance_query(
            claim_id=claim_id,
            limit=int(data.get("limit") or 50),
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error querying UGR embryo v1 provenance: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/v1/regions/health", methods=["GET"])
def ugr_v1_regions_health():
    """Region health overlay snapshot via embryo v1 gateway."""
    try:
        return jsonify(_get_embryo_v1_gateway().regions_health()), 200
    except Exception as e:
        logger.error(f"Error reading UGR embryo v1 region health: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ugr/v1/causal/rebuild", methods=["POST"])
def ugr_v1_causal_rebuild():
    """Rebuild causal graph from canonical JSONL via embryo v1 gateway."""
    try:
        return jsonify(_get_embryo_v1_gateway().rebuild_causal_graph()), 200
    except Exception as e:
        logger.error(f"Error rebuilding UGR embryo v1 causal graph: {e}")
        return jsonify({"error": str(e)}), 500


# Infinity 1 operator product seam (see src/operator_api_routes.py):
# GET /api/operator/ledger
# GET /api/operator/ledger/digest
# GET /api/operator/ledger/query
# GET /api/operator/ledger/diff
# GET /api/operator/ledger/federation/
# GET /api/operator/replay/<subject_type>/<subject_id>/timeline
# GET /api/operator/plugins
# GET /api/operator/plugins/libraries
# GET /api/operator/plugins/workflows
# POST /api/operator/plugins/rescan
# GET /api/operator/organs
# POST /api/operator/workflows/<workflow_id>/execute
# GET /api/operator/brain/sessions
# POST /api/operator/brain/sessions
# GET /api/jarvis/operator-decision-ledger/status


@app.route("/api/operator/console", methods=["GET"])
def get_operator_console():
    """UGR + Cloud Forge operator console snapshot (advisory readout only)."""
    try:
        return jsonify(build_operator_console_snapshot(runtime=ugr_runtime)), 200
    except Exception as e:
        logger.error(f"Error building operator console snapshot: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/operator/console/mesh-health", methods=["GET"])
def get_operator_console_mesh_health():
    """Lightweight mesh health poll for operator console live refresh."""
    try:
        return jsonify(poll_mesh_health()), 200
    except Exception as e:
        logger.error(f"Error polling operator console mesh health: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/operator/console/traces", methods=["GET"])
def get_operator_console_traces():
    """Read-only UGR deliberation trace viewer."""
    try:
        trace_id = str(request.args.get("trace_id") or "").strip() or None
        limit = max(1, min(int(request.args.get("limit") or 20), 100))
        payload = load_deliberation_traces(runtime=ugr_runtime, limit=limit, trace_id=trace_id)
        return jsonify(payload), 200
    except Exception as e:
        logger.error(f"Error loading operator console traces: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/operator/console/forge-platform", methods=["GET"])
def get_operator_console_forge_platform():
    """Forge platform dashboard JSON for operator console."""
    try:
        live = str(request.args.get("live") or "").strip().lower() in {"1", "true", "yes", "on"}
        return jsonify(load_forge_platform_dashboard(live_checks=live)), 200
    except Exception as e:
        logger.error(f"Error loading forge platform dashboard: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/blueprint", methods=["GET"])
def get_aais_blueprint():
    """Expose the live AAIS blueprint so Jarvis can explain how the system fits together."""
    try:
        requested_mode = _get_model_mode()
        status = "initialized" if ai_model is not None else "not_initialized"
        return jsonify(
            {
                "requested_model_mode": requested_mode,
                "active_model_mode": ai_mode,
                "ai_status": status,
                "blueprint": build_aais_blueprint(
                    requested_model_mode=requested_mode,
                    active_model_mode=ai_mode,
                    ai_status=status,
                ),
            }
        )
    except Exception as e:
        logger.error(f"Error building AAIS blueprint payload: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/missions", methods=["GET"])
def get_mission_board():
    """Return the persistent Mission Board snapshot for Jarvis."""
    try:
        session_id = request.args.get("session_id")
        return jsonify({"mission_board": mission_board.snapshot(session_id=session_id)})
    except Exception as e:
        logger.error(f"Error reading Mission Board: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/lineage/<mission_id>", methods=["GET"])
def get_lineage_graph(mission_id):
    """Return the UL lineage graph for one mission (read-only)."""
    try:
        from src.ul_lineage import build_graph

        session_id = request.args.get("session_id")
        graph = build_graph(str(mission_id), session_id=session_id)
        return jsonify(attach_ul_substrate({"lineage_graph": graph}))
    except Exception as e:
        logger.error(f"Error reading lineage graph for {mission_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/safety-envelope/status", methods=["GET"])
def get_safety_envelope_status():
    """Read-only safety envelope threshold snapshot (Alt-5 organ)."""
    try:
        from src.safety_envelope import build_envelope_status

        return jsonify(attach_ul_substrate({"safety_envelope": build_envelope_status()}))
    except Exception as e:
        logger.error(f"Error reading safety envelope status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/operator-profile", methods=["GET"])
def get_operator_profile():
    """Normalized operator profile snapshot (Alt-5 organ)."""
    try:
        from src.operator_profile_organ import build_operator_profile

        profile_id = request.args.get("profile_id") or "operator"
        return jsonify(
            attach_ul_substrate(
                {"operator_profile": build_operator_profile(knowledge_authority, profile_id=profile_id)}
            )
        )
    except Exception as e:
        logger.error(f"Error reading operator profile: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/adaptive-lanes/status", methods=["GET"])
def get_adaptive_lane_status():
    """Awakened Tier 5 operator-weighted lane registry (Alt-6 organ)."""
    try:
        from src.adaptive_lane_organ import build_adaptive_lane_status

        return jsonify(attach_ul_substrate({"adaptive_lanes": build_adaptive_lane_status()}))
    except Exception as e:
        logger.error(f"Error reading adaptive lane status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/coherence-fabric/status", methods=["GET"])
def get_coherence_fabric_status():
    """Cross-plane coherence snapshot — profile, lanes, and envelopes (Alt-7 organ)."""
    try:
        from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

        bridge_snapshot = jarvis_operator.capability_bridge_snapshot()
        pipeline_trace = None
        session_id = str(request.args.get("session_id") or "").strip()
        if session_id:
            session = conversation_memory.get_session(session_id)
            if session:
                pipeline_trace = _previous_governed_pipeline(session)
        return jsonify(
            attach_ul_substrate(
                {
                    "coherence_fabric": build_coherence_fabric_status(
                        bridge_snapshot=bridge_snapshot,
                        pipeline_trace=pipeline_trace,
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading coherence fabric status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/reflection-runtime/status", methods=["GET"])
def get_reflection_runtime_status():
    """Read-only Reflection Runtime organ snapshot (Alt-5 wave 2)."""
    try:
        from src.reflection_runtime_organ import build_reflection_runtime_status

        return jsonify(
            attach_ul_substrate({"reflection_runtime": build_reflection_runtime_status()})
        )
    except Exception as e:
        logger.error(f"Error reading reflection runtime status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory-runtime/status", methods=["GET"])
def get_memory_runtime_status():
    """Read-only Memory Runtime organ snapshot (Alt-5 wave 2)."""
    try:
        from src.memory_runtime_organ import build_memory_runtime_status

        return jsonify(attach_ul_substrate({"memory_runtime": build_memory_runtime_status()}))
    except Exception as e:
        logger.error(f"Error reading memory runtime status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/continuity-witness/status", methods=["GET"])
def get_continuity_witness_status():
    """Read-only Continuity Witness organ snapshot (Alt-8 wave)."""
    try:
        from src.continuity_witness_organ import build_continuity_witness_status

        return jsonify(
            attach_ul_substrate({"continuity_witness": build_continuity_witness_status()})
        )
    except Exception as e:
        logger.error(f"Error reading continuity witness status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/narrative-continuity/status", methods=["GET"])
def get_narrative_continuity_status():
    """Read-only Narrative Continuity organ snapshot (Alt-8 wave)."""
    try:
        from src.narrative_continuity_organ import build_narrative_continuity_status

        return jsonify(
            attach_ul_substrate({"narrative_continuity": build_narrative_continuity_status()})
        )
    except Exception as e:
        logger.error(f"Error reading narrative continuity status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/intent-agency/status", methods=["GET"])
def get_intent_agency_status():
    """Read-only Intent Agency organ snapshot (Alt-8 wave)."""
    try:
        from src.intent_agency_organ import build_intent_agency_status

        return jsonify(attach_ul_substrate({"intent_agency": build_intent_agency_status()}))
    except Exception as e:
        logger.error(f"Error reading intent agency status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/phase-gate/status", methods=["GET"])
def get_phase_gate_status():
    """Read-only Phase Gate organ snapshot (Alt-9 wave)."""
    try:
        from src.phase_gate_organ import build_phase_gate_status

        return jsonify(attach_ul_substrate({"phase_gate": build_phase_gate_status()}))
    except Exception as e:
        logger.error(f"Error reading phase gate status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/realtime-predictor/status", methods=["GET"])
def get_realtime_predictor_status():
    """Read-only Realtime Predictor organ snapshot (Alt-9 wave)."""
    try:
        from src.realtime_event_cause_predictor_organ import build_realtime_predictor_status

        pipeline_trace = None
        session_id = str(request.args.get("session_id") or "").strip()
        if session_id:
            session = conversation_memory.get_session(session_id)
            if session:
                pipeline_trace = _previous_governed_pipeline(session)
        return jsonify(
            attach_ul_substrate(
                {
                    "realtime_predictor": build_realtime_predictor_status(
                        governed_pipeline=pipeline_trace
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading realtime predictor status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/invariant-engine/status", methods=["GET"])
def get_invariant_engine_status():
    """Read-only Invariant Engine organ snapshot (Alt-9 wave)."""
    try:
        from src.invariant_engine_organ import build_invariant_engine_status

        pipeline_trace = None
        companion_lane = None
        session_id = str(request.args.get("session_id") or "").strip()
        if session_id:
            session = conversation_memory.get_session(session_id)
            if session:
                pipeline_trace = _previous_governed_pipeline(session)
                companion_lane = companion_lane_identity(
                    session.metadata.get("persona_mode"),
                    session.metadata.get("response_mode"),
                )
        return jsonify(
            attach_ul_substrate(
                {
                    "invariant_engine": build_invariant_engine_status(
                        companion_lane=companion_lane,
                        governed_pipeline=pipeline_trace,
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading invariant engine status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/verification-gate/status", methods=["GET"])
def get_verification_gate_organ_status():
    """Read-only Verification Gate organ snapshot (Alt-10 wave)."""
    try:
        from src.verification_gate_organ import build_verification_gate_status

        return jsonify(
            attach_ul_substrate({"verification_gate": build_verification_gate_status()})
        )
    except Exception as e:
        logger.error(f"Error reading verification gate status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/knowledge-authority/status", methods=["GET"])
def get_knowledge_authority_organ_status():
    """Read-only Knowledge Authority organ snapshot (Alt-10 wave)."""
    try:
        from src.knowledge_authority_organ import build_knowledge_authority_status

        return jsonify(
            attach_ul_substrate({"knowledge_authority": build_knowledge_authority_status()})
        )
    except Exception as e:
        logger.error(f"Error reading knowledge authority status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/scorpion-bridge/status", methods=["GET"])
def get_scorpion_bridge_status():
    """Read-only Scorpion Bridge organ snapshot (Alt-10 wave)."""
    try:
        from src.scorpion_bridge_organ import build_scorpion_bridge_status

        return jsonify(attach_ul_substrate({"scorpion_bridge": build_scorpion_bridge_status()}))
    except Exception as e:
        logger.error(f"Error reading scorpion bridge status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/mechanic-handoff/status", methods=["GET"])
def get_mechanic_handoff_status():
    """Read-only Mechanic Handoff organ snapshot (Alt-10 wave)."""
    try:
        from src.mechanic_handoff_organ import build_mechanic_handoff_status

        session_metadata = None
        session_id = str(request.args.get("session_id") or "").strip()
        if session_id:
            session = conversation_memory.get_session(session_id)
            if session:
                session_metadata = dict(session.metadata or {})
        return jsonify(
            attach_ul_substrate(
                {
                    "mechanic_handoff": build_mechanic_handoff_status(
                        session_metadata=session_metadata
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading mechanic handoff status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/forensic-triangulation/status", methods=["GET"])
def get_forensic_triangulation_organ_status():
    """Read-only Forensic Triangulation organ snapshot (Alt-10 wave)."""
    try:
        from src.forensic_triangulation_organ import build_forensic_triangulation_status

        return jsonify(
            attach_ul_substrate(
                {"forensic_triangulation": build_forensic_triangulation_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading forensic triangulation organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/immune-observe/status", methods=["GET"])
def get_immune_observe_status():
    """Read-only Immune Observe organ snapshot (Alt-10 wave)."""
    try:
        from src.immune_observe_organ import build_immune_observe_status

        return jsonify(attach_ul_substrate({"immune_observe": build_immune_observe_status()}))
    except Exception as e:
        logger.error(f"Error reading immune observe status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/policy-gate/status", methods=["GET"])
def get_policy_gate_status():
    """Read-only Policy Gate organ snapshot (Alt-10 wave)."""
    try:
        from src.policy_gate_organ import build_policy_gate_status

        return jsonify(attach_ul_substrate({"policy_gate": build_policy_gate_status()}))
    except Exception as e:
        logger.error(f"Error reading policy gate status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/predictor-immune-bridge/status", methods=["GET"])
def get_predictor_immune_bridge_status():
    """Read-only Predictor Immune Bridge organ snapshot (Alt-10 wave)."""
    try:
        from src.predictor_immune_bridge_organ import build_predictor_immune_bridge_status

        pipeline_trace = None
        session_id = str(request.args.get("session_id") or "").strip()
        if session_id:
            session = conversation_memory.get_session(session_id)
            if session:
                pipeline_trace = _previous_governed_pipeline(session)
        return jsonify(
            attach_ul_substrate(
                {
                    "predictor_immune_bridge": build_predictor_immune_bridge_status(
                        governed_pipeline=pipeline_trace
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading predictor immune bridge status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/cognitive-bridge/status", methods=["GET"])
def get_cognitive_bridge_organ_status():
    """Read-only Cognitive Bridge organ snapshot (Alt-11 wave)."""
    try:
        from src.cognitive_bridge_organ import build_cognitive_bridge_status

        return jsonify(
            attach_ul_substrate({"cognitive_bridge": build_cognitive_bridge_status()})
        )
    except Exception as e:
        logger.error(f"Error reading cognitive bridge status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/governed-event-chain/status", methods=["GET"])
def get_governed_event_chain_organ_status():
    """Read-only Governed Event Chain organ snapshot (Alt-11 wave)."""
    try:
        from src.governed_event_chain_organ import build_governed_event_chain_status

        return jsonify(
            attach_ul_substrate(
                {"governed_event_chain": build_governed_event_chain_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading governed event chain status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/tracing-spine/status", methods=["GET"])
def get_tracing_spine_organ_status():
    """Read-only Tracing Spine organ snapshot (Alt-11 wave)."""
    try:
        from src.tracing_spine_organ import build_tracing_spine_status

        return jsonify(
            attach_ul_substrate({"tracing_spine": build_tracing_spine_status()})
        )
    except Exception as e:
        logger.error(f"Error reading tracing spine status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/aris-boundary/status", methods=["GET"])
def get_aris_boundary_organ_status():
    """Read-only ARIS Boundary organ snapshot (Alt-11 wave)."""
    try:
        from src.aris_boundary_organ import build_aris_boundary_status

        return jsonify(
            attach_ul_substrate({"aris_boundary": build_aris_boundary_status()})
        )
    except Exception as e:
        logger.error(f"Error reading ARIS boundary status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/capability-module/status", methods=["GET"])
def get_capability_module_organ_status():
    """Read-only Capability Module organ snapshot (Alt-11 wave)."""
    try:
        from src.capability_module_organ import build_capability_module_status

        return jsonify(
            attach_ul_substrate(
                {"capability_module": build_capability_module_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading capability module status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/patchforge/status", methods=["GET"])
def get_patchforge_organ_status():
    """Read-only Patchforge organ snapshot (Alt-11 wave)."""
    try:
        from src.patchforge_organ import build_patchforge_status

        return jsonify(attach_ul_substrate({"patchforge": build_patchforge_status()}))
    except Exception as e:
        logger.error(f"Error reading patchforge organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/change-scope/status", methods=["GET"])
def get_change_scope_organ_status():
    """Read-only Change Scope organ snapshot (Alt-11 wave)."""
    try:
        from src.change_scope_organ import build_change_scope_status

        return jsonify(
            attach_ul_substrate({"change_scope": build_change_scope_status()})
        )
    except Exception as e:
        logger.error(f"Error reading change scope status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/patch-verification/status", methods=["GET"])
def get_patch_verification_organ_status():
    """Read-only Patch Verification organ snapshot (Alt-11 wave)."""
    try:
        from src.patch_verification_organ import build_patch_verification_status

        return jsonify(
            attach_ul_substrate(
                {"patch_verification": build_patch_verification_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading patch verification status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/otem-bounded/status", methods=["GET"])
def get_otem_bounded_organ_status():
    """Read-only OTEM Bounded organ snapshot (Alt-12 wave)."""
    try:
        from src.otem_bounded_organ import build_otem_bounded_status

        return jsonify(attach_ul_substrate({"otem_bounded": build_otem_bounded_status()}))
    except Exception as e:
        logger.error(f"Error reading otem bounded status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/direct-challenge/status", methods=["GET"])
def get_direct_challenge_organ_status():
    """Read-only Direct Challenge organ snapshot (Alt-12 wave)."""
    try:
        from src.direct_challenge_organ import build_direct_challenge_status

        return jsonify(
            attach_ul_substrate({"direct_challenge": build_direct_challenge_status()})
        )
    except Exception as e:
        logger.error(f"Error reading direct challenge status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/orchestration-spine/status", methods=["GET"])
def get_orchestration_spine_organ_status():
    """Read-only Orchestration Spine organ snapshot (Alt-12 wave)."""
    try:
        from src.orchestration_spine_organ import build_orchestration_spine_status

        return jsonify(
            attach_ul_substrate(
                {"orchestration_spine": build_orchestration_spine_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading orchestration spine status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/operator-health-sentinel/status", methods=["GET"])
def get_operator_health_sentinel_organ_status():
    """Read-only Operator Health Sentinel organ snapshot (Alt-12 wave)."""
    try:
        from src.operator_health_sentinel_organ import (
            build_operator_health_sentinel_organ_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "operator_health_sentinel": (
                        build_operator_health_sentinel_organ_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading operator health sentinel status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/governed-realtime-lane/status", methods=["GET"])
def get_governed_realtime_lane_organ_status():
    """Read-only Governed Realtime Lane organ snapshot (Alt-12 wave)."""
    try:
        from src.governed_realtime_lane_organ import build_governed_realtime_lane_status

        return jsonify(
            attach_ul_substrate(
                {"governed_realtime_lane": build_governed_realtime_lane_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading governed realtime lane status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v8-runtime/status", methods=["GET"])
def get_v8_runtime_organ_status():
    """Read-only V8 Runtime organ snapshot (Alt-12 wave)."""
    try:
        from src.v8_runtime_organ import build_v8_runtime_status

        return jsonify(attach_ul_substrate({"v8_runtime": build_v8_runtime_status()}))
    except Exception as e:
        logger.error(f"Error reading v8 runtime status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/patch-apply/status", methods=["GET"])
def get_patch_apply_organ_status():
    """Read-only Patch Apply organ snapshot (Alt-12 wave)."""
    try:
        from src.patch_apply_organ import build_patch_apply_status

        return jsonify(attach_ul_substrate({"patch_apply": build_patch_apply_status()}))
    except Exception as e:
        logger.error(f"Error reading patch apply status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/patch-execution-preview/status", methods=["GET"])
def get_patch_execution_preview_organ_status():
    """Read-only Patch Execution Preview organ snapshot (Alt-12 wave)."""
    try:
        from src.patch_execution_preview_organ import build_patch_execution_preview_status

        return jsonify(
            attach_ul_substrate(
                {
                    "patch_execution_preview": build_patch_execution_preview_status()
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading patch execution preview status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/run-ledger/status", methods=["GET"])
def get_run_ledger_organ_status():
    """Read-only Run Ledger organ snapshot (Alt-12 wave)."""
    try:
        from src.run_ledger_organ import build_run_ledger_status

        return jsonify(attach_ul_substrate({"run_ledger": build_run_ledger_status()}))
    except Exception as e:
        logger.error(f"Error reading run ledger status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/ul-lineage-console/status", methods=["GET"])
def get_ul_lineage_console_organ_status():
    """Read-only UL Lineage Console organ snapshot (Alt-13 wave)."""
    try:
        from src.ul_lineage_console_organ import build_ul_lineage_console_status

        return jsonify(
            attach_ul_substrate({"ul_lineage_console": build_ul_lineage_console_status()})
        )
    except Exception as e:
        logger.error(f"Error reading ul lineage console status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/module-governance/status", methods=["GET"])
def get_module_governance_organ_status():
    """Read-only Module Governance organ snapshot (Alt-13 wave)."""
    try:
        from src.module_governance_organ import build_module_governance_status

        return jsonify(
            attach_ul_substrate({"module_governance": build_module_governance_status()})
        )
    except Exception as e:
        logger.error(f"Error reading module governance status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/recipe-module/status", methods=["GET"])
def get_recipe_module_organ_status():
    """Read-only Recipe Module organ snapshot (Alt-13 wave)."""
    try:
        from src.recipe_module_organ import build_recipe_module_status

        return jsonify(attach_ul_substrate({"recipe_module": build_recipe_module_status()}))
    except Exception as e:
        logger.error(f"Error reading recipe module organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/imagine-generator/status", methods=["GET"])
def get_imagine_generator_organ_status():
    """Read-only Imagine Generator organ snapshot (Alt-13 wave)."""
    try:
        from src.imagine_generator_organ import build_imagine_generator_status

        return jsonify(
            attach_ul_substrate({"imagine_generator": build_imagine_generator_status()})
        )
    except Exception as e:
        logger.error(f"Error reading imagine generator organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/story-forge-lane/status", methods=["GET"])
def get_story_forge_lane_organ_status():
    """Read-only Story Forge lane organ snapshot (Alt-13 wave)."""
    try:
        from src.story_forge_lane_organ import build_story_forge_lane_status

        return jsonify(
            attach_ul_substrate({"story_forge_lane": build_story_forge_lane_status()})
        )
    except Exception as e:
        logger.error(f"Error reading story forge lane status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/beatbox-lane/status", methods=["GET"])
def get_beatbox_lane_organ_status():
    """Read-only Beatbox lane organ snapshot (Alt-13 wave)."""
    try:
        from src.beatbox_lane_organ import build_beatbox_lane_status

        return jsonify(attach_ul_substrate({"beatbox_lane": build_beatbox_lane_status()}))
    except Exception as e:
        logger.error(f"Error reading beatbox lane status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/speakers-lane/status", methods=["GET"])
def get_speakers_lane_organ_status():
    """Read-only Speakers lane organ snapshot (Alt-13 wave)."""
    try:
        from src.speakers_lane_organ import build_speakers_lane_status

        return jsonify(attach_ul_substrate({"speakers_lane": build_speakers_lane_status()}))
    except Exception as e:
        logger.error(f"Error reading speakers lane status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/human-voice-extraction/status", methods=["GET"])
def get_human_voice_extraction_organ_status():
    """Read-only Human Voice Extraction organ snapshot (Alt-13 wave)."""
    try:
        from src.human_voice_extraction_organ import build_human_voice_extraction_status

        return jsonify(
            attach_ul_substrate(
                {"human_voice_extraction": build_human_voice_extraction_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading human voice extraction organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/story-forge-launcher/status", methods=["GET"])
def get_story_forge_launcher_organ_status():
    """Read-only Story Forge launcher organ snapshot (Release 28)."""
    try:
        from src.story_forge_launcher_organ import build_story_forge_launcher_status

        return jsonify(
            attach_ul_substrate(
                {"story_forge_launcher": build_story_forge_launcher_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading story forge launcher status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/movie-renderer-lane/status", methods=["GET"])
def get_movie_renderer_lane_organ_status():
    """Read-only movie renderer lane organ snapshot (Release 28)."""
    try:
        from src.movie_renderer_lane_organ import build_movie_renderer_lane_status

        return jsonify(
            attach_ul_substrate(
                {"movie_renderer_lane": build_movie_renderer_lane_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading movie renderer lane status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/text-game-to-video/status", methods=["GET"])
def get_text_game_to_video_organ_status():
    """Read-only text-game-to-video front door snapshot (Release 28)."""
    try:
        from src.text_game_to_video_organ import build_text_game_to_video_status

        return jsonify(
            attach_ul_substrate(
                {"text_game_to_video": build_text_game_to_video_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading text-game-to-video status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/game-front-door/status", methods=["GET"])
def get_game_front_door_organ_status():
    """Read-only game front door organ snapshot (Release 28)."""
    try:
        from src.game_front_door_organ import build_game_front_door_status

        return jsonify(
            attach_ul_substrate({"game_front_door": build_game_front_door_status()})
        )
    except Exception as e:
        logger.error(f"Error reading game front door status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/text-to-3d-world-lane/status", methods=["GET"])
def get_text_to_3d_world_lane_organ_status():
    """Read-only text-to-3D world lane organ snapshot (Release 28)."""
    try:
        from src.text_to_3d_world_lane_organ import build_text_to_3d_world_lane_status

        return jsonify(
            attach_ul_substrate(
                {"text_to_3d_world_lane": build_text_to_3d_world_lane_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading text-to-3d world lane status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/world-pack-lane/status", methods=["GET"])
def get_world_pack_lane_organ_status():
    """Read-only world pack lane organ snapshot (Release 28)."""
    try:
        from src.world_pack_lane_organ import build_world_pack_lane_status

        return jsonify(
            attach_ul_substrate({"world_pack_lane": build_world_pack_lane_status()})
        )
    except Exception as e:
        logger.error(f"Error reading world pack lane status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/media-processor-bridge/status", methods=["GET"])
def get_media_processor_bridge_organ_status():
    """Read-only media processor bridge organ snapshot (Release 29)."""
    try:
        from src.media_processor_bridge_organ import build_media_processor_bridge_status

        return jsonify(
            attach_ul_substrate(
                {"media_processor_bridge": build_media_processor_bridge_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading media processor bridge status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/narrative-trust-pack/status", methods=["GET"])
def get_narrative_trust_pack_organ_status():
    """Read-only Narrative Trust Pack organ snapshot (Alt-13 wave)."""
    try:
        from src.narrative_trust_pack_organ import build_narrative_trust_pack_status

        return jsonify(
            attach_ul_substrate({"narrative_trust_pack": build_narrative_trust_pack_status()})
        )
    except Exception as e:
        logger.error(f"Error reading narrative trust pack organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/document-vision/status", methods=["GET"])
def get_document_vision_organ_status():
    """Read-only Document Vision organ snapshot (Alt-14 wave)."""
    try:
        from src.document_vision_organ import build_document_vision_status

        return jsonify(
            attach_ul_substrate({"document_vision": build_document_vision_status()})
        )
    except Exception as e:
        logger.error(f"Error reading document vision organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/ui-vision/status", methods=["GET"])
def get_ui_vision_organ_status():
    """Read-only UI Vision organ snapshot (Alt-14 wave)."""
    try:
        from src.ui_vision_organ import build_ui_vision_status

        return jsonify(attach_ul_substrate({"ui_vision": build_ui_vision_status()}))
    except Exception as e:
        logger.error(f"Error reading ui vision organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/perception-gateway/status", methods=["GET"])
def get_perception_gateway_organ_status():
    """Read-only Perception Gateway organ snapshot (Alt-14 wave)."""
    try:
        from src.perception_gateway_organ import build_perception_gateway_status

        return jsonify(
            attach_ul_substrate({"perception_gateway": build_perception_gateway_status()})
        )
    except Exception as e:
        logger.error(f"Error reading perception gateway organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/spatial-reasoning/status", methods=["GET"])
def get_spatial_reasoning_organ_status():
    """Read-only Spatial Reasoning organ snapshot (Alt-14 wave)."""
    try:
        from src.spatial_reasoning_organ import build_spatial_reasoning_status

        return jsonify(
            attach_ul_substrate({"spatial_reasoning": build_spatial_reasoning_status()})
        )
    except Exception as e:
        logger.error(f"Error reading spatial reasoning organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/mystic-engine/status", methods=["GET"])
def get_mystic_engine_organ_status():
    """Read-only Mystic Engine organ snapshot (Alt-14 wave)."""
    try:
        from src.mystic_engine_organ import build_mystic_engine_status

        return jsonify(
            attach_ul_substrate({"mystic_engine": build_mystic_engine_status()})
        )
    except Exception as e:
        logger.error(f"Error reading mystic engine organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/perception-lane/status", methods=["GET"])
def get_perception_lane_organ_status():
    """Read-only Perception Lane organ snapshot (Alt-14 wave)."""
    try:
        from src.perception_lane_organ import build_perception_lane_status

        return jsonify(
            attach_ul_substrate({"perception_lane": build_perception_lane_status()})
        )
    except Exception as e:
        logger.error(f"Error reading perception lane organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/route-choice/status", methods=["GET"])
def get_route_choice_organ_status():
    """Read-only Route Choice organ snapshot (Alt-14 wave)."""
    try:
        from src.route_choice_organ import build_route_choice_status

        return jsonify(attach_ul_substrate({"route_choice": build_route_choice_status()}))
    except Exception as e:
        logger.error(f"Error reading route choice organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/specialist-route/status", methods=["GET"])
def get_specialist_route_organ_status():
    """Read-only Specialist Route organ snapshot (Alt-14 wave)."""
    try:
        from src.specialist_route_organ import build_specialist_route_status

        return jsonify(
            attach_ul_substrate({"specialist_route": build_specialist_route_status()})
        )
    except Exception as e:
        logger.error(f"Error reading specialist route organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/provider-route/status", methods=["GET"])
def get_provider_route_organ_status():
    """Read-only Provider Route organ snapshot (Alt-14 wave)."""
    try:
        from src.provider_route_organ import build_provider_route_status

        return jsonify(
            attach_ul_substrate({"provider_route": build_provider_route_status()})
        )
    except Exception as e:
        logger.error(f"Error reading provider route organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/reasoning-executive/status", methods=["GET"])
def get_reasoning_executive_organ_status():
    """Read-only Reasoning Executive organ snapshot (Alt-15 wave)."""
    try:
        from src.reasoning_executive_organ import build_reasoning_executive_status

        return jsonify(
            attach_ul_substrate(
                {"reasoning_executive": build_reasoning_executive_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading reasoning executive organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/attention/status", methods=["GET"])
def get_attention_organ_status():
    """Read-only Attention organ snapshot (Alt-15 wave)."""
    try:
        from src.attention_organ import build_attention_status

        return jsonify(attach_ul_substrate({"attention": build_attention_status()}))
    except Exception as e:
        logger.error(f"Error reading attention organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/coherence-projection/status", methods=["GET"])
def get_coherence_projection_organ_status():
    """Read-only Coherence Projection organ snapshot (Alt-15 wave)."""
    try:
        from src.coherence_projection_organ import build_coherence_projection_status

        return jsonify(
            attach_ul_substrate(
                {"coherence_projection": build_coherence_projection_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading coherence projection organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/deliberation/status", methods=["GET"])
def get_deliberation_organ_status():
    """Read-only Deliberation organ snapshot (Alt-15 wave)."""
    try:
        from src.deliberation_organ import build_deliberation_status

        return jsonify(attach_ul_substrate({"deliberation": build_deliberation_status()}))
    except Exception as e:
        logger.error(f"Error reading deliberation organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/planning/status", methods=["GET"])
def get_planning_organ_status():
    """Read-only Planning organ snapshot (Alt-15 wave)."""
    try:
        from src.planning_organ import build_planning_status

        return jsonify(attach_ul_substrate({"planning": build_planning_status()}))
    except Exception as e:
        logger.error(f"Error reading planning organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/cortex-arcs/status", methods=["GET"])
def get_cortex_arcs_organ_status():
    """Read-only Cortex Arcs organ snapshot (Alt-15 wave)."""
    try:
        from src.cortex_arcs_organ import build_cortex_arcs_status

        return jsonify(attach_ul_substrate({"cortex_arcs": build_cortex_arcs_status()}))
    except Exception as e:
        logger.error(f"Error reading cortex arcs organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/cognitive-execution/status", methods=["GET"])
def get_cognitive_execution_organ_status():
    """Read-only Cognitive Execution organ snapshot (Alt-15 wave)."""
    try:
        from src.cognitive_execution_organ import build_cognitive_execution_status

        return jsonify(
            attach_ul_substrate(
                {"cognitive_execution": build_cognitive_execution_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading cognitive execution organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/speaking-runtime/status", methods=["GET"])
def get_speaking_runtime_organ_status():
    """Read-only Speaking Runtime organ snapshot (Alt-15 wave)."""
    try:
        from src.speaking_runtime_organ import build_speaking_runtime_status

        return jsonify(
            attach_ul_substrate({"speaking_runtime": build_speaking_runtime_status()})
        )
    except Exception as e:
        logger.error(f"Error reading speaking runtime organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/nova-face/status", methods=["GET"])
def get_nova_face_organ_status():
    """Read-only Nova Face organ snapshot (Alt-15 wave)."""
    try:
        from src.nova_face_organ import build_nova_face_status

        return jsonify(attach_ul_substrate({"nova_face": build_nova_face_status()}))
    except Exception as e:
        logger.error(f"Error reading nova face organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/ai-factory/status", methods=["GET"])
def get_ai_factory_organ_status():
    """Read-only AI Factory organ snapshot (Alt-16 wave)."""
    try:
        from src.ai_factory_organ import build_ai_factory_status

        return jsonify(attach_ul_substrate({"ai_factory": build_ai_factory_status()}))
    except Exception as e:
        logger.error(f"Error reading ai factory organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/cogos-runtime-bridge/status", methods=["GET"])
def get_cogos_runtime_bridge_organ_status():
    """Read-only CoGOS runtime bridge organ snapshot (Alt-16 wave)."""
    try:
        from src.cogos_runtime_bridge_organ import build_cogos_runtime_bridge_status

        return jsonify(
            attach_ul_substrate(
                {"cogos_runtime_bridge": build_cogos_runtime_bridge_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading cogos runtime bridge organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/wolf-rehydration/status", methods=["GET"])
def get_wolf_rehydration_organ_status():
    """Read-only Wolf rehydration organ snapshot (Alt-16 wave)."""
    try:
        from src.wolf_rehydration_organ import build_wolf_rehydration_status

        return jsonify(
            attach_ul_substrate({"wolf_rehydration": build_wolf_rehydration_status()})
        )
    except Exception as e:
        logger.error(f"Error reading wolf rehydration organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/forge-contractor/status", methods=["GET"])
def get_forge_contractor_organ_status():
    """Read-only Forge contractor organ snapshot (Alt-16 wave)."""
    try:
        from src.forge_contractor_organ import build_forge_contractor_status

        return jsonify(
            attach_ul_substrate({"forge_contractor": build_forge_contractor_status()})
        )
    except Exception as e:
        logger.error(f"Error reading forge contractor organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/forge-eval/status", methods=["GET"])
def get_forge_eval_organ_status():
    """Read-only ForgeEval organ snapshot (Alt-16 wave)."""
    try:
        from src.forge_eval_organ import build_forge_eval_status

        return jsonify(attach_ul_substrate({"forge_eval": build_forge_eval_status()}))
    except Exception as e:
        logger.error(f"Error reading forge eval organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/evolve-engine/status", methods=["GET"])
def get_evolve_engine_organ_status():
    """Read-only Evolve Engine organ snapshot (Alt-16 wave)."""
    try:
        from src.evolve_engine_organ import build_evolve_engine_status

        return jsonify(attach_ul_substrate({"evolve_engine": build_evolve_engine_status()}))
    except Exception as e:
        logger.error(f"Error reading evolve engine organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/slingshot/status", methods=["GET"])
def get_slingshot_organ_status():
    """Read-only Slingshot organ snapshot (Alt-16 wave)."""
    try:
        from src.slingshot_organ import build_slingshot_status

        case_id = (request.args.get("case_id") or "").strip() or None
        return jsonify(
            attach_ul_substrate({"slingshot": build_slingshot_status(case_id=case_id)})
        )
    except Exception as e:
        logger.error(f"Error reading slingshot organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/operator-workbench/status", methods=["GET"])
def get_operator_workbench_organ_status():
    """Read-only operator workbench organ snapshot (Alt-16 wave)."""
    try:
        from src.operator_workbench_organ import build_operator_workbench_status

        return jsonify(
            attach_ul_substrate(
                {"operator_workbench": build_operator_workbench_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading operator workbench organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workflow-shell/status", methods=["GET"])
def get_workflow_shell_organ_status():
    """Read-only workflow shell organ snapshot (Alt-16 wave)."""
    try:
        from src.workflow_shell_organ import build_workflow_shell_status

        return jsonify(
            attach_ul_substrate({"workflow_shell": build_workflow_shell_status()})
        )
    except Exception as e:
        logger.error(f"Error reading workflow shell organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/jarvis-protocol/status", methods=["GET"])
def get_jarvis_protocol_organ_status():
    """Read-only Jarvis protocol organ snapshot (Alt-17 wave)."""
    try:
        from src.jarvis_protocol_organ import build_jarvis_protocol_status

        return jsonify(
            attach_ul_substrate({"jarvis_protocol": build_jarvis_protocol_status()})
        )
    except Exception as e:
        logger.error(f"Error reading jarvis protocol organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/reasoning-contract/status", methods=["GET"])
def get_reasoning_contract_organ_status():
    """Read-only reasoning contract organ snapshot (Alt-17 wave)."""
    try:
        from src.reasoning_contract_organ import build_reasoning_contract_status

        return jsonify(
            attach_ul_substrate(
                {"reasoning_contract": build_reasoning_contract_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading reasoning contract organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/rls/status", methods=["GET"])
def get_rls_status():
    """Read-only Reasoning & Logic Substrate posture snapshot."""
    try:
        from src.rls.status import rls_status

        return jsonify(attach_ul_substrate({"rls": rls_status()}))
    except Exception as e:
        logger.error(f"Error reading RLS status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/wonder/status", methods=["GET"])
def get_wonder_status():
    """Read-only Gate of Wonder posture snapshot."""
    try:
        from src.wonder.status import wonder_status

        return jsonify(attach_ul_substrate({"wonder": wonder_status()}))
    except Exception as e:
        logger.error(f"Error reading Wonder status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/jarvis-reasoning-lane/status", methods=["GET"])
def get_jarvis_reasoning_lane_organ_status():
    """Read-only Jarvis reasoning lane organ snapshot (Alt-17 wave)."""
    try:
        from src.jarvis_reasoning_lane_organ import build_jarvis_reasoning_lane_status

        return jsonify(
            attach_ul_substrate(
                {"jarvis_reasoning_lane": build_jarvis_reasoning_lane_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading jarvis reasoning lane organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/conversation-memory/status", methods=["GET"])
def get_conversation_memory_organ_status():
    """Read-only conversation memory organ snapshot (Alt-17 wave)."""
    try:
        from src.conversation_memory_organ import build_conversation_memory_status

        return jsonify(
            attach_ul_substrate(
                {"conversation_memory": build_conversation_memory_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading conversation memory organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/continuity-substrate/status", methods=["GET"])
def get_continuity_substrate_organ_status():
    """Read-only continuity substrate organ snapshot (Alt-17 wave)."""
    try:
        from src.continuity.organ import build_continuity_substrate_status

        return jsonify(
            attach_ul_substrate(
                {"continuity_substrate": build_continuity_substrate_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading continuity substrate organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/jarvis-operator/status", methods=["GET"])
def get_jarvis_operator_organ_status():
    """Read-only Jarvis operator organ snapshot (Alt-17 wave)."""
    try:
        from src.jarvis_operator_organ import build_jarvis_operator_status

        return jsonify(
            attach_ul_substrate({"jarvis_operator": build_jarvis_operator_status()})
        )
    except Exception as e:
        logger.error(f"Error reading jarvis operator organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/anti-drift/status", methods=["GET"])
def get_anti_drift_organ_status():
    """Read-only anti-drift organ snapshot (Alt-17 wave)."""
    try:
        from src.anti_drift_organ import build_anti_drift_status

        return jsonify(attach_ul_substrate({"anti_drift": build_anti_drift_status()}))
    except Exception as e:
        logger.error(f"Error reading anti-drift organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/prompt-assembly/status", methods=["GET"])
def get_prompt_assembly_organ_status():
    """Read-only prompt assembly organ snapshot (Alt-17 wave)."""
    try:
        from src.prompt_assembly_organ import build_prompt_assembly_status

        return jsonify(
            attach_ul_substrate({"prompt_assembly": build_prompt_assembly_status()})
        )
    except Exception as e:
        logger.error(f"Error reading prompt assembly organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/output-integrity/status", methods=["GET"])
def get_output_integrity_organ_status():
    """Read-only output integrity organ snapshot (Alt-17 wave)."""
    try:
        from src.output_integrity_organ import build_output_integrity_status

        return jsonify(
            attach_ul_substrate({"output_integrity": build_output_integrity_status()})
        )
    except Exception as e:
        logger.error(f"Error reading output integrity organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/project-infi-state-machine/status", methods=["GET"])
def get_project_infi_state_machine_organ_status():
    try:
        from src.project_infi_state_machine_organ import (
            build_project_infi_state_machine_status,
        )

        return jsonify(
            attach_ul_substrate(
                {"project_infi_state_machine": build_project_infi_state_machine_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading project infi state machine organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/project-infi-law/status", methods=["GET"])
def get_project_infi_law_organ_status():
    try:
        from src.project_infi_law_organ import build_project_infi_law_status

        return jsonify(
            attach_ul_substrate({"project_infi_law": build_project_infi_law_status()})
        )
    except Exception as e:
        logger.error(f"Error reading project infi law organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/run-ledger-binding/status", methods=["GET"])
def get_run_ledger_binding_organ_status():
    try:
        from src.run_ledger_binding_organ import build_run_ledger_binding_status

        return jsonify(
            attach_ul_substrate(
                {"run_ledger_binding": build_run_ledger_binding_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading run ledger binding organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/chat-turn-governance/status", methods=["GET"])
def get_chat_turn_governance_organ_status():
    try:
        from src.chat_turn_governance_organ import build_chat_turn_governance_status

        return jsonify(
            attach_ul_substrate(
                {"chat_turn_governance": build_chat_turn_governance_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading chat turn governance organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/aais-ul-substrate/status", methods=["GET"])
def get_aais_ul_substrate_organ_status():
    try:
        from src.aais_ul.organ import build_aais_ul_substrate_status

        return jsonify(
            attach_ul_substrate({"aais_ul_substrate": build_aais_ul_substrate_status()})
        )
    except Exception as e:
        logger.error(f"Error reading aais ul substrate organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/aris-integration/status", methods=["GET"])
def get_aris_integration_organ_status():
    try:
        from src.aris_integration_organ import build_aris_integration_status

        return jsonify(
            attach_ul_substrate({"aris_integration": build_aris_integration_status()})
        )
    except Exception as e:
        logger.error(f"Error reading aris integration organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/governance-layer/status", methods=["GET"])
def get_governance_layer_organ_status():
    try:
        from src.governance_layer_organ import build_governance_layer_status

        return jsonify(
            attach_ul_substrate({"governance_layer": build_governance_layer_status()})
        )
    except Exception as e:
        logger.error(f"Error reading governance layer organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/security-protocol/status", methods=["GET"])
def get_security_protocol_organ_status():
    try:
        from src.security_protocol_organ import build_security_protocol_status

        return jsonify(
            attach_ul_substrate({"security_protocol": build_security_protocol_status()})
        )
    except Exception as e:
        logger.error(f"Error reading security protocol organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/system-guard/status", methods=["GET"])
def get_system_guard_organ_status():
    try:
        from src.system_guard_organ import build_system_guard_status

        return jsonify(
            attach_ul_substrate({"system_guard": build_system_guard_status()})
        )
    except Exception as e:
        logger.error(f"Error reading system guard organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/launcher/status", methods=["GET"])
def get_launcher_organ_status():
    try:
        from src.launcher_organ import build_launcher_status

        return jsonify(attach_ul_substrate({"launcher": build_launcher_status()}))
    except Exception as e:
        logger.error(f"Error reading launcher organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/aais-doctor/status", methods=["GET"])
def get_aais_doctor_organ_status():
    try:
        from src.aais_doctor_organ import build_aais_doctor_status

        return jsonify(
            attach_ul_substrate({"aais_doctor": build_aais_doctor_status()})
        )
    except Exception as e:
        logger.error(f"Error reading aais doctor organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workflow-runtime/status", methods=["GET"])
def get_workflow_runtime_organ_status():
    try:
        from src.workflow_runtime_organ import build_workflow_runtime_status

        return jsonify(
            attach_ul_substrate(
                {"workflow_runtime": build_workflow_runtime_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading workflow runtime organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/jarvis-console-surface/status", methods=["GET"])
def get_jarvis_console_surface_organ_status():
    try:
        from src.jarvis_console_surface_organ import build_jarvis_console_surface_status

        return jsonify(
            attach_ul_substrate(
                {
                    "jarvis_console_surface": build_jarvis_console_surface_status()
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading jarvis console surface organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory-bank-surface/status", methods=["GET"])
def get_memory_bank_surface_organ_status():
    try:
        from src.memory_bank_surface_organ import build_memory_bank_surface_status

        return jsonify(
            attach_ul_substrate(
                {"memory_bank_surface": build_memory_bank_surface_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading memory bank surface organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/dashboard-surface/status", methods=["GET"])
def get_dashboard_surface_organ_status():
    try:
        from src.dashboard_surface_organ import build_dashboard_surface_status

        return jsonify(
            attach_ul_substrate(
                {"dashboard_surface": build_dashboard_surface_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading dashboard surface organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/nova-landing-surface/status", methods=["GET"])
def get_nova_landing_surface_organ_status():
    try:
        from src.nova_landing_surface_organ import build_nova_landing_surface_status

        return jsonify(
            attach_ul_substrate(
                {"nova_landing_surface": build_nova_landing_surface_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading nova landing surface organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/aais-composed-runtime/status", methods=["GET"])
def get_aais_composed_runtime_organ_status():
    try:
        from src.aais_composed_runtime_organ import build_aais_composed_runtime_status

        return jsonify(
            attach_ul_substrate(
                {
                    "aais_composed_runtime": build_aais_composed_runtime_status()
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading aais composed runtime organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/api-gateway/status", methods=["GET"])
def get_api_gateway_organ_status():
    try:
        from src.api_gateway_organ import build_api_gateway_status

        return jsonify(
            attach_ul_substrate({"api_gateway": build_api_gateway_status()})
        )
    except Exception as e:
        logger.error(f"Error reading api gateway organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/memory-smith/status", methods=["GET"])
def get_memory_smith_organ_status():
    try:
        from src.memory_smith_organ import build_memory_smith_status

        return jsonify(
            attach_ul_substrate({"memory_smith": build_memory_smith_status()})
        )
    except Exception as e:
        logger.error(f"Error reading memory_smith_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/operator-workspace/status", methods=["GET"])
def get_operator_workspace_organ_status():
    try:
        from src.operator_workspace_organ import build_operator_workspace_status

        return jsonify(
            attach_ul_substrate(
                {"operator_workspace": build_operator_workspace_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading operator_workspace_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/jarvis-runs/status", methods=["GET"])
def get_jarvis_runs_organ_status():
    try:
        from src.jarvis_runs_organ import build_jarvis_runs_status

        return jsonify(
            attach_ul_substrate({"jarvis_runs": build_jarvis_runs_status()})
        )
    except Exception as e:
        logger.error(f"Error reading jarvis_runs_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/state-hygiene/status", methods=["GET"])
def get_state_hygiene_organ_status():
    try:
        from src.state_hygiene_organ import build_state_hygiene_status

        return jsonify(
            attach_ul_substrate({"state_hygiene": build_state_hygiene_status()})
        )
    except Exception as e:
        logger.error(f"Error reading state_hygiene_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/blueprint-posture/status", methods=["GET"])
def get_blueprint_posture_organ_status():
    try:
        from src.blueprint_posture_organ import build_blueprint_posture_status

        return jsonify(
            attach_ul_substrate(
                {"blueprint_posture": build_blueprint_posture_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading blueprint_posture_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/workflow-interfaces/status", methods=["GET"])
def get_workflow_interfaces_organ_status():
    try:
        from src.workflow_interfaces_organ import build_workflow_interfaces_status

        return jsonify(
            attach_ul_substrate(
                {"workflow_interfaces": build_workflow_interfaces_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading workflow_interfaces_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/platform-console-interfaces/status", methods=["GET"])
def get_platform_console_interfaces_organ_status():
    try:
        from src.platform_console_interfaces_organ import (
            build_platform_console_interfaces_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "platform_console_interfaces": (
                        build_platform_console_interfaces_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading platform_console_interfaces_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/operator-console-interface/status", methods=["GET"])
def get_operator_console_interface_organ_status():
    try:
        from src.operator_console_interface_organ import (
            build_operator_console_interface_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "operator_console_interface": (
                        build_operator_console_interface_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading operator_console_interface_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/nova-workspace-interface/status", methods=["GET"])
def get_nova_workspace_interface_organ_status():
    try:
        from src.nova_workspace_interface_organ import (
            build_nova_workspace_interface_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "nova_workspace_interface": (
                        build_nova_workspace_interface_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading nova_workspace_interface_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/creative-core-runtime/status", methods=["GET"])
def get_creative_core_runtime_organ_status():
    try:
        from src.creative_core_runtime_organ import build_creative_core_runtime_status

        return jsonify(
            attach_ul_substrate(
                {"creative_core_runtime": build_creative_core_runtime_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading creative_core_runtime_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v9-core/status", methods=["GET"])
def get_v9_core_organ_status():
    try:
        from src.v9_core_organ import build_v9_core_status

        return jsonify(attach_ul_substrate({"v9_core": build_v9_core_status()}))
    except Exception as e:
        logger.error(f"Error reading v9_core_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v9-runtime/status", methods=["GET"])
def get_v9_runtime_organ_status():
    try:
        from src.v9_runtime_organ import build_v9_runtime_status

        return jsonify(attach_ul_substrate({"v9_runtime": build_v9_runtime_status()}))
    except Exception as e:
        logger.error(f"Error reading v9_runtime_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v10-core/status", methods=["GET"])
def get_v10_core_organ_status():
    try:
        from src.v10_core_organ import build_v10_core_status

        return jsonify(attach_ul_substrate({"v10_core": build_v10_core_status()}))
    except Exception as e:
        logger.error(f"Error reading v10_core_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v10-runtime/status", methods=["GET"])
def get_v10_runtime_organ_status():
    try:
        from src.v10_runtime_organ import build_v10_runtime_status

        return jsonify(
            attach_ul_substrate({"v10_runtime": build_v10_runtime_status()})
        )
    except Exception as e:
        logger.error(f"Error reading v10_runtime_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/v10-action-engine/status", methods=["GET"])
def get_v10_action_engine_organ_status():
    try:
        from src.v10_action_engine_organ import build_v10_action_engine_status

        return jsonify(
            attach_ul_substrate(
                {"v10_action_engine": build_v10_action_engine_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading v10_action_engine_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/creative-capability-bridge/status", methods=["GET"])
def get_creative_capability_bridge_organ_status():
    try:
        from src.creative_capability_bridge_organ import (
            build_creative_capability_bridge_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "creative_capability_bridge": (
                        build_creative_capability_bridge_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading creative_capability_bridge_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/creative-operator-handoff/status", methods=["GET"])
def get_creative_operator_handoff_organ_status():
    try:
        from src.creative_operator_handoff_organ import (
            build_creative_operator_handoff_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "creative_operator_handoff": (
                        build_creative_operator_handoff_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading creative_operator_handoff_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/creative-console-interface/status", methods=["GET"])
def get_creative_console_interface_organ_status():
    try:
        from src.creative_console_interface_organ import (
            build_creative_console_interface_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "creative_console_interface": (
                        build_creative_console_interface_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading creative_console_interface_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/naming-protocol/status", methods=["GET"])
def get_naming_protocol_organ_status():
    try:
        from src.naming_protocol_organ import build_naming_protocol_status

        return jsonify(
            attach_ul_substrate({"naming_protocol": build_naming_protocol_status()})
        )
    except Exception as e:
        logger.error(f"Error reading naming_protocol_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/naming-genome/status", methods=["GET"])
def get_naming_genome_organ_status():
    try:
        from src.naming_genome_organ import build_naming_genome_status

        return jsonify(
            attach_ul_substrate({"naming_genome": build_naming_genome_status()})
        )
    except Exception as e:
        logger.error(f"Error reading naming_genome_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-mutation/status", methods=["GET"])
def get_linguistic_mutation_organ_status():
    try:
        from src.linguistic_mutation_organ import build_linguistic_mutation_status

        return jsonify(
            attach_ul_substrate(
                {"linguistic_mutation": build_linguistic_mutation_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_mutation_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/mythic-engineering-translator/status", methods=["GET"])
def get_mythic_engineering_translator_organ_status():
    try:
        from src.mythic_engineering_translator_organ import (
            build_mythic_engineering_translator_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "mythic_engineering_translator": build_mythic_engineering_translator_status()
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading mythic_engineering_translator_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-drift-predictor/status", methods=["GET"])
def get_linguistic_drift_predictor_organ_status():
    try:
        from src.linguistic_drift_predictor_organ import (
            build_linguistic_drift_predictor_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_drift_predictor": build_linguistic_drift_predictor_status()
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_drift_predictor_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-lineage-viz/status", methods=["GET"])
def get_linguistic_lineage_viz_organ_status():
    try:
        from src.linguistic_lineage_viz_organ import build_linguistic_lineage_viz_status

        return jsonify(
            attach_ul_substrate(
                {"linguistic_lineage_viz": build_linguistic_lineage_viz_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_lineage_viz_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-remediation/status", methods=["GET"])
def get_linguistic_remediation_organ_status():
    try:
        from src.linguistic_remediation_organ import build_linguistic_remediation_status

        return jsonify(
            attach_ul_substrate(
                {"linguistic_remediation": build_linguistic_remediation_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_remediation_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-cascade/status", methods=["GET"])
def get_linguistic_cascade_organ_status():
    try:
        from src.linguistic_cascade_organ import build_linguistic_cascade_status

        return jsonify(
            attach_ul_substrate({"linguistic_cascade": build_linguistic_cascade_status()})
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_cascade_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/meta-linguistic-governance/status", methods=["GET"])
def get_meta_linguistic_governance_organ_status():
    try:
        from src.meta_linguistic_governance_organ import (
            build_meta_linguistic_governance_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "meta_linguistic_governance": build_meta_linguistic_governance_status()
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading meta_linguistic_governance_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-drift-forecast/status", methods=["GET"])
def get_linguistic_drift_forecast_organ_status():
    try:
        from src.linguistic_drift_forecast_organ import build_linguistic_drift_forecast_status

        return jsonify(
            attach_ul_substrate(
                {"linguistic_drift_forecast": build_linguistic_drift_forecast_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_drift_forecast_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-preemptive-remediation/status", methods=["GET"])
def get_linguistic_preemptive_remediation_organ_status():
    try:
        from src.linguistic_preemptive_remediation_organ import (
            build_linguistic_preemptive_remediation_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_preemptive_remediation": (
                        build_linguistic_preemptive_remediation_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_preemptive_remediation_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-predictive-governance/status", methods=["GET"])
def get_linguistic_predictive_governance_organ_status():
    try:
        from src.linguistic_predictive_governance_organ import (
            build_linguistic_predictive_governance_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_predictive_governance": (
                        build_linguistic_predictive_governance_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_predictive_governance_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-predictive-cycle-history/status", methods=["GET"])
def get_linguistic_predictive_cycle_history_organ_status():
    try:
        from src.linguistic_predictive_cycle_history_organ import (
            build_linguistic_predictive_cycle_history_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_predictive_cycle_history": (
                        build_linguistic_predictive_cycle_history_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_predictive_cycle_history_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-governance-cycle/status", methods=["GET"])
def get_linguistic_governance_cycle_organ_status():
    try:
        from src.linguistic_governance_cycle_organ import build_linguistic_governance_cycle_status

        return jsonify(
            attach_ul_substrate(
                {"linguistic_governance_cycle": build_linguistic_governance_cycle_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_governance_cycle_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-governance-cycle-history/status", methods=["GET"])
def get_linguistic_governance_cycle_history_organ_status():
    try:
        from src.linguistic_governance_cycle_history_organ import (
            build_linguistic_governance_cycle_history_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_governance_cycle_history": (
                        build_linguistic_governance_cycle_history_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_governance_cycle_history_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-forecast-consumption/status", methods=["GET"])
def get_linguistic_forecast_consumption_organ_status():
    try:
        from src.linguistic_forecast_consumption_organ import (
            build_linguistic_forecast_consumption_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_forecast_consumption": (
                        build_linguistic_forecast_consumption_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_forecast_consumption_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-cycle-optimization/status", methods=["GET"])
def get_linguistic_cycle_optimization_organ_status():
    try:
        from src.linguistic_cycle_optimization_organ import (
            build_linguistic_cycle_optimization_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_cycle_optimization": (
                        build_linguistic_cycle_optimization_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_cycle_optimization_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-closed-loop-fabric/status", methods=["GET"])
def get_linguistic_closed_loop_fabric_organ_status():
    try:
        from src.linguistic_closed_loop_fabric_organ import (
            build_linguistic_closed_loop_fabric_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_closed_loop_fabric": (
                        build_linguistic_closed_loop_fabric_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_closed_loop_fabric_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-forecast-calibration/status", methods=["GET"])
def get_linguistic_forecast_calibration_organ_status():
    try:
        from src.linguistic_forecast_calibration_organ import (
            build_linguistic_forecast_calibration_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_forecast_calibration": (
                        build_linguistic_forecast_calibration_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_forecast_calibration_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-governance-queue/status", methods=["GET"])
def get_linguistic_governance_queue_organ_status():
    try:
        from src.linguistic_governance_queue_organ import (
            build_linguistic_governance_queue_status,
        )

        return jsonify(
            attach_ul_substrate(
                {"linguistic_governance_queue": build_linguistic_governance_queue_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_governance_queue_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-full-governance-cycle/status", methods=["GET"])
def get_linguistic_full_governance_cycle_organ_status():
    try:
        from src.linguistic_full_governance_cycle_organ import (
            build_linguistic_full_governance_cycle_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_full_governance_cycle": (
                        build_linguistic_full_governance_cycle_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_full_governance_cycle_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-governance-attestation/status", methods=["GET"])
def get_linguistic_governance_attestation_organ_status():
    try:
        from src.linguistic_governance_attestation_organ import (
            build_linguistic_governance_attestation_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_governance_attestation": (
                        build_linguistic_governance_attestation_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_governance_attestation_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-forecast-archive/status", methods=["GET"])
def get_linguistic_forecast_archive_organ_status():
    try:
        from src.linguistic_forecast_archive_organ import (
            build_linguistic_forecast_archive_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_forecast_archive": (
                        build_linguistic_forecast_archive_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_forecast_archive_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-drift-report/status", methods=["GET"])
def get_linguistic_drift_report_organ_status():
    try:
        from src.linguistic_drift_report_organ import build_linguistic_drift_report_status

        return jsonify(
            attach_ul_substrate(
                {"linguistic_drift_report": build_linguistic_drift_report_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_drift_report_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-governance-work-order/status", methods=["GET"])
def get_linguistic_governance_work_order_organ_status():
    try:
        from src.linguistic_governance_work_order_organ import (
            build_linguistic_governance_work_order_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_governance_work_order": (
                        build_linguistic_governance_work_order_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(
            f"Error reading linguistic_governance_work_order_organ status: {e}"
        )
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-governance-cadence/status", methods=["GET"])
def get_linguistic_governance_cadence_organ_status():
    try:
        from src.linguistic_governance_cadence_organ import (
            build_linguistic_governance_cadence_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_governance_cadence": (
                        build_linguistic_governance_cadence_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_governance_cadence_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-forecast-calibration-report/status", methods=["GET"])
def get_linguistic_forecast_calibration_report_organ_status():
    try:
        from src.linguistic_forecast_calibration_report_organ import (
            build_linguistic_forecast_calibration_report_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_forecast_calibration_report": (
                        build_linguistic_forecast_calibration_report_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(
            f"Error reading linguistic_forecast_calibration_report_organ status: {e}"
        )
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-full-governance-cycle-history/status", methods=["GET"])
def get_linguistic_full_governance_cycle_history_organ_status():
    try:
        from src.linguistic_full_governance_cycle_history_organ import (
            build_linguistic_full_governance_cycle_history_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_full_governance_cycle_history": (
                        build_linguistic_full_governance_cycle_history_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(
            f"Error reading linguistic_full_governance_cycle_history_organ status: {e}"
        )
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/meta-linguistic-registry/status", methods=["GET"])
def get_meta_linguistic_registry_organ_status():
    try:
        from src.meta_linguistic_registry_organ import build_meta_linguistic_registry_status

        return jsonify(
            attach_ul_substrate(
                {"meta_linguistic_registry": build_meta_linguistic_registry_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading meta_linguistic_registry_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-subsystem-promotion/status", methods=["GET"])
def get_linguistic_subsystem_promotion_organ_status():
    try:
        from src.linguistic_subsystem_promotion_organ import (
            build_linguistic_subsystem_promotion_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_subsystem_promotion": (
                        build_linguistic_subsystem_promotion_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_subsystem_promotion_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-governed-lifecycle-fabric/status", methods=["GET"])
def get_linguistic_governed_lifecycle_fabric_organ_status():
    try:
        from src.linguistic_governed_lifecycle_fabric_organ import (
            build_linguistic_governed_lifecycle_fabric_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_governed_lifecycle_fabric": (
                        build_linguistic_governed_lifecycle_fabric_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(
            f"Error reading linguistic_governed_lifecycle_fabric_organ status: {e}"
        )
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-governance-day/status", methods=["GET"])
def get_linguistic_governance_day_organ_status():
    try:
        from src.linguistic_governance_day_organ import build_linguistic_governance_day_status

        return jsonify(
            attach_ul_substrate(
                {"linguistic_governance_day": build_linguistic_governance_day_status()}
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_governance_day_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-work-order-history/status", methods=["GET"])
def get_linguistic_work_order_history_organ_status():
    try:
        from src.linguistic_work_order_history_organ import (
            build_linguistic_work_order_history_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_work_order_history": (
                        build_linguistic_work_order_history_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_work_order_history_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/linguistic-attestation-history/status", methods=["GET"])
def get_linguistic_attestation_history_organ_status():
    try:
        from src.linguistic_attestation_history_organ import (
            build_linguistic_attestation_history_status,
        )

        return jsonify(
            attach_ul_substrate(
                {
                    "linguistic_attestation_history": (
                        build_linguistic_attestation_history_status()
                    )
                }
            )
        )
    except Exception as e:
        logger.error(f"Error reading linguistic_attestation_history_organ status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/missions/reset", methods=["POST"])
def reset_mission_board():
    """Reset Mission Board state with an optional backup and seeded current objectives."""
    try:
        data = request.get_json(silent=True) or {}
        backup_path = None
        if bool(data.get("backup", True)):
            backup_path = mission_board.backup_state()

        mission_board.reset()
        snapshot = mission_board.snapshot()
        seeded = []
        for mission in data.get("seed") or []:
            if not isinstance(mission, dict):
                continue
            snapshot = mission_board.create_mission(
                title=mission.get("title"),
                objective=mission.get("objective"),
                next_step=mission.get("next_step"),
                blocker=mission.get("blocker"),
                status=mission.get("status"),
                session_id=mission.get("session_id"),
                tags=mission.get("tags"),
                links=mission.get("links"),
                focus=bool(mission.get("focus", False)),
                cisiv_stage=mission.get("cisiv_stage"),
            )
            seeded.append(mission.get("title") or mission.get("objective") or "Untitled mission")

        return jsonify(
            {
                "mission_board": snapshot,
                "backup_path": str(backup_path) if backup_path else None,
                "seeded_missions": seeded,
            }
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error resetting Mission Board: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/missions", methods=["POST"])
def create_mission():
    """Create a new mission on the persistent Mission Board."""
    try:
        data = request.json or {}
        snapshot = mission_board.create_mission(
            title=data.get("title"),
            objective=data.get("objective"),
            next_step=data.get("next_step"),
            blocker=data.get("blocker"),
            status=data.get("status"),
            session_id=data.get("session_id"),
            tags=data.get("tags"),
            links=data.get("links"),
            focus=bool(data.get("focus", False)),
            cisiv_stage=data.get("cisiv_stage"),
        )
        return jsonify({"mission_board": snapshot}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating mission: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/missions/from-preset", methods=["POST"])
def create_mission_from_preset():
    """Create a mission from one of the built-in mission recipes."""
    try:
        data = request.json or {}
        preset_id = data.get("preset_id")
        if not preset_id:
            return jsonify({"error": "preset_id is required"}), 400
        snapshot = mission_board.create_from_preset(
            str(preset_id),
            session_id=data.get("session_id"),
            focus=bool(data.get("focus", True)),
            title=data.get("title"),
            objective=data.get("objective"),
            next_step=data.get("next_step"),
            cisiv_stage=data.get("cisiv_stage"),
        )
        return jsonify({"mission_board": snapshot}), 201
    except KeyError:
        return jsonify({"error": "Mission preset not found"}), 404
    except Exception as e:
        logger.error(f"Error creating mission from preset: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/missions/from-recipe", methods=["POST"])
def create_mission_from_recipe():
    """Create a mission from a governed Recipe Module pack (distinct from presets)."""
    try:
        data = request.json or {}
        recipe_id = data.get("recipe_id")
        if not recipe_id:
            return jsonify({"error": "recipe_id is required"}), 400
        snapshot = mission_board.create_from_recipe(
            str(recipe_id),
            session_id=data.get("session_id"),
            focus=bool(data.get("focus", True)),
            signoff_ack=bool(data.get("signoff_ack", False)),
            title=data.get("title"),
            objective=data.get("objective"),
            next_step=data.get("next_step"),
            cisiv_stage=data.get("cisiv_stage"),
        )
        return jsonify({"mission_board": snapshot}), 201
    except FileNotFoundError:
        return jsonify({"error": "Recipe pack not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating mission from recipe: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/imagine/emit", methods=["POST"])
def imagine_emit():
    """Emit a governed imagine pattern artifact."""
    try:
        from src.imagine_generator import build_pattern, build_pattern_from_fixture, persist_pattern

        data = request.json or {}
        if data.get("fixture"):
            pattern = build_pattern_from_fixture(str(data["fixture"]))
        else:
            pattern = build_pattern(
                pattern_type=str(data.get("pattern_type") or "scene_seed"),
                prompt_frame=str(data.get("prompt_frame") or ""),
                constraints=data.get("constraints"),
                mission_id=data.get("mission_id"),
                session_id=data.get("session_id"),
            )
        if pattern.get("claim_label") == "rejected":
            return jsonify({"error": "constraint_violation", "pattern": pattern}), 400
        path = persist_pattern(pattern)
        try:
            from src.alt3_lineage import record_alt3_lineage

            record_alt3_lineage(
                subsystem="imagine_generator",
                action="emit",
                mission_id=data.get("mission_id"),
                session_id=data.get("session_id"),
                payload={"pattern_id": pattern.get("pattern_id")},
            )
        except Exception:
            pass
        return jsonify({"pattern": pattern, "pattern_path": str(path)}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError:
        return jsonify({"error": "fixture not found"}), 404
    except Exception as e:
        logger.error(f"Error emitting imagine pattern: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/imagine/handoff", methods=["POST"])
def imagine_handoff():
    """Admit an imagine pattern to the Story Forge admission path."""
    try:
        from src.imagine_generator import admit_to_story_forge, load_pattern

        data = request.json or {}
        pattern_id = data.get("pattern_id")
        pattern = data.get("pattern")
        if pattern is None:
            if not pattern_id:
                return jsonify({"error": "pattern_id or pattern is required"}), 400
            pattern = load_pattern(str(pattern_id))
        result = admit_to_story_forge(pattern)
        if result.get("status") != "admitted":
            return jsonify(result), 400
        try:
            from src.alt3_lineage import record_alt3_lineage

            record_alt3_lineage(
                subsystem="imagine_generator",
                action="handoff",
                mission_id=data.get("mission_id"),
                session_id=data.get("session_id"),
                payload={"pattern_id": pattern.get("pattern_id")},
            )
        except Exception:
            pass
        return jsonify(result), 200
    except FileNotFoundError:
        return jsonify({"error": "pattern not found"}), 404
    except Exception as e:
        logger.error(f"Error in imagine handoff: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/imagine/keys-status", methods=["GET"])
def imagine_keys_status():
    """Report whether xAI API keys are configured (never exposes key material)."""
    from src.imagine_grok import keys_status

    return jsonify(keys_status())


@app.route("/api/jarvis/imagine/grok-render", methods=["POST"])
def imagine_grok_render():
    """Render an imagine pattern via xAI Grok; requires env API key."""
    try:
        from src.imagine_grok import KeysRequiredError
        from src.capabilities.imagine_generator import run_imagine_generator_capability

        data = request.json or {}
        cap = run_imagine_generator_capability(
            {
                "action": "grok_render",
                "runtime_context": "operator_runtime",
                "pattern_id": data.get("pattern_id"),
                "pattern": data.get("pattern"),
                "mission_id": data.get("mission_id"),
                "session_id": data.get("session_id"),
            }
        )
        if not cap.get("ok"):
            if cap.get("error_type") == "KeysRequired":
                return jsonify({"error": "keys_required", "message": cap.get("message")}), 428
            return jsonify({"error": cap.get("message") or "grok_render_failed"}), 400
        return jsonify(cap), 200
    except KeysRequiredError as exc:
        return jsonify({"error": "keys_required", "message": str(exc)}), 428
    except FileNotFoundError:
        return jsonify({"error": "pattern not found"}), 404
    except Exception as e:
        logger.error(f"Error in imagine grok render: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/human-voice/extract", methods=["POST"])
def human_voice_extract():
    """Extract governed voice profile constraints from human notes."""
    try:
        from src.human_voice_extraction import extract_from_fixture, extract_from_notes, persist_extraction

        data = request.json or {}
        if data.get("fixture"):
            pack = extract_from_fixture(str(data["fixture"]))
        else:
            notes = data.get("notes_text")
            if not notes:
                return jsonify({"error": "notes_text or fixture is required"}), 400
            pack = extract_from_notes(
                str(notes),
                source_kind=str(data.get("source_kind") or "human_notes"),
                mission_id=data.get("mission_id"),
            )
        path = persist_extraction(pack)
        try:
            from src.alt3_lineage import record_alt3_lineage

            record_alt3_lineage(
                subsystem="human_voice_extraction",
                action="extract",
                mission_id=data.get("mission_id"),
                session_id=data.get("session_id"),
                payload={"extraction_id": pack.get("extraction_id")},
            )
        except Exception:
            pass
        return jsonify({"extraction": pack, "path": str(path)}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError:
        return jsonify({"error": "fixture not found"}), 404
    except Exception as e:
        logger.error(f"Error in human voice extract: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/human-voice/signoff", methods=["POST"])
def human_voice_signoff():
    """Apply operator signoff to an extraction pack."""
    try:
        from src.human_voice_extraction import apply_signoff, load_extraction, persist_extraction

        data = request.json or {}
        extraction_id = data.get("extraction_id")
        pack = data.get("extraction")
        if pack is None:
            if not extraction_id:
                return jsonify({"error": "extraction_id or extraction is required"}), 400
            pack = load_extraction(str(extraction_id))
        signed = apply_signoff(pack, str(data.get("signoff_by") or "operator"))
        path = persist_extraction(signed)
        try:
            from src.alt3_lineage import record_alt3_lineage

            record_alt3_lineage(
                subsystem="human_voice_extraction",
                action="signoff",
                mission_id=data.get("mission_id"),
                session_id=data.get("session_id"),
                payload={"extraction_id": signed.get("extraction_id")},
            )
        except Exception:
            pass
        return jsonify({"extraction": signed, "path": str(path)}), 200
    except FileNotFoundError:
        return jsonify({"error": "extraction not found"}), 404
    except Exception as e:
        logger.error(f"Error in human voice signoff: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/human-voice/handoff", methods=["POST"])
def human_voice_handoff():
    """Admit voice constraints to Speakers lane."""
    try:
        from src.human_voice_extraction import admit_speakers_constraints, load_extraction

        data = request.json or {}
        extraction_id = data.get("extraction_id")
        pack = data.get("extraction")
        if pack is None:
            if not extraction_id:
                return jsonify({"error": "extraction_id or extraction is required"}), 400
            pack = load_extraction(str(extraction_id))
        result = admit_speakers_constraints(pack)
        if result.get("status") != "admitted":
            return jsonify(result), 400
        try:
            from src.alt3_lineage import record_alt3_lineage

            record_alt3_lineage(
                subsystem="human_voice_extraction",
                action="handoff",
                mission_id=data.get("mission_id"),
                session_id=data.get("session_id"),
                payload={"extraction_id": pack.get("extraction_id")},
            )
        except Exception:
            pass
        return jsonify(result), 200
    except FileNotFoundError:
        return jsonify({"error": "extraction not found"}), 404
    except Exception as e:
        logger.error(f"Error in human voice handoff: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/triangulation/correlate", methods=["POST"])
def triangulation_correlate():
    """Correlate forensic claims into triangulation.v1 for a case_id."""
    try:
        from src.capabilities.forensic_triangulation import run_forensic_triangulation_capability

        data = request.json or {}
        cap = run_forensic_triangulation_capability(
            {
                "action": "correlate",
                "runtime_context": "operator_runtime",
                **data,
            }
        )
        if not cap.get("ok"):
            status = 400 if cap.get("error_type") == "ValidationError" else 500
            return jsonify(cap), status
        return jsonify({"triangulation": cap.get("triangulation"), "case_id": cap.get("case_id")}), 201
    except Exception as e:
        logger.error(f"Error in triangulation correlate: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/narrative/pack", methods=["POST"])
def narrative_trust_pack_pack():
    """Build a governed narrative trust pack from capability output."""
    try:
        from src.capabilities.narrative_trust_pack import run_narrative_trust_pack_capability

        data = request.json or {}
        cap = run_narrative_trust_pack_capability(
            {
                "action": "pack",
                "runtime_context": "operator_runtime",
                **data,
            }
        )
        if not cap.get("ok"):
            return jsonify(cap), 400
        return jsonify({"pack": cap.get("pack")}), 201
    except Exception as e:
        logger.error(f"Error in narrative pack: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/narrative/verify", methods=["POST"])
def narrative_trust_pack_verify():
    """Verify artifact hashes in a narrative trust pack."""
    try:
        from src.capabilities.narrative_trust_pack import run_narrative_trust_pack_capability

        data = request.json or {}
        cap = run_narrative_trust_pack_capability(
            {
                "action": "verify",
                "runtime_context": "operator_runtime",
                **data,
            }
        )
        if not cap.get("ok"):
            return jsonify(cap), 400
        return jsonify(cap), 200
    except FileNotFoundError:
        return jsonify({"error": "pack not found"}), 404
    except Exception as e:
        logger.error(f"Error in narrative verify: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/narrative/signoff", methods=["POST"])
def narrative_trust_pack_signoff():
    """Apply human signoff to a verified narrative trust pack."""
    try:
        from src.capabilities.narrative_trust_pack import run_narrative_trust_pack_capability

        data = request.json or {}
        cap = run_narrative_trust_pack_capability(
            {
                "action": "signoff",
                "runtime_context": "operator_runtime",
                **data,
            }
        )
        if not cap.get("ok"):
            return jsonify(cap), 400
        return jsonify({"pack": cap.get("pack")}), 200
    except FileNotFoundError:
        return jsonify({"error": "pack not found"}), 404
    except Exception as e:
        logger.error(f"Error in narrative signoff: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/missions/<mission_id>", methods=["PATCH"])
def update_mission(mission_id):
    """Update an existing mission."""
    try:
        data = request.json or {}
        snapshot = mission_board.update_mission(
            mission_id,
            title=data.get("title"),
            objective=data.get("objective"),
            next_step=data.get("next_step"),
            blocker=data.get("blocker"),
            status=data.get("status"),
            session_id=data.get("session_id"),
            tags=data.get("tags"),
            links=data.get("links"),
            cisiv_stage=data.get("cisiv_stage"),
        )
        return jsonify({"mission_board": snapshot})
    except KeyError:
        return jsonify({"error": "Mission not found"}), 404
    except Exception as e:
        logger.error(f"Error updating mission {mission_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/missions/<mission_id>/apply-critic", methods=["POST"])
def apply_mission_critic(mission_id):
    """Apply the latest Mission Critic suggestion to one mission."""
    try:
        data = request.get_json(silent=True) or {}
        snapshot = mission_board.apply_critic_suggestion(
            mission_id,
            adopt_status=bool(data.get("adopt_status", True)),
            adopt_next_step=bool(data.get("adopt_next_step", True)),
        )
        return jsonify({"mission_board": snapshot})
    except KeyError:
        return jsonify({"error": "Mission not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error applying Mission Critic suggestion for {mission_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/missions/<mission_id>", methods=["DELETE"])
def delete_mission(mission_id):
    """Delete a mission from the board."""
    try:
        snapshot = mission_board.delete_mission(mission_id)
        return jsonify({"mission_board": snapshot})
    except KeyError:
        return jsonify({"error": "Mission not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting mission {mission_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis/missions/<mission_id>/focus", methods=["POST"])
def focus_mission(mission_id):
    """Focus the board on one mission."""
    try:
        snapshot = mission_board.focus_mission(mission_id)
        return jsonify({"mission_board": snapshot})
    except KeyError:
        return jsonify({"error": "Mission not found"}), 404
    except Exception as e:
        logger.error(f"Error focusing mission {mission_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/sessions/<session_id>/browser/verify", methods=["POST"])
def verify_browser_route(session_id):
    """Ground a rendered browser route against local code and safe next actions."""
    try:
        session = conversation_memory.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found or expired"}), 404

        data = request.json or {}
        snapshot = data.get("snapshot") or {}
        expectation = data.get("expectation")
        _set_session_persona_mode(session, data.get("persona_mode"))
        _set_session_response_mode(session, data.get("response_mode"))
        _set_session_requested_specialists(session, data.get("requested_specialists"))
        _set_session_requested_specialist_preset(session, data.get("requested_specialist_preset"))

        if not isinstance(snapshot, dict):
            return jsonify({"error": "snapshot must be an object"}), 400
        if not str(snapshot.get("url") or "").strip():
            return jsonify({"error": "snapshot.url is required"}), 400

        _transition_session_state(
            session,
            "gathering",
            summary="Jarvis is grounding a live browser route against local code.",
            reason="browser_verification",
            event_type="browser_verification_started",
            payload={
                "target_path": snapshot.get("path"),
                "capture_mode": snapshot.get("capture_mode"),
            },
        )
        verification = jarvis_operator.build_browser_verification(
            snapshot,
            expectation=expectation,
        )
        session.metadata["browser_verification"] = verification
        session.metadata["workspace_context"] = verification.get("workspace_context")
        mission_board.attach_browser_verification(session.session_id, verification)
        _attach_session_mission_context(session)
        review = mission_critic.review_browser_verification(
            verification=verification,
            mission_context=session.metadata.get("mission_board"),
        )
        _apply_mission_critic_review(session, review)
        _transition_session_state(
            session,
            "ready",
            summary="Browser verification is ready for review.",
            reason="browser_verification",
            event_type="browser_verification_completed",
            payload={
                "status": verification.get("status"),
                "target_path": verification.get("target_path"),
                "suggested_action": (verification.get("suggested_action") or {}).get("id"),
                "workspace_hits": len((verification.get("workspace_context") or {}).get("results", [])),
                "critic_status": (review or {}).get("status"),
                "critic_score": (review or {}).get("score"),
            },
        )

        return jsonify({
            "browser_verification": verification,
            **_build_chat_runtime_payload(session, session_id),
        })
    except ValueError as e:
        if "session" in locals() and session:
            _transition_session_state(
                session,
                "degraded",
                summary="Browser verification could not be grounded safely.",
                reason="browser_verification_error",
                event_type="browser_verification_error",
                payload={"error": str(e)},
            )
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        if "session" in locals() and session:
            _transition_session_state(
                session,
                "degraded",
                summary="A local action target could not be found.",
                reason="action_missing",
                event_type="action_error",
                payload={"error": str(e)},
            )
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        if "session" in locals() and session:
            _transition_session_state(
                session,
                "degraded",
                summary="Jarvis hit an error while verifying the browser route.",
                reason="browser_verification_error",
                event_type="browser_verification_error",
                payload={"error": str(e)},
            )
        logger.error(f"Error in browser route verification: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Conversation Memory / Chat
# ──────────────────────────────────────────────

def _create_chat_session_from_payload(data: dict | None):
    """Create one session from the canonical chat-session payload."""
    payload = dict(data or {})
    persona_mode = normalize_persona_mode(payload.get("persona_mode"))
    companion_profile = _get_companion_surface_profile(persona_mode=persona_mode)
    system_prompt = companion_profile["system_prompt"] if companion_profile else payload.get("system_prompt")
    session_id = conversation_memory.create_session(system_prompt=system_prompt)
    session = conversation_memory.get_session(session_id)
    if session:
        _set_session_persona_mode(session, persona_mode)
        if not companion_profile:
            session.metadata["nova_narrative_id"] = (
                str(payload.get("nova_narrative_id") or "").strip() or f"chat-{session_id}"
            )
            session.metadata["nova_intent_id"] = (
                str(payload.get("nova_intent_id") or "").strip() or session.metadata["nova_narrative_id"]
            )
        _set_session_response_mode(
            session,
            _coerce_response_mode_for_persona(persona_mode, payload.get("response_mode")),
        )
        _set_session_preferred_provider(
            session,
            payload.get("provider"),
            requested_provider_mode=payload.get("provider_mode"),
            prefer_new_session_default=bool(
                normalize_provider_mode_identifier(payload.get("provider_mode"), default="")
            ),
        )
        _set_session_requested_specialists(session, payload.get("requested_specialists"))
        _set_session_requested_specialist_preset(session, payload.get("requested_specialist_preset"))
        mechanic_case_id = str(payload.get("mechanic_case_id") or "").strip()
        if mechanic_case_id:
            session.metadata["mechanic_case_id"] = mechanic_case_id
        _transition_session_state(
            session,
            "idle",
            summary="Session created and waiting for the operator.",
            reason="session_created",
            event_type="session_created",
            payload={
                "persona_mode": session.metadata.get("persona_mode"),
                "requested_response_mode": session.metadata.get("requested_response_mode"),
                "response_mode": session.metadata.get("response_mode"),
                "preferred_provider": session.metadata.get("preferred_provider"),
                "provider_mode": session.metadata.get("provider_mode"),
                "provider_fallback": session.metadata.get("provider_fallback"),
                "requested_specialists": session.metadata.get("requested_specialists"),
                "requested_specialist_preset": session.metadata.get("requested_specialist_preset"),
            },
        )
        if companion_profile:
            from src.memory_governance_membrane import seed_session_memory_membrane

            seed_session_memory_membrane(
                session,
                jarvis_operator=jarvis_operator,
                companion_turn=True,
            )
    return session


def _infer_jarvis_compat_status(payload: dict | None, status_code: int) -> str:
    """Project one runtime payload into the UI-facing chat contract status."""
    normalized_payload = dict(payload or {})
    if status_code >= 400 or normalized_payload.get("error"):
        return "blocked"

    response_trace = dict(normalized_payload.get("response_trace") or {})
    output_completion = dict(response_trace.get("output_completion") or {})
    provider_dispatch = dict(response_trace.get("provider_dispatch") or {})

    if (
        normalized_payload.get("provider_notice")
        or output_completion.get("truncation_detected")
        or output_completion.get("repetition_detected")
        or output_completion.get("completion_guard_applied")
        or provider_dispatch.get("prompt_overflow_tokens")
    ):
        return "degraded"

    return "ok"


def _build_jarvis_compat_message_payload(data: dict | None) -> tuple[dict, dict, str]:
    """Normalize one simplified `/api/jarvis` request into the session-message payload."""
    payload = dict(data or {})
    context = dict(payload.get("context") or {})
    mode = " ".join(str(payload.get("mode") or "normal").strip().lower().split()) or "normal"
    message_payload = {
        "message": payload.get("input"),
        "persona_mode": context.get("persona_mode"),
        "provider": context.get("provider"),
        "provider_mode": context.get("provider_mode"),
        "requested_specialists": context.get("requested_specialists"),
        "requested_specialist_preset": context.get("requested_specialist_preset"),
        "_bridge_route": "api.jarvis.compat",
        "_bridge_surface": "jarvis_compat",
    }
    if mode == "think":
        message_payload["response_mode"] = "think"
    if mode == "research":
        message_payload["use_research"] = True
    if payload.get("slingshot"):
        message_payload["slingshot"] = dict(payload.get("slingshot") or {})
    if context.get("mechanic_case_id"):
        message_payload["mechanic_case_id"] = context.get("mechanic_case_id")
    return context, message_payload, mode


def _parse_json_object_body(*, require_object: bool = True) -> tuple[dict[str, Any], tuple[Any, int] | None]:
    """Parse JSON request body; return (data, None) or ({}, error_response)."""
    data = request.get_json(silent=True)
    if data is None and request.data:
        return {}, (jsonify({"error": "Request body must be valid JSON"}), 400)
    if require_object and data is not None and not isinstance(data, dict):
        return {}, (jsonify({"error": "Request body must be a JSON object"}), 400)
    return dict(data or {}), None


@app.route("/api/chat/sessions", methods=["POST"])
def create_chat_session():
    """Create a new chat session"""
    try:
        payload, error = _parse_json_object_body()
        if error is not None:
            return error
        session = _create_chat_session_from_payload(payload)
        return jsonify(
            _serialize_session_payload(session)
            if session
            else {"session_id": None, "error": "Unable to create session"}
        ), 201

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jarvis", methods=["POST"])
def jarvis_chat_compat():
    """Expose one simplified Jarvis chat endpoint on top of the session runtime."""
    try:
        request_payload, error = _parse_json_object_body()
        if error is not None:
            return error
        context, message_payload, mode = _build_jarvis_compat_message_payload(request_payload)
        session_id = str(context.get("session_id") or "").strip()

        if not message_payload.get("message"):
            payload = {
                "output": "",
                "trace": None,
                "status": "blocked",
                "session_id": session_id or None,
                "runtime": {"error": "Input is required"},
                "error": "Input is required",
            }
            return jsonify(payload), 400

        if session_id:
            session = conversation_memory.get_session(session_id)
            if not session:
                payload = {
                    "output": "",
                    "trace": None,
                    "status": "blocked",
                    "session_id": session_id,
                    "runtime": {"error": "Session not found or expired"},
                    "error": "Session not found or expired",
                }
                return jsonify(payload), 404
        else:
            session = _create_chat_session_from_payload(context)
            if not session:
                return jsonify(
                    {
                        "output": "",
                        "trace": None,
                        "status": "blocked",
                        "session_id": None,
                        "runtime": {"error": "Unable to create Jarvis session"},
                        "error": "Unable to create Jarvis session",
                    }
                ), 500
            session_id = session.session_id

        with app.test_request_context(
            f"/api/chat/sessions/{session_id}/message",
            method="POST",
            json=message_payload,
        ):
            chat_result = chat_message(session_id)
            chat_response = app.make_response(chat_result)

        runtime_payload = chat_response.get_json(silent=True) or {}
        normalized_payload = {
            "output": runtime_payload.get("response") or "",
            "trace": runtime_payload.get("response_trace"),
            "status": _infer_jarvis_compat_status(runtime_payload, chat_response.status_code),
            "session_id": session_id,
            "runtime": runtime_payload,
        }
        if runtime_payload.get("error"):
            normalized_payload["error"] = runtime_payload.get("error")
        if mode:
            normalized_payload["mode"] = mode
        return jsonify(normalized_payload), chat_response.status_code
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in jarvis_chat_compat: {e}")
        payload = {
            "output": "",
            "trace": None,
            "status": "blocked",
            "session_id": None,
            "runtime": {"error": str(e)},
            "error": str(e),
        }
        return jsonify(payload), 500


@app.route("/api/chat/sessions", methods=["GET"])
def list_chat_sessions():
    """List all active chat sessions"""
    return jsonify({"sessions": conversation_memory.list_sessions()})


@app.route("/api/chat/sessions/<session_id>", methods=["GET"])
def get_chat_session(session_id):
    """Get conversation history for a session"""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404
    return jsonify(_serialize_session_payload(session))


@app.route("/api/chat/sessions/<session_id>/events", methods=["GET"])
def list_chat_session_events(session_id):
    """List the V8-style event log for one session."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    try:
        limit = int(request.args.get("limit", 50))
    except (TypeError, ValueError):
        limit = 50

    return jsonify({
        "session_id": session_id,
        "events": _dedupe_session_events(v8_event_log.list_events(session_id, limit=limit)),
    })


@app.route("/api/chat/sessions/<session_id>/approval-audit", methods=["GET"])
def list_chat_session_approval_audit(session_id):
    """Expose the evolving approval/execution audit trail for one session."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20

    return jsonify({
        "session_id": session_id,
        "current": jarvis_operator.get_approval_state(session_id),
        "entries": jarvis_operator.list_approval_audit(session_id, limit=limit),
    })


@app.route("/api/chat/sessions/<session_id>/policy", methods=["GET"])
def get_chat_session_policy(session_id):
    """Return the latest stored policy posture for one session."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    return jsonify({
        "session_id": session_id,
        "policy_status": dict(session.metadata.get("policy_status") or default_policy_status()),
    })


@app.route("/api/chat/sessions/<session_id>", methods=["DELETE"])
def delete_chat_session(session_id):
    """Delete a chat session"""
    session = conversation_memory.get_session(session_id)
    if session:
        _transition_session_state(
            session,
            "closed",
            summary="Session was closed by the operator.",
            reason="session_deleted",
            event_type="session_deleted",
        )
    if conversation_memory.delete_session(session_id):
        return jsonify({"message": "Session deleted"})
    return jsonify({"error": "Session not found"}), 404


def _normalize_operator_source_type(value: str | None) -> str | None:
    """Normalize one operator-facing authority source identifier."""
    normalized = " ".join(str(value or "").strip().lower().split()).replace("-", "_")
    return normalized if normalized in OPERATOR_AUTHORITY_SOURCES else None


def _apply_authority_preference_payload(session, data: dict | None) -> tuple[dict, dict]:
    """Apply one authority control update to the active session."""
    payload = dict(data or {})
    preferences, _ = _ensure_authority_state(session)
    next_preferences = normalize_authority_preferences(preferences)
    preset = str(payload.get("preset") or "").strip().lower()
    action = str(payload.get("action") or "").strip().lower()

    if preset:
        if preset not in AUTHORITY_PRESETS:
            raise ValueError("Unknown authority preset.")
        preset_payload = AUTHORITY_PRESETS[preset]
        next_preferences = normalize_authority_preferences(
            {
                **default_authority_preferences(),
                "preset": preset,
                "primary_source": preset_payload.get("primary_source"),
                "shadow_sources": preset_payload.get("shadow_sources"),
                "disabled_sources": preset_payload.get("disabled_sources"),
            }
        )
        return next_preferences, {
            "preset": preset,
            "summary": f"Applied the {preset_payload['label']} authority preset.",
        }

    if action in {"", "set"}:
        action = "pin_primary"
    source_type = _normalize_operator_source_type(payload.get("source_type"))

    if action in {"pin_primary", "demote_shadow", "disable", "enable"} and not source_type:
        raise ValueError("A valid authority source is required for this action.")

    if action == "pin_primary":
        next_preferences["primary_source"] = source_type
        next_preferences["shadow_sources"] = [
            entry for entry in next_preferences["shadow_sources"] if entry != source_type
        ]
        next_preferences["disabled_sources"] = [
            entry for entry in next_preferences["disabled_sources"] if entry != source_type
        ]
        next_preferences["preset"] = "custom"
        return next_preferences, {
            "action": action,
            "source_type": source_type,
            "summary": f"Surfaced {source_type} for operator priority without changing Jarvis authority.",
        }

    if action == "demote_shadow":
        if source_type not in next_preferences["shadow_sources"]:
            next_preferences["shadow_sources"] = next_preferences["shadow_sources"] + [source_type]
        next_preferences["disabled_sources"] = [
            entry for entry in next_preferences["disabled_sources"] if entry != source_type
        ]
        if next_preferences.get("primary_source") == source_type:
            next_preferences["primary_source"] = None
        next_preferences["preset"] = "custom"
        return next_preferences, {
            "action": action,
            "source_type": source_type,
            "summary": f"Demoted {source_type} to shadow authority.",
        }

    if action == "disable":
        if source_type not in next_preferences["disabled_sources"]:
            next_preferences["disabled_sources"] = next_preferences["disabled_sources"] + [source_type]
        next_preferences["shadow_sources"] = [
            entry for entry in next_preferences["shadow_sources"] if entry != source_type
        ]
        if next_preferences.get("primary_source") == source_type:
            next_preferences["primary_source"] = None
        next_preferences["preset"] = "custom"
        return next_preferences, {
            "action": action,
            "source_type": source_type,
            "summary": f"Disabled {source_type} for the active session authority stack.",
        }

    if action == "enable":
        next_preferences["disabled_sources"] = [
            entry for entry in next_preferences["disabled_sources"] if entry != source_type
        ]
        next_preferences["shadow_sources"] = [
            entry for entry in next_preferences["shadow_sources"] if entry != source_type
        ]
        next_preferences["preset"] = "custom"
        return next_preferences, {
            "action": action,
            "source_type": source_type,
            "summary": f"Re-enabled {source_type} in the active session authority stack.",
        }

    if action == "lock_truth_scope":
        scope = normalize_truth_scope(payload.get("truth_scope"), default="live")
        turns = max(1, min(int(payload.get("turns", 3)), 12))
        next_preferences["truth_scope_lock"] = {
            "scope": scope,
            "remaining_turns": turns,
            "created_at": datetime.now(UTC).isoformat(),
        }
        next_preferences["preset"] = "custom"
        return next_preferences, {
            "action": action,
            "truth_scope": scope,
            "remaining_turns": turns,
            "summary": f"Locked truth scope to {scope} for the next {turns} turn(s).",
        }

    if action == "unlock_truth_scope":
        next_preferences["truth_scope_lock"] = None
        next_preferences["preset"] = "custom"
        return next_preferences, {
            "action": action,
            "summary": "Removed the session truth-scope lock.",
        }

    raise ValueError("Unknown authority control action.")


@app.route("/api/chat/sessions/<session_id>/state/reset", methods=["POST"])
def reset_chat_session_state(session_id):
    """Hard reset one session's volatile runtime state while preserving mission context."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    snapshot = _append_session_state_snapshot(session, reason="Pre-reset snapshot")
    system_turn_count = len([turn for turn in session.turns if turn.role == "system"])
    cleared_turns = max(0, len(session.turns) - system_turn_count)
    result = _hard_reset_session_state(session)
    result["cleared_turns"] = cleared_turns
    _record_session_event(
        session,
        "session_state_reset",
        "Operator reset the volatile session state while preserving mission context.",
        payload={"cleared_turns": cleared_turns},
    )
    return jsonify(
        {
            "result": result,
            "snapshot": snapshot,
            **_serialize_session_payload(session),
        }
    )


@app.route("/api/chat/sessions/<session_id>/state/flush-fallback", methods=["POST"])
def flush_chat_session_fallback(session_id):
    """Clear stale fallback residue from one session without touching mission context."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    result = _flush_fallback_residue(session)
    _record_session_event(
        session,
        "fallback_residue_flushed",
        "Operator cleared stale fallback residue from the session.",
        payload=result,
    )
    return jsonify({"result": result, **_serialize_session_payload(session)})


@app.route("/api/chat/sessions/<session_id>/state/freeze-mode", methods=["POST"])
def freeze_chat_session_mode(session_id):
    """Freeze one session into a specific response mode for the next N turns."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    data = request.json or {}
    mode = normalize_response_mode(data.get("mode") or session.metadata.get("response_mode"))
    turns = max(1, min(int(data.get("turns", 3)), 12))
    freeze = {
        "mode": mode,
        "remaining_turns": turns,
        "created_at": datetime.now(UTC).isoformat(),
    }
    session.metadata["mode_freeze"] = freeze
    _record_session_event(
        session,
        "mode_frozen",
        f"Operator froze the session into {mode.title()} mode for {turns} turn(s).",
        payload=freeze,
    )
    return jsonify({"mode_freeze": freeze, **_serialize_session_payload(session)})


@app.route("/api/chat/sessions/<session_id>/state/snapshot", methods=["POST"])
def snapshot_chat_session_state(session_id):
    """Capture one session-scoped operator snapshot for later comparison."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    data = request.json or {}
    snapshot = _append_session_state_snapshot(session, reason=data.get("reason"))
    _record_session_event(
        session,
        "state_snapshot_captured",
        "Operator captured a bounded session snapshot.",
        payload={"snapshot_id": snapshot["id"], "reason": snapshot["reason"]},
    )
    return jsonify({"snapshot": snapshot, **_serialize_session_payload(session)})


@app.route("/api/chat/sessions/<session_id>/state/diff", methods=["GET"])
def diff_chat_session_state(session_id):
    """Compare the current session state against one captured snapshot."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    snapshot_id = str(request.args.get("snapshot_id") or "").strip() or None
    return jsonify({"state_diff": _build_session_state_diff(session, snapshot_id=snapshot_id)})


@app.route("/api/chat/sessions/<session_id>/super-nova/status", methods=["GET"])
def get_super_nova_status(session_id):
    """Return the current operator-facing Super Nova status for one session."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404
    if not _session_uses_super_nova(session):
        return jsonify({"error": "Super Nova is not the active lane for this session."}), 409

    return jsonify(
        {
            "super_nova": _sync_super_nova_state(session),
            **_serialize_session_payload(session),
        }
    )


@app.route("/api/chat/sessions/<session_id>/super-nova/activate", methods=["POST"])
def activate_super_nova(session_id):
    """Run the explicit Super Nova activation gate for one session."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404
    if not _session_uses_super_nova(session):
        return jsonify({"error": "Super Nova is not the active lane for this session."}), 409

    activation = _activate_super_nova_session(session)
    status_code = 200 if activation["result"] == "pass" else 409
    return jsonify(
        {
            "activation": activation,
            **_serialize_session_payload(session),
        }
    ), status_code


@app.route("/api/chat/sessions/<session_id>/super-nova/pause", methods=["POST"])
def pause_super_nova(session_id):
    """Pause a live Super Nova session immediately."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404
    if not _session_uses_super_nova(session):
        return jsonify({"error": "Super Nova is not the active lane for this session."}), 409

    reason = str((request.json or {}).get("reason") or "operator_pause").strip() or "operator_pause"
    event = super_nova_scaffold.operator_pause(session_id, reason=reason)
    _sync_super_nova_state(session)
    _record_session_event(
        session,
        "super_nova_state_change",
        "Operator paused Super Nova.",
        payload={"reason": event.reason, "state": event.state, "details": list(event.details)},
    )
    return jsonify({"event": {"reason": event.reason, "state": event.state}, **_serialize_session_payload(session)})


@app.route("/api/chat/sessions/<session_id>/super-nova/resume", methods=["POST"])
def resume_super_nova(session_id):
    """Resume a paused Super Nova session when the token is still valid."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404
    if not _session_uses_super_nova(session):
        return jsonify({"error": "Super Nova is not the active lane for this session."}), 409

    reason = str((request.json or {}).get("reason") or "operator_resume").strip() or "operator_resume"
    event = super_nova_scaffold.operator_resume(session_id, reason=reason)
    _sync_super_nova_state(session)
    _record_session_event(
        session,
        "super_nova_state_change",
        "Operator resumed Super Nova.",
        payload={"reason": event.reason, "state": event.state, "details": list(event.details)},
    )
    return jsonify({"event": {"reason": event.reason, "state": event.state}, **_serialize_session_payload(session)})


@app.route("/api/chat/sessions/<session_id>/super-nova/stop", methods=["POST"])
def stop_super_nova(session_id):
    """Stop Super Nova immediately and revoke any live activation token."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404
    if not _session_uses_super_nova(session):
        return jsonify({"error": "Super Nova is not the active lane for this session."}), 409

    reason = str((request.json or {}).get("reason") or "operator_stop").strip() or "operator_stop"
    event = super_nova_scaffold.operator_stop(session_id, reason=reason)
    _sync_super_nova_state(session)
    _record_session_event(
        session,
        "super_nova_state_change",
        "Operator stopped Super Nova and revoked the live token.",
        payload={"reason": event.reason, "state": event.state, "details": list(event.details)},
    )
    return jsonify({"event": {"reason": event.reason, "state": event.state}, **_serialize_session_payload(session)})


@app.route("/api/chat/sessions/<session_id>/authority/preferences", methods=["POST"])
def update_chat_session_authority_preferences(session_id):
    """Update session-scoped knowledge authority preferences."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    try:
        next_preferences, result = _apply_authority_preference_payload(session, request.json or {})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    session.metadata["authority_preferences"] = next_preferences
    _record_session_event(
        session,
        "authority_preferences_updated",
        result["summary"],
        payload={
            "action": result.get("action") or "preset",
            "source_type": result.get("source_type"),
            "preset": result.get("preset"),
            "truth_scope": result.get("truth_scope"),
            "remaining_turns": result.get("remaining_turns"),
        },
    )
    return jsonify({"result": result, **_serialize_session_payload(session)})


@app.route("/api/chat/sessions/<session_id>/knowledge/conflicts/<conflict_id>/defer", methods=["POST"])
def defer_chat_session_knowledge_conflict(session_id, conflict_id):
    """Mark one knowledge conflict as deferred or reopen it."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    _, conflict_decisions = _ensure_authority_state(session)
    deferred = bool((request.json or {}).get("deferred", True))
    deferred_conflicts = list(conflict_decisions.get("deferred_conflicts") or [])
    if deferred and conflict_id not in deferred_conflicts:
        deferred_conflicts.append(conflict_id)
    if not deferred:
        deferred_conflicts = [item for item in deferred_conflicts if item != conflict_id]
    session.metadata["knowledge_conflict_decisions"] = normalize_knowledge_conflict_decisions(
        {"deferred_conflicts": deferred_conflicts}
    )
    _record_session_event(
        session,
        "knowledge_conflict_updated",
        f"{'Deferred' if deferred else 'Reopened'} knowledge conflict {conflict_id}.",
        payload={"conflict_id": conflict_id, "deferred": deferred},
    )
    return jsonify(
        {
            "result": {
                "conflict_id": conflict_id,
                "deferred": deferred,
            },
            **_serialize_session_payload(session),
        }
    )


@app.route("/api/chat/sessions/<session_id>/mechanic", methods=["PATCH"])
def patch_chat_session_mechanic(session_id):
    """Bind a Mechanic case id to a chat session (MECH-CHAT-01)."""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404
    payload = dict(request.json or {})
    case_id = str(payload.get("mechanic_case_id") or payload.get("case_id") or "").strip()
    if not case_id:
        session.metadata.pop("mechanic_case_id", None)
        summary = "Mechanic case binding cleared."
    else:
        session.metadata["mechanic_case_id"] = case_id
        summary = f"Mechanic case bound: {case_id}"
    _record_session_event(
        session,
        "mechanic_case_bound",
        summary,
        payload={"mechanic_case_id": case_id or None},
    )
    return jsonify({"mechanic_case_id": case_id or None, **_serialize_session_payload(session)})


@app.route("/api/slingshot/status", methods=["GET"])
def slingshot_status():
    """Return slingshot frame/packet status for a case."""
    case_id = str(request.args.get("case_id") or "").strip()
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    from slingshot.common import frame_path, packet_path
    from slingshot.frame import load_slingshot_frame
    from slingshot.packet import load_slingshot_packet

    payload: dict[str, Any] = {"case_id": case_id, "claim_label": "asserted"}
    if frame_path(case_id).is_file():
        frame = load_slingshot_frame(case_id)
        payload["frame"] = {
            "launch_blocked": frame.get("launch_blocked"),
            "drift_count": frame.get("drift_count"),
            "ma13_summary": frame.get("ma13_summary"),
        }
    else:
        payload["frame"] = None
    if packet_path(case_id).is_file():
        packet = load_slingshot_packet(case_id)
        payload["packet"] = {
            "expires_at_utc": packet.get("expires_at_utc"),
            "compose_mode": packet.get("compose_mode"),
            "authorized_goals": packet.get("authorized_goals"),
            "required_constraints": packet.get("required_constraints"),
        }
    else:
        payload["packet"] = None
    payload["artifacts_present"] = bool(payload.get("frame")) and bool(payload.get("packet"))
    return jsonify(payload)


@app.route("/api/slingshot/preload", methods=["POST"])
def slingshot_preload():
    """Run slingshot preload for a repo case (governed, no auto-apply)."""
    payload = dict(request.json or {})
    case_id = str(payload.get("case_id") or "").strip()
    repo_path = str(payload.get("repo_path") or payload.get("repo") or ".").strip() or "."
    trace_path = str(payload.get("trace_path") or "").strip()
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    from slingshot.common import frame_path, packet_path
    from slingshot.frame import build_slingshot_frame
    from slingshot.packet import build_slingshot_packet

    frame = build_slingshot_frame(
        case_id=case_id,
        repo_path=repo_path,
        trace_path=trace_path,
    )
    packet = None
    if not frame.get("launch_blocked"):
        packet = build_slingshot_packet(
            frame,
            {
                "authorized_goals": payload.get("authorized_goals") or ["analyze and propose remediation only"],
                "required_constraints": payload.get("required_constraints") or [],
            },
        )
    result = {
        "case_id": case_id,
        "launch_blocked": frame.get("launch_blocked"),
        "frame_path": str(frame_path(case_id)),
        "packet_path": str(packet_path(case_id)) if packet else None,
        "drift_count": frame.get("drift_count"),
        "claim_label": "asserted",
    }
    status_code = 200 if not frame.get("launch_blocked") else 403
    return jsonify(result), status_code


@app.route("/api/chat/sessions/<session_id>/message", methods=["POST"])
def chat_message(session_id):
    """Send a message in a chat session (with conversation memory)"""
    try:
        session = conversation_memory.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found or expired"}), 404

        data, error = _parse_json_object_body()
        if error is not None:
            return error
        _bind_mechanic_case_from_payload(session, data)
        user_message = data.get("message")
        use_research = bool(data["use_research"]) if "use_research" in data else None
        persona_mode = _set_session_persona_mode(session, data.get("persona_mode"))
        _set_session_preferred_provider(
            session,
            data.get("provider"),
            requested_provider_mode=data.get("provider_mode"),
        )
        requested_specialists = _set_session_requested_specialists(session, data.get("requested_specialists"))
        requested_specialist_preset = _set_session_requested_specialist_preset(
            session,
            data.get("requested_specialist_preset"),
        )
        requested_response_input = _coerce_response_mode_for_persona(
            persona_mode,
            data.get("response_mode"),
        )
        requested_response_mode, max_length, temperature = _resolve_generation_controls(
            requested_response_input,
            requested_length=data.get("max_length"),
            requested_temperature=data.get("temperature"),
        )
        _set_session_response_mode(session, requested_response_mode)
        companion_turn = _session_uses_companion_lane(session)
        super_nova_turn = _session_uses_super_nova(session)
        _attach_session_mission_context(session)
        if companion_turn:
            _attach_nova_invariant_consumer_snapshot(session)

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        try:
            bridge_result = _route_session_turn_to_bridge(
                session,
                user_message=user_message,
                request_payload=data,
                response_mode=requested_response_mode,
                bridge_route=str(data.get("_bridge_route") or "api.chat.sessions.message"),
                bridge_surface=str(data.get("_bridge_surface") or "jarvis_chat"),
            )
        except CognitiveBridgeValidationError as exc:
            return jsonify({"error": str(exc)}), 400
        if bridge_result.get("decision") == "BLOCK":
            return jsonify(
                {
                    "error": _bridge_block_message(
                        bridge_result,
                        "Cognitive Bridge blocked the turn before runtime execution.",
                    ),
                    "cognitive_bridge": bridge_result,
                }
            ), 403

        slingshot_block = _admit_slingshot_turn(session, data, session_id)
        if slingshot_block is not None:
            status = int(slingshot_block.get("status_code") or 403)
            return jsonify(slingshot_block), status

        mechanic_block = _maybe_block_mechanic_enforcement(session, session_id)
        if mechanic_block is not None:
            status = int(mechanic_block.get("status_code") or 403)
            return jsonify(mechanic_block), status

        _begin_turn_trace(session)
        # Add the new turn and generate from structured history.
        awaiting_approval = session.session_state.state == "awaiting_approval"
        pending_action = _load_pending_action(session) if awaiting_approval else None
        session.add_turn("user", user_message)
        approval_execution = None
        if not companion_turn:
            approval_execution = _consume_pending_action_approval(
                session,
                user_message,
                awaiting_approval=awaiting_approval,
                pending_action=pending_action,
            )
        if approval_execution:
            if approval_execution.get("blocked"):
                return jsonify({
                    "error": approval_execution["policy_status"].get("summary", "Local action blocked."),
                    **_build_chat_runtime_payload(session, session_id),
                }), 403

            action_result = approval_execution["action_result"]
            return jsonify({
                "response": action_result["response"],
                **_build_chat_runtime_payload(
                    session,
                    session_id,
                    tool_result=action_result["tool_result"],
                ),
            })
        requested_response_mode, response_mode, mode_guidance = _resolve_turn_mode_guidance(
            session,
            user_message=user_message,
            requested_mode=requested_response_mode,
            use_research=use_research,
        )
        _record_session_event(
            session,
            "user_message_received",
            "Operator request accepted for processing.",
            payload={
                "message_preview": _clip_trace_text(user_message, limit=180),
                "persona_mode": session.metadata.get("persona_mode"),
                "requested_response_mode": requested_response_mode,
                "response_mode": response_mode,
                "requested_specialists": requested_specialists,
                "requested_specialist_preset": requested_specialist_preset,
            },
        )
        _record_session_event(
            session,
            "cognitive_bridge_routed",
            summarize_bridge_result(session.metadata.get("cognitive_bridge")),
            payload=session.metadata.get("cognitive_bridge"),
        )
        if mode_guidance.get("status") != "aligned":
            _record_session_event(
                session,
                "response_mode_guided",
                mode_guidance.get("summary") or "Jarvis adjusted or recommended an operating mode.",
                payload=mode_guidance,
            )
        _evaluate_turn_policy(
            session,
            user_message=user_message,
            response_mode=response_mode,
            use_research=use_research,
        )
        _clear_turn_context(session)
        if super_nova_turn:
            allowed, blocked_payload = _require_super_nova_before_composed_turn(session)
            if not allowed:
                payload, status_code = blocked_payload
                return jsonify(payload), status_code
        _configure_speaking_runtime_turn(
            session,
            data,
            user_message,
            companion_turn=companion_turn,
        )
        _attach_pipeline_transport_substrate(session, response_mode)
        _configure_cognitive_runtime_turn(
            session,
            data,
            user_message,
            companion_turn=companion_turn,
            super_nova_turn=super_nova_turn,
        )
        composed_block = _composed_turn_block_payload(session)
        if composed_block:
            _record_session_event(
                session,
                "aais_composed_turn_blocked",
                composed_block.get("error") or "Composed turn blocked before runtime execution.",
                payload=session.metadata.get("aais_composed_turn"),
            )
            return jsonify(
                {
                    **composed_block,
                    **_build_chat_runtime_payload(session, session_id),
                }
            ), 403
        if session.metadata.get("aais_composed_turn"):
            _record_session_event(
                session,
                "aais_composed_turn_routed",
                "Turn routed through Spine, ARIS, and Nova Cortex composition.",
                payload=summarize_composed_turn(session),
            )
        tool_result = _maybe_handle_freeform_external_suggestion(
            session,
            user_message=user_message,
            request_payload=data,
        )
        if tool_result is None:
            loaded_archive = _apply_loaded_session_archive(session, data.get("loaded_session_archive"))
            if loaded_archive:
                _record_session_event(
                    session,
                    "session_archive_loaded",
                    "Jarvis attached a user-opened local session archive as document context.",
                    payload=loaded_archive,
                )
            _resolve_provider_mind(session, user_message, response_mode)
            if not companion_turn:
                tool_result = _maybe_handle_memory_rejection_followup(session, user_message)
                if tool_result is None:
                    tool_result = corrigibility_engine.handle_user_correction(session, user_message)
        if tool_result:
            direct_tool_payload = tool_result.get("tool_result") or {}
            tool_event_type = "direct_tool_selected"
            tool_event_summary = "Jarvis handled this turn through a direct operator path."
            if direct_tool_payload.get("type") == "corrigibility":
                tool_event_type = "corrigibility_command_detected"
                tool_event_summary = "Jarvis handled an explicit operator correction."
            _record_session_event(
                session,
                tool_event_type,
                tool_event_summary,
                payload={
                    "tool_type": direct_tool_payload.get("type"),
                    "action": (direct_tool_payload.get("action") or {}).get("id"),
                    "severity": direct_tool_payload.get("severity"),
                },
            )
            if (direct_tool_payload.get("action") or {}).get("id") == "corrigibility_soft_pause":
                _broadcast_system_guard_update("pause", system_guard.snapshot(limit_events=4))
        elif not companion_turn:
            tool_result = jarvis_operator.handle_command(
                user_message,
                response_mode=response_mode,
                session_id=session.session_id,
                otem_state=session.metadata.get("otem_state"),
            )

        if tool_result:
            direct_tool = tool_result["tool_result"] or {}
            _apply_direct_tool_turn_contract(session, direct_tool, response_mode)
            _snapshot_completed_turn_contract(session)
            response_text = _finalize_direct_tool_response_text(
                session,
                user_message,
                direct_tool,
                tool_result.get("response") or "",
            )
            _sync_pending_action(session, direct_tool, response_mode=response_mode)
            tool_response_mode = _resolve_direct_tool_response_mode(response_mode, direct_tool)
            specialist_preset = get_specialist_preset(session.metadata.get("requested_specialist_preset"))
            god_brain = build_god_brain_trace(
                user_message=user_message,
                response_mode=tool_response_mode,
                current_goal=session.spiral_state.current_goal,
                contract="direct_tool",
                requested_specialists=requested_specialists,
                specialist_preset=specialist_preset,
                policy_status=session.metadata.get("policy_status"),
                mode_guidance=session.metadata.get("mode_guidance"),
                tool_type=direct_tool.get("type"),
                tool_label=(direct_tool.get("action") or {}).get("label"),
            )
            session.metadata["god_brain"] = god_brain
            model_route = resolve_model_route(
                response_mode=tool_response_mode,
                specialist_preset=specialist_preset,
                god_brain=god_brain,
                policy_status=session.metadata.get("policy_status"),
                tool_type=direct_tool.get("type"),
                preferred_provider=session.metadata.get("preferred_provider"),
                provider_available=provider_registry.can_invoke,
            )
            session.metadata["model_route"] = model_route
            session.metadata["response_trace"] = _build_tool_response_trace(
                tool_response_mode,
                tool_result=direct_tool,
                god_brain=god_brain,
                model_route=model_route,
                provider_mind=session.metadata.get("provider_mind"),
                specialist_preset=specialist_preset,
                action_lifecycle=(
                    session.metadata.get("action_lifecycle")
                    if direct_tool.get("type") in {"action_request", "action_result"}
                    else None
                ),
                turn_contract=session.metadata.get("turn_contract"),
                session=session,
            )
            _record_external_suggestion_admission_trace(
                session.metadata["response_trace"],
                session.metadata.get("external_suggestion_admission"),
            )
            response_text = _finalize_otem_boundary_response(
                session,
                user_message,
                direct_tool,
                response_text,
            )
            direct_summary = "A direct Jarvis tool handled this turn without model generation."
            if direct_tool.get("type") == "corrigibility":
                direct_summary = direct_tool.get(
                    "summary",
                    "Jarvis handled an explicit operator correction without model generation.",
                )
            elif direct_tool.get("type") == "external_suggestion_guardrail":
                direct_summary = direct_tool.get(
                    "summary",
                    "Jarvis blocked raw external adoption in ordinary conversation.",
                )
            _record_session_event(
                session,
                "direct_tool_selected",
                direct_summary,
                payload={
                    "tool_type": direct_tool.get("type"),
                    "god_brain_strategy": god_brain.get("strategy_label"),
                },
            )
        else:
            _transition_session_state(
                session,
                "gathering",
                summary="Jarvis is gathering local context for this turn.",
                reason="context_gather",
                event_type="context_gather_start",
            )
            response_trace = _hydrate_jarvis_context(
                session,
                user_message,
                response_mode=response_mode,
                use_research=use_research,
                requested_specialists=requested_specialists,
                requested_specialist_preset=requested_specialist_preset,
            )
            response_trace = _apply_coherence_guard_to_response_trace(response_trace)
            if response_trace.get("blocked_by") == "coherence_fabric":
                return _coherence_block_http_response(session, session_id, response_trace)
            _record_external_suggestion_admission_trace(
                response_trace,
                session.metadata.get("external_suggestion_admission"),
            )
            _record_session_event(
                session,
                "context_gathered",
                "Jarvis gathered memory, workspace, and optional research context.",
                payload={
                    "memory_count": response_trace.get("memory_count"),
                    "memory_unique": (response_trace.get("memory_cues") or {}).get("unique"),
                    "workspace_hits": response_trace.get("workspace_hits"),
                    "research_sources": response_trace.get("research_sources"),
                    "research_reason": response_trace.get("research_reason"),
                    "model_route": (response_trace.get("model_route") or {}).get("id"),
                },
            )
            _record_session_event(
                session,
                "god_brain_aligned",
                response_trace["god_brain"]["summary"],
                payload={
                    "strategy": response_trace["god_brain"].get("strategy_label"),
                    "lead": response_trace["god_brain"].get("lead", {}).get("label"),
                    "action_bias": response_trace["god_brain"].get("action_bias"),
                    "confidence": response_trace["god_brain"].get("arbiter", {}).get("confidence"),
                },
            )

            def _generate_chat_reply():
                def _generate_once():
                    correction_prompt = corrigibility_engine.apply_to_next_generation(session)
                    if correction_prompt:
                        _append_response_trace_step(
                            response_trace,
                            "Folded the latest operator correction silently into this reply."
                        )
                        _record_session_event(
                            session,
                            "corrigibility_applied",
                            "Jarvis folded a queued correction into the next generated reply.",
                            payload={
                                "severity": (
                                    (session.metadata.get("corrigibility") or {}).get("pending") or {}
                                ).get("severity"),
                            },
                        )
                    direct_challenge_turn = _direct_challenge_turn_active(
                        session,
                        response_trace=response_trace,
                        user_message=user_message,
                    )
                    relational_turn = _relational_turn_active(
                        session,
                        response_trace=response_trace,
                        user_message=user_message,
                    )
                    if _mode_uses_plan(response_mode) and not relational_turn:
                        _transition_session_state(
                            session,
                            "planning",
                            summary=f"Jarvis is drafting a compact {response_mode} plan before answering.",
                            reason="planning",
                            event_type="planning_started",
                        )
                        plan_summary = _build_mode_plan(
                            session,
                            response_mode=response_mode,
                            model=None,
                            max_length=max_length,
                        )
                        if plan_summary:
                            response_trace["plan_summary"] = plan_summary
                            _append_response_trace_step(
                                response_trace,
                                f"Built a structured {response_mode} planning pass before the final answer."
                            )
                            _record_session_event(
                                session,
                                "planning_completed",
                                f"{response_mode.title()} mode completed its planning pass.",
                                payload={"plan_summary": plan_summary},
                            )
                    session.metadata["response_trace"] = response_trace
                    generation_package = _prepare_chat_turn_modular_generation(
                        session,
                        plan_summary=response_trace.get("plan_summary"),
                        response_trace=response_trace,
                        max_length=max_length,
                        model=ai_model,
                        temperature=temperature,
                        stream=False,
                    )
                    message_history = generation_package["local_messages"]
                    _transition_session_state(
                        session,
                        "responding",
                        summary="Jarvis is generating the final reply.",
                        reason="responding",
                        event_type="response_generation_started",
                        payload={"response_mode": response_mode},
                    )
                    routing_profile = session.metadata.get("model_route") or {}
                    response_text = None
                    generation_metadata = {"output_token_budget": int(max_length or 0)}
                    if routing_profile.get("provider") not in {None, "", "local"}:
                        try:
                            remote_response = _generate_remote_provider_reply(
                                session,
                                max_length=max_length,
                                temperature=temperature,
                                plan_summary=response_trace.get("plan_summary"),
                            )
                        except Exception as exc:
                            provider_notice = _apply_remote_provider_fallback(
                                session,
                                exc,
                                response_trace=response_trace,
                            )
                            if provider_notice is None:
                                raise
                            _record_session_event(
                                session,
                                "provider_fallback",
                                provider_notice["summary"],
                                payload=provider_notice,
                            )
                        else:
                            _append_response_trace_step(
                                response_trace,
                                f"Delegated the final answer to {routing_profile.get('provider_label', routing_profile.get('provider'))}."
                            )
                            response_text = remote_response.content
                            generation_metadata = _generation_metadata_from_provider_response(
                                remote_response,
                                output_token_budget=_effective_provider_output_budget(session, max_length),
                            )

                    if response_text is None:
                        message_history = generation_package["local_messages"]
                        model, _ = init_ai()
                        response_text = model.generate_chat(
                            message_history,
                            max_length=max_length,
                            temperature=temperature,
                            response_mode=response_mode,
                            routing_profile=session.metadata.get("model_route"),
                        )
                        generation_metadata = _generation_metadata_from_model(
                            model,
                            output_token_budget=max_length,
                        )
                    return _finalize_visible_response(
                        session,
                        user_message,
                        response_text,
                        response_trace=response_trace,
                        generation_metadata=generation_metadata,
                    )

                from src.cog_runtime.formal.generation_gate import (
                    generation_verification_enabled,
                    run_generation_with_verification,
                )

                if generation_verification_enabled(session):
                    return run_generation_with_verification(
                        session,
                        _generate_once,
                        user_message=user_message,
                    )
                return _generate_once()

            if super_nova_turn:
                response_text, blocked_payload = _run_super_nova_session(
                    session,
                    _generate_chat_reply,
                    user_message=user_message,
                )
                if blocked_payload:
                    payload, status_code = blocked_payload
                    return jsonify(payload), status_code
            else:
                response_text = _run_with_inference_lock(_generate_chat_reply)
            if not tool_result and not super_nova_turn:
                response_text, blocked_payload = finalize_chat_turn_admission(
                    session,
                    user_message=user_message,
                    response_text=response_text,
                    response_trace=session.metadata.get("response_trace"),
                )
                if blocked_payload:
                    apply_chat_turn_admission_block(session, blocked_payload)
                    return jsonify(
                        {
                            **blocked_payload,
                            **_build_chat_runtime_payload(session, session_id),
                        }
                    ), int(blocked_payload.get("status_code") or 409)
            corrigibility_engine.mark_generation_applied(session)

        review = mission_critic.review_reply(
            answer=response_text,
            user_message=user_message,
            mission_context=session.metadata.get("mission_board"),
            response_trace=session.metadata.get("response_trace"),
            tool_result=(tool_result or {}).get("tool_result"),
        )
        _apply_mission_critic_review(session, review)
        _observe_continuity_witness(session, session.metadata.get("response_trace"))
        _sanitize_session_response_trace(session)

        # Store assistant response
        session.add_turn(
            "assistant",
            response_text,
            metadata={
                "persistent_memories": list(session.metadata.get("persistent_memories", [])),
                "workspace_context": session.metadata.get("workspace_context"),
                "live_research": session.metadata.get("live_research"),
                "response_trace": session.metadata.get("response_trace"),
                "tool_result": tool_result["tool_result"] if tool_result else None,
            },
        )
        if (tool_result or {}).get("tool_result", {}).get("type") in {"action_request", "action_result"}:
            _refresh_action_lifecycle(session)
        _consume_mode_freeze(session)
        _record_session_event(
            session,
            "assistant_response_ready",
            "Jarvis finished the turn and returned a response.",
            payload={
                "tool_type": (tool_result or {}).get("tool_result", {}).get("type"),
                "contract": (session.metadata.get("response_trace") or {}).get("contract"),
            },
        )

        slingshot_block = _finalize_slingshot_turn_impact(
            session,
            user_message=user_message,
            response_text=response_text,
            session_id=session_id,
        )
        if slingshot_block is not None:
            status = int(slingshot_block.get("status_code") or 403)
            return jsonify(
                {
                    **slingshot_block,
                    **_build_chat_runtime_payload(
                        session,
                        session_id,
                        tool_result=tool_result["tool_result"] if tool_result else None,
                    ),
                }
            ), status

        return jsonify({
            "response": response_text,
            **_build_chat_runtime_payload(
                session,
                session_id,
                tool_result=tool_result["tool_result"] if tool_result else None,
            ),
        })

    except MemoryBoardEnforcerError as e:
        if "session" in locals() and session:
            _transition_session_state(
                session,
                "degraded",
                summary="Jarvis blocked the turn because memory governance is contained.",
                reason="memory_governance_blocked",
                event_type="turn_blocked",
                payload={
                    "error": str(e),
                    "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
                },
            )
            logger.warning(f"Chat turn blocked by memory governance gateway: {e}")
            return jsonify(
                _build_chat_memory_enforcer_block_payload(session, session_id, e)
            ), 403
        logger.warning(f"Chat turn blocked by memory governance gateway before session payload: {e}")
        return _build_memory_enforcer_block_response(e)
    except HTTPException:
        raise
    except Exception as e:
        if "session" in locals() and session:
            _transition_session_state(
                session,
                "degraded",
                summary="Jarvis hit an error while processing the turn.",
                reason="turn_error",
                event_type="turn_error",
                payload={"error": str(e)},
            )
        logger.error(f"Error in chat_message: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/sessions/<session_id>/stream", methods=["POST"])
def chat_message_stream(session_id):
    """Send a message in a chat session with streaming response (SSE)"""
    try:
        session = conversation_memory.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found or expired"}), 404

        data, error = _parse_json_object_body()
        if error is not None:
            return error
        _bind_mechanic_case_from_payload(session, data)
        user_message = data.get("message")
        use_research = bool(data["use_research"]) if "use_research" in data else None
        persona_mode = _set_session_persona_mode(session, data.get("persona_mode"))
        _set_session_preferred_provider(
            session,
            data.get("provider"),
            requested_provider_mode=data.get("provider_mode"),
        )
        requested_specialists = _set_session_requested_specialists(session, data.get("requested_specialists"))
        requested_specialist_preset = _set_session_requested_specialist_preset(
            session,
            data.get("requested_specialist_preset"),
        )
        requested_response_input = _coerce_response_mode_for_persona(
            persona_mode,
            data.get("response_mode"),
        )
        requested_response_mode, max_new_tokens, temperature = _resolve_generation_controls(
            requested_response_input,
            requested_length=data.get("max_new_tokens"),
            requested_temperature=data.get("temperature"),
        )
        _set_session_response_mode(session, requested_response_mode)
        companion_turn = _session_uses_companion_lane(session)
        super_nova_turn = _session_uses_super_nova(session)
        _attach_session_mission_context(session)
        if super_nova_turn:
            allowed, blocked_payload = _require_super_nova_before_composed_turn(session)
            if not allowed:
                payload, status_code = blocked_payload
                return jsonify(payload), status_code

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        try:
            bridge_result = _route_session_turn_to_bridge(
                session,
                user_message=user_message,
                request_payload=data,
                response_mode=requested_response_mode,
                bridge_route=str(data.get("_bridge_route") or "api.chat.sessions.stream"),
                bridge_surface=str(data.get("_bridge_surface") or "jarvis_chat_stream"),
            )
        except CognitiveBridgeValidationError as exc:
            return jsonify({"error": str(exc)}), 400
        if bridge_result.get("decision") == "BLOCK":
            return jsonify(
                {
                    "error": _bridge_block_message(
                        bridge_result,
                        "Cognitive Bridge blocked the turn before runtime execution.",
                    ),
                    "cognitive_bridge": bridge_result,
                }
            ), 403

        slingshot_block = _admit_slingshot_turn(session, data, session_id)
        if slingshot_block is not None:
            status = int(slingshot_block.get("status_code") or 403)
            return jsonify(slingshot_block), status

        mechanic_block = _maybe_block_mechanic_enforcement(session, session_id)
        if mechanic_block is not None:
            status = int(mechanic_block.get("status_code") or 403)
            return jsonify(mechanic_block), status

        _begin_turn_trace(session)
        awaiting_approval = session.session_state.state == "awaiting_approval"
        pending_action = _load_pending_action(session) if awaiting_approval else None
        session.add_turn("user", user_message)
        approval_execution = None
        if not companion_turn:
            approval_execution = _consume_pending_action_approval(
                session,
                user_message,
                awaiting_approval=awaiting_approval,
                pending_action=pending_action,
            )
        if approval_execution:
            if approval_execution.get("blocked"):
                return jsonify({
                    "error": approval_execution["policy_status"].get("summary", "Local action blocked."),
                    **_build_chat_runtime_payload(session, session_id),
                }), 403

            action_result = approval_execution["action_result"]

            def stream_approved_action():
                live_payload = _build_live_session_event_payload(
                    session,
                    session_id,
                    _latest_session_event(session),
                )
                if live_payload:
                    yield _format_sse_payload(live_payload)
                runtime_payload = _build_chat_runtime_payload(
                    session,
                    session_id,
                    tool_result=action_result["tool_result"],
                )
                yield _format_sse_payload({"event": "context", **runtime_payload})
                _emit_clean_console_response(action_result.get("response"))
                yield _format_sse_payload({
                    "event": "final",
                    "response": action_result["response"],
                    **runtime_payload,
                })
                yield _format_sse_payload({"event": "done"})

            return Response(
                stream_approved_action(),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "Connection": "keep-alive",
                },
            )
        requested_response_mode, response_mode, mode_guidance = _resolve_turn_mode_guidance(
            session,
            user_message=user_message,
            requested_mode=requested_response_mode,
            use_research=use_research,
        )
        user_event = _record_session_event(
            session,
            "user_message_received",
            "Operator request accepted for streaming processing.",
            payload={
                "message_preview": _clip_trace_text(user_message, limit=180),
                "persona_mode": session.metadata.get("persona_mode"),
                "requested_response_mode": requested_response_mode,
                "response_mode": response_mode,
                "requested_specialists": requested_specialists,
                "requested_specialist_preset": requested_specialist_preset,
            },
        )
        _record_session_event(
            session,
            "cognitive_bridge_routed",
            summarize_bridge_result(session.metadata.get("cognitive_bridge")),
            payload=session.metadata.get("cognitive_bridge"),
        )
        mode_event = None
        if mode_guidance.get("status") != "aligned":
            mode_event = _record_session_event(
                session,
                "response_mode_guided",
                mode_guidance.get("summary") or "Jarvis adjusted or recommended an operating mode.",
                payload=mode_guidance,
            )
        _evaluate_turn_policy(
            session,
            user_message=user_message,
            response_mode=response_mode,
            use_research=use_research,
        )
        policy_event = _latest_session_event(session)
        _clear_turn_context(session)
        _configure_speaking_runtime_turn(
            session,
            data,
            user_message,
            companion_turn=companion_turn,
        )
        _attach_pipeline_transport_substrate(session, response_mode)
        _configure_cognitive_runtime_turn(
            session,
            data,
            user_message,
            companion_turn=companion_turn,
            super_nova_turn=super_nova_turn,
        )
        composed_block = _composed_turn_block_payload(session)
        if composed_block:
            _record_session_event(
                session,
                "aais_composed_turn_blocked",
                composed_block.get("error") or "Composed turn blocked before runtime execution.",
                payload=session.metadata.get("aais_composed_turn"),
            )
            return jsonify(
                {
                    **composed_block,
                    **_build_chat_runtime_payload(session, session_id),
                }
            ), 403
        if session.metadata.get("aais_composed_turn"):
            _record_session_event(
                session,
                "aais_composed_turn_routed",
                "Turn routed through Spine, ARIS, and Nova Cortex composition.",
                payload=summarize_composed_turn(session),
            )
        tool_result = _maybe_handle_freeform_external_suggestion(
            session,
            user_message=user_message,
            request_payload=data,
        )
        archive_event = None
        if tool_result is None:
            loaded_archive = _apply_loaded_session_archive(session, data.get("loaded_session_archive"))
            if loaded_archive:
                archive_event = _record_session_event(
                    session,
                    "session_archive_loaded",
                    "Jarvis attached a user-opened local session archive as document context.",
                    payload=loaded_archive,
                )
            _resolve_provider_mind(session, user_message, response_mode)
            if not companion_turn:
                tool_result = _maybe_handle_memory_rejection_followup(session, user_message)
                if tool_result is None:
                    tool_result = corrigibility_engine.handle_user_correction(session, user_message)
        correction_event = None
        if tool_result:
            direct_tool_payload = tool_result.get("tool_result") or {}
            event_type = "direct_tool_selected"
            event_summary = "Jarvis handled this turn through a direct operator path."
            if direct_tool_payload.get("type") == "corrigibility":
                event_type = "corrigibility_command_detected"
                event_summary = "Jarvis handled an explicit operator correction."
            correction_event = _record_session_event(
                session,
                event_type,
                event_summary,
                payload={
                    "tool_type": direct_tool_payload.get("type"),
                    "action": (direct_tool_payload.get("action") or {}).get("id"),
                    "severity": direct_tool_payload.get("severity"),
                },
            )
            if (direct_tool_payload.get("action") or {}).get("id") == "corrigibility_soft_pause":
                _broadcast_system_guard_update("pause", system_guard.snapshot(limit_events=4))

        def stream_and_remember():
            full_response = ""
            prelude_events = [
                event for event in (user_event, mode_event, policy_event, archive_event, correction_event) if event
            ]

            def emit_live_event(event_record, tool_result=None):
                payload = _build_live_session_event_payload(session, session_id, event_record)
                if payload is None:
                    return None
                if tool_result is not None:
                    payload["tool_result"] = tool_result
                return _format_sse_payload(payload)

            try:
                for prelude_event in prelude_events:
                    live_payload = emit_live_event(prelude_event)
                    if live_payload:
                        yield live_payload

                active_tool_result = tool_result
                if active_tool_result is None and not companion_turn:
                    active_tool_result = jarvis_operator.handle_command(
                        user_message,
                        response_mode=response_mode,
                        session_id=session.session_id,
                        otem_state=session.metadata.get("otem_state"),
                    )

                if active_tool_result:
                    direct_tool = active_tool_result["tool_result"] or {}
                    _apply_direct_tool_turn_contract(session, direct_tool, response_mode)
                    _snapshot_completed_turn_contract(session)
                    response_text = _finalize_direct_tool_response_text(
                        session,
                        user_message,
                        direct_tool,
                        active_tool_result.get("response") or "",
                    )
                    _sync_pending_action(session, direct_tool, response_mode=response_mode)
                    tool_response_mode = _resolve_direct_tool_response_mode(response_mode, direct_tool)
                    god_brain = build_god_brain_trace(
                        user_message=user_message,
                        response_mode=tool_response_mode,
                        current_goal=session.spiral_state.current_goal,
                        contract="direct_tool",
                        requested_specialists=requested_specialists,
                        specialist_preset=get_specialist_preset(
                            session.metadata.get("requested_specialist_preset")
                        ),
                        policy_status=session.metadata.get("policy_status"),
                        mode_guidance=session.metadata.get("mode_guidance"),
                        tool_type=direct_tool.get("type"),
                        tool_label=(direct_tool.get("action") or {}).get("label"),
                    )
                    session.metadata["god_brain"] = god_brain
                    model_route = resolve_model_route(
                        response_mode=tool_response_mode,
                        specialist_preset=get_specialist_preset(
                            session.metadata.get("requested_specialist_preset")
                        ),
                        god_brain=god_brain,
                        policy_status=session.metadata.get("policy_status"),
                        tool_type=direct_tool.get("type"),
                        preferred_provider=session.metadata.get("preferred_provider"),
                        provider_available=provider_registry.can_invoke,
                    )
                    session.metadata["model_route"] = model_route
                    session.metadata["response_trace"] = _build_tool_response_trace(
                        tool_response_mode,
                        tool_result=direct_tool,
                        god_brain=god_brain,
                        model_route=model_route,
                        provider_mind=session.metadata.get("provider_mind"),
                        specialist_preset=get_specialist_preset(
                            session.metadata.get("requested_specialist_preset")
                        ),
                        action_lifecycle=(
                            session.metadata.get("action_lifecycle")
                            if direct_tool.get("type") in {"action_request", "action_result"}
                            else None
                        ),
                        turn_contract=session.metadata.get("turn_contract"),
                        session=session,
                    )
                    _record_external_suggestion_admission_trace(
                        session.metadata["response_trace"],
                        session.metadata.get("external_suggestion_admission"),
                    )
                    response_text = _finalize_otem_boundary_response(
                        session,
                        user_message,
                        direct_tool,
                        response_text,
                    )
                    direct_summary = "A direct Jarvis tool handled this streamed turn without model generation."
                    if direct_tool.get("type") == "corrigibility":
                        direct_summary = direct_tool.get(
                            "summary",
                            "Jarvis handled an explicit operator correction without model generation.",
                        )
                    elif direct_tool.get("type") == "external_suggestion_guardrail":
                        direct_summary = direct_tool.get(
                            "summary",
                            "Jarvis blocked raw external adoption in ordinary conversation.",
                        )
                    review = mission_critic.review_reply(
                        answer=response_text,
                        user_message=user_message,
                        mission_context=session.metadata.get("mission_board"),
                        response_trace=session.metadata.get("response_trace"),
                        tool_result=direct_tool,
                    )
                    _apply_mission_critic_review(session, review)
                    _observe_continuity_witness(session, session.metadata.get("response_trace"))
                    _sanitize_session_response_trace(session)
                    session.add_turn(
                        "assistant",
                        response_text,
                        metadata={
                            "persistent_memories": [],
                            "workspace_context": None,
                            "live_research": None,
                            "response_trace": session.metadata.get("response_trace"),
                            "tool_result": direct_tool,
                        },
                    )
                    if direct_tool.get("type") in {"action_request", "action_result"}:
                        _refresh_action_lifecycle(session)
                    _consume_mode_freeze(session)
                    tool_event = _record_session_event(
                        session,
                        "direct_tool_selected",
                        direct_summary,
                        payload={
                            "tool_type": direct_tool.get("type"),
                            "god_brain_strategy": god_brain.get("strategy_label"),
                        },
                    )
                    live_payload = emit_live_event(
                        tool_event,
                        tool_result=direct_tool,
                    )
                    if live_payload:
                        yield live_payload

                    runtime_payload = _build_chat_runtime_payload(
                        session,
                        session_id,
                        tool_result=direct_tool,
                    )
                    _emit_clean_console_response(response_text)
                    yield _format_sse_payload({"event": "context", **runtime_payload})
                    yield _format_sse_payload({
                        "event": "final",
                        "response": response_text,
                        **runtime_payload,
                    })
                    yield _format_sse_payload({"event": "done"})
                    return

                _transition_session_state(
                    session,
                    "gathering",
                    summary="Jarvis is gathering local context for this streamed turn.",
                    reason="context_gather",
                    event_type="context_gather_start",
                )
                live_payload = emit_live_event(_latest_session_event(session))
                if live_payload:
                    yield live_payload

                response_trace = _hydrate_jarvis_context(
                    session,
                    user_message,
                    response_mode=response_mode,
                    use_research=use_research,
                    requested_specialists=requested_specialists,
                    requested_specialist_preset=requested_specialist_preset,
                )
                response_trace = _apply_coherence_guard_to_response_trace(response_trace)
                if response_trace.get("blocked_by") == "coherence_fabric":
                    block_payload = _build_chat_coherence_block_payload(
                        session,
                        session_id,
                        response_trace,
                    )
                    _transition_session_state(
                        session,
                        "degraded",
                        summary="Jarvis blocked the streamed turn because coherence fabric is not aligned.",
                        reason="coherence_fabric_blocked",
                        event_type="turn_blocked",
                        payload={
                            "error": response_trace.get("error"),
                            "coherence_protocol": response_trace.get("coherence_protocol"),
                        },
                    )
                    session.metadata["response_trace"] = response_trace
                    live_payload = emit_live_event(_latest_session_event(session))
                    if live_payload:
                        yield live_payload
                    yield _format_sse_payload({"event": "blocked", **block_payload})
                    yield _format_sse_payload({"event": "done"})
                    return
                _record_external_suggestion_admission_trace(
                    response_trace,
                    session.metadata.get("external_suggestion_admission"),
                )
                gathered_event = _record_session_event(
                    session,
                    "context_gathered",
                    "Jarvis gathered memory, workspace, and optional research context.",
                payload={
                    "memory_count": response_trace.get("memory_count"),
                    "memory_unique": (response_trace.get("memory_cues") or {}).get("unique"),
                    "workspace_hits": response_trace.get("workspace_hits"),
                    "research_sources": response_trace.get("research_sources"),
                    "research_reason": response_trace.get("research_reason"),
                    "model_route": (response_trace.get("model_route") or {}).get("id"),
                },
                )
                live_payload = emit_live_event(gathered_event)
                if live_payload:
                    yield live_payload
                god_brain_event = _record_session_event(
                    session,
                    "god_brain_aligned",
                    response_trace["god_brain"]["summary"],
                    payload={
                        "strategy": response_trace["god_brain"].get("strategy_label"),
                        "lead": response_trace["god_brain"].get("lead", {}).get("label"),
                        "action_bias": response_trace["god_brain"].get("action_bias"),
                        "confidence": response_trace["god_brain"].get("arbiter", {}).get("confidence"),
                    },
                )
                live_payload = emit_live_event(god_brain_event)
                if live_payload:
                    yield live_payload

                direct_challenge_turn = _direct_challenge_turn_active(
                    session,
                    response_trace=response_trace,
                    user_message=user_message,
                )
                relational_turn = _relational_turn_active(
                    session,
                    response_trace=response_trace,
                    user_message=user_message,
                )

                if _mode_uses_plan(response_mode) and not relational_turn:
                    _transition_session_state(
                        session,
                        "planning",
                        summary=f"Jarvis is drafting a compact {response_mode} plan before streaming the answer.",
                        reason="planning",
                        event_type="planning_started",
                    )
                    live_payload = emit_live_event(_latest_session_event(session))
                    if live_payload:
                        yield live_payload

                    plan_summary = _build_mode_plan(
                        session,
                        response_mode=response_mode,
                        max_length=max_new_tokens,
                    )
                    if plan_summary:
                        response_trace["plan_summary"] = plan_summary
                        _append_response_trace_step(
                            response_trace,
                            f"Built a structured {response_mode} planning pass before the streamed answer."
                        )
                        planning_event = _record_session_event(
                            session,
                            "planning_completed",
                            f"{response_mode.title()} mode completed its planning pass.",
                            payload={"plan_summary": plan_summary},
                        )
                        live_payload = emit_live_event(planning_event)
                        if live_payload:
                            yield live_payload

                session.metadata["response_trace"] = response_trace
                correction_prompt = corrigibility_engine.apply_to_next_generation(session)
                if correction_prompt:
                    _append_response_trace_step(
                        response_trace,
                        "Folded the latest operator correction silently into this reply."
                    )
                    correction_applied_event = _record_session_event(
                        session,
                        "corrigibility_applied",
                        "Jarvis folded a queued correction into the next generated reply.",
                        payload={
                            "severity": (
                                (session.metadata.get("corrigibility") or {}).get("pending") or {}
                            ).get("severity"),
                        },
                    )
                    live_payload = emit_live_event(correction_applied_event)
                    if live_payload:
                        yield live_payload
                generation_package = _prepare_chat_turn_modular_generation(
                    session,
                    plan_summary=response_trace.get("plan_summary"),
                    response_trace=response_trace,
                    max_length=max_new_tokens,
                    model=ai_model,
                    temperature=temperature,
                    stream=True,
                )
                final_messages = generation_package["local_messages"]
                contextual_prompt = _messages_to_prompt(final_messages)
                yield _format_sse_payload({
                    "event": "context",
                    **_build_chat_runtime_payload(session, session_id),
                })

                if super_nova_turn:
                    def _generate_super_nova_stream_reply():
                        _transition_session_state(
                            session,
                            "responding",
                            summary="Super Nova is generating the governed reply.",
                            reason="responding",
                            event_type="response_generation_started",
                            payload={"response_mode": response_mode},
                        )
                        routing_profile = session.metadata.get("model_route") or {}
                        response_text = None
                        generation_metadata = {"output_token_budget": int(max_new_tokens or 0)}
                        if routing_profile.get("provider") not in {None, "", "local"}:
                            try:
                                remote_response = _generate_remote_provider_reply(
                                    session,
                                    max_length=max_new_tokens,
                                    temperature=temperature,
                                    plan_summary=response_trace.get("plan_summary"),
                                )
                            except Exception as exc:
                                provider_notice = _apply_remote_provider_fallback(
                                    session,
                                    exc,
                                    response_trace=response_trace,
                                )
                                if provider_notice is None:
                                    raise
                                _record_session_event(
                                    session,
                                    "provider_fallback",
                                    provider_notice["summary"],
                                    payload=provider_notice,
                                )
                            else:
                                _append_response_trace_step(
                                    response_trace,
                                    f"Delegated the final answer to {routing_profile.get('provider_label', routing_profile.get('provider'))}.",
                                )
                                response_text = remote_response.content
                                generation_metadata = _generation_metadata_from_provider_response(
                                    remote_response,
                                    output_token_budget=_effective_provider_output_budget(session, max_new_tokens),
                                )
                        if response_text is None:
                            final_messages = generation_package["local_messages"]
                            model, _ = init_ai()
                            response_text = model.generate_chat(
                                final_messages,
                                max_length=max_new_tokens,
                                temperature=temperature,
                                response_mode=response_mode,
                                routing_profile=session.metadata.get("model_route"),
                            )
                            generation_metadata = _generation_metadata_from_model(
                                model,
                                output_token_budget=max_new_tokens,
                            )
                        return _finalize_visible_response(
                            session,
                            user_message,
                            response_text,
                            response_trace=response_trace,
                            generation_metadata=generation_metadata,
                        )

                    full_response, blocked_payload = _run_super_nova_session(
                        session,
                        _generate_super_nova_stream_reply,
                        user_message=user_message,
                    )
                    if blocked_payload:
                        payload, status_code = blocked_payload
                        yield _format_sse_payload({
                            "event": "final",
                            **payload,
                        })
                        yield _format_sse_payload({"event": "done"})
                        return
                    for payload in _iter_finalized_stream_payloads(full_response):
                        yield _format_sse_payload(payload)
                    _emit_clean_console_response(full_response)
                elif direct_challenge_turn:
                    _transition_session_state(
                        session,
                        "responding",
                        summary="Jarvis is answering the direct challenge.",
                        reason="responding",
                        event_type="response_generation_started",
                        payload={"response_mode": response_mode},
                    )
                    live_payload = emit_live_event(_latest_session_event(session))
                    if live_payload:
                        yield live_payload

                    routing_profile = session.metadata.get("model_route") or {}
                    direct_response = None
                    generation_metadata = {"output_token_budget": int(max_new_tokens or 0)}
                    if routing_profile.get("provider") not in {None, "", "local"}:
                        try:
                            remote_response = _run_with_inference_lock(
                                lambda: _generate_remote_provider_reply(
                                    session,
                                    max_length=max_new_tokens,
                                    temperature=temperature,
                                    plan_summary=None,
                                )
                            )
                        except Exception as exc:
                            provider_notice = _apply_remote_provider_fallback(
                                session,
                                exc,
                                response_trace=response_trace,
                            )
                            if provider_notice is None:
                                raise
                            fallback_event = _record_session_event(
                                session,
                                "provider_fallback",
                                provider_notice["summary"],
                                payload=provider_notice,
                            )
                            live_payload = emit_live_event(fallback_event)
                            if live_payload:
                                yield live_payload
                        else:
                            _append_response_trace_step(
                                response_trace,
                                f"Delegated the direct challenge reply to {routing_profile.get('provider_label', routing_profile.get('provider'))}."
                            )
                            direct_response = remote_response.content
                            generation_metadata = _generation_metadata_from_provider_response(
                                remote_response,
                                output_token_budget=_effective_provider_output_budget(session, max_new_tokens),
                            )

                    if direct_response is None:
                        final_messages = generation_package["local_messages"]
                        with ai_inference_lock:
                            model, _ = init_ai()
                            direct_response = model.generate_chat(
                                final_messages,
                                max_length=max_new_tokens,
                                temperature=temperature,
                                response_mode=response_mode,
                                routing_profile=session.metadata.get("model_route"),
                            )
                            generation_metadata = _generation_metadata_from_model(
                                model,
                                output_token_budget=max_new_tokens,
                            )

                    full_response = _finalize_visible_response(
                        session,
                        user_message,
                        direct_response,
                        response_trace=response_trace,
                        generation_metadata=generation_metadata,
                    )
                    for payload in _iter_finalized_stream_payloads(full_response):
                        yield _format_sse_payload(payload)
                    _emit_clean_console_response(full_response)
                else:

                    routing_profile = session.metadata.get("model_route") or {}
                    if routing_profile.get("provider") not in {None, "", "local"}:
                        _transition_session_state(
                            session,
                            "responding",
                            summary="Jarvis is streaming the final reply.",
                            reason="responding",
                            event_type="response_generation_started",
                            payload={"response_mode": response_mode},
                        )
                        live_payload = emit_live_event(_latest_session_event(session))
                        if live_payload:
                            yield live_payload

                        remote_response = None
                        generation_metadata = {"output_token_budget": int(max_new_tokens or 0)}
                        try:
                            remote_response = _run_with_inference_lock(
                                lambda: _generate_remote_provider_reply(
                                    session,
                                    max_length=max_new_tokens,
                                    temperature=temperature,
                                    plan_summary=response_trace.get("plan_summary"),
                                )
                            )
                        except Exception as exc:
                            provider_notice = _apply_remote_provider_fallback(
                                session,
                                exc,
                                response_trace=response_trace,
                            )
                            if provider_notice is None:
                                raise
                            fallback_event = _record_session_event(
                                session,
                                "provider_fallback",
                                provider_notice["summary"],
                                payload=provider_notice,
                            )
                            live_payload = emit_live_event(fallback_event)
                            if live_payload:
                                yield live_payload

                            with ai_inference_lock:
                                model, streamer = init_ai()
                                if hasattr(model, "_select_text_adapter"):
                                    model._select_text_adapter(
                                        (session.metadata.get("model_route") or {}).get("adapter_mode")
                                        or response_mode
                                    )
                                contextual_prompt = _messages_to_prompt(
                                    generation_package["local_messages"]
                                )
                                stream = streamer.generate_stream(
                                    prompt=contextual_prompt,
                                    max_new_tokens=max_new_tokens,
                                    temperature=temperature,
                                    routing_profile=session.metadata.get("model_route"),
                                )
                                buffered_text = ""
                                generation_metadata = {"output_token_budget": int(max_new_tokens or 0)}
                                for chunk in stream:
                                    buffered_text = chunk.get("text_so_far", buffered_text) or buffered_text
                                    generation_metadata = _capture_stream_generation_metadata(
                                        generation_metadata,
                                        chunk,
                                    )
                                full_response = _finalize_visible_response(
                                    session,
                                    user_message,
                                    buffered_text,
                                    response_trace=response_trace,
                                    generation_metadata=generation_metadata,
                                )
                                for payload in _iter_finalized_stream_payloads(full_response):
                                    yield _format_sse_payload(payload)
                        else:
                            _append_response_trace_step(
                                response_trace,
                                f"Delegated the streamed answer to {routing_profile.get('provider_label', routing_profile.get('provider'))}."
                            )
                            generation_metadata = _generation_metadata_from_provider_response(
                                remote_response,
                                output_token_budget=_effective_provider_output_budget(session, max_new_tokens),
                            )
                            full_response = _finalize_visible_response(
                                session,
                                user_message,
                                remote_response.content,
                                response_trace=response_trace,
                                generation_metadata=generation_metadata,
                            )
                            for payload in _iter_finalized_stream_payloads(full_response):
                                yield _format_sse_payload(payload)
                        _emit_clean_console_response(full_response)
                    else:
                        with ai_inference_lock:
                            model, streamer = init_ai()
                            if hasattr(model, "_select_text_adapter"):
                                model._select_text_adapter(
                                    (session.metadata.get("model_route") or {}).get("adapter_mode")
                                    or response_mode
                                )
                            _transition_session_state(
                                session,
                                "responding",
                                summary="Jarvis is streaming the final reply.",
                                reason="responding",
                                event_type="response_generation_started",
                                payload={"response_mode": response_mode},
                            )
                            live_payload = emit_live_event(_latest_session_event(session))
                            if live_payload:
                                yield live_payload

                            stream = streamer.generate_stream(
                                prompt=contextual_prompt,
                                max_new_tokens=max_new_tokens,
                                temperature=temperature,
                                routing_profile=session.metadata.get("model_route"),
                            )
                            generation_metadata = {"output_token_budget": int(max_new_tokens or 0)}
                            buffered_text = ""
                            for chunk in stream:
                                buffered_text = chunk.get("text_so_far", buffered_text) or buffered_text
                                generation_metadata = _capture_stream_generation_metadata(
                                    generation_metadata,
                                    chunk,
                                )
                            full_response = _finalize_visible_response(
                                session,
                                user_message,
                                buffered_text,
                                response_trace=response_trace,
                                generation_metadata=generation_metadata,
                            )
                            for payload in _iter_finalized_stream_payloads(full_response):
                                yield _format_sse_payload(payload)
            except MemoryBoardEnforcerError as exc:
                _transition_session_state(
                    session,
                    "degraded",
                    summary="Jarvis blocked the streamed turn because memory governance is contained.",
                    reason="memory_governance_blocked",
                    event_type="turn_blocked",
                    payload={
                        "error": str(exc),
                        "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
                    },
                )
                live_payload = emit_live_event(_latest_session_event(session))
                if live_payload:
                    yield live_payload
                logger.warning(f"Streaming turn blocked by memory governance gateway: {exc}")
                yield _format_sse_payload(
                    {
                        "event": "blocked",
                        **_build_chat_memory_enforcer_block_payload(session, session_id, exc),
                    }
                )
                yield _format_sse_payload({"event": "done"})
                return
            except Exception as exc:
                _transition_session_state(
                    session,
                    "degraded",
                    summary="Jarvis hit an error while streaming the turn.",
                    reason="stream_error",
                    event_type="turn_error",
                    payload={"error": str(exc)},
                )
                live_payload = emit_live_event(_latest_session_event(session))
                if live_payload:
                    yield live_payload
                logger.error(f"Error during streaming generation: {exc}")
                yield _format_sse_payload({"event": "error", "error": str(exc)})
                yield _format_sse_payload({"event": "done"})
                return

            corrigibility_engine.mark_generation_applied(session)
            if not active_tool_result and not super_nova_turn:
                full_response, blocked_payload = finalize_chat_turn_admission(
                    session,
                    user_message=user_message,
                    response_text=full_response,
                    response_trace=session.metadata.get("response_trace"),
                )
                if blocked_payload:
                    apply_chat_turn_admission_block(session, blocked_payload)
                    yield _format_sse_payload(
                        {
                            "event": "final",
                            **blocked_payload,
                            **_build_chat_runtime_payload(session, session_id),
                        }
                    )
                    yield _format_sse_payload({"event": "done"})
                    return
            review = mission_critic.review_reply(
                answer=full_response,
                user_message=user_message,
                mission_context=session.metadata.get("mission_board"),
                response_trace=session.metadata.get("response_trace"),
                tool_result=None,
            )
            _apply_mission_critic_review(session, review)
            _observe_continuity_witness(session, session.metadata.get("response_trace"))
            _sanitize_session_response_trace(session)
            session.add_turn(
                "assistant",
                full_response,
                metadata={
                    "persistent_memories": list(session.metadata.get("persistent_memories", [])),
                    "workspace_context": session.metadata.get("workspace_context"),
                    "live_research": session.metadata.get("live_research"),
                    "response_trace": session.metadata.get("response_trace"),
                    "tool_result": None,
                },
            )
            _consume_mode_freeze(session)
            final_event = _record_session_event(
                session,
                "assistant_response_ready",
                "Jarvis finished streaming the turn.",
                payload={
                    "contract": (session.metadata.get("response_trace") or {}).get("contract"),
                },
            )
            live_payload = emit_live_event(final_event)
            if live_payload:
                yield live_payload
            slingshot_block = _finalize_slingshot_turn_impact(
                session,
                user_message=user_message,
                response_text=full_response,
                session_id=session_id,
            )
            runtime_payload = _build_chat_runtime_payload(session, session_id)
            if slingshot_block is not None:
                yield _format_sse_payload({
                    "event": "final",
                    "error": slingshot_block.get("error"),
                    "slingshot": slingshot_block.get("slingshot"),
                    **runtime_payload,
                })
                yield _format_sse_payload({"event": "done"})
                return
            yield _format_sse_payload({
                "event": "final",
                "response": full_response,
                **runtime_payload,
            })
            yield _format_sse_payload({"event": "done"})

        return Response(
            stream_and_remember(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    except MemoryBoardEnforcerError as e:
        if "session" in locals() and session:
            _transition_session_state(
                session,
                "degraded",
                summary="Jarvis blocked the streamed turn before it could start because memory governance is contained.",
                reason="memory_governance_blocked",
                event_type="turn_blocked",
                payload={
                    "error": str(e),
                    "memory_enforcer": jarvis_operator.memory_enforcer.last_audit(),
                },
            )
            logger.warning(f"Streaming route blocked by memory governance gateway: {e}")
            return jsonify(
                _build_chat_memory_enforcer_block_payload(session, session_id, e)
            ), 403
        logger.warning(f"Streaming route blocked by memory governance gateway before session payload: {e}")
        return _build_memory_enforcer_block_response(e)
    except HTTPException:
        raise
    except Exception as e:
        if "session" in locals() and session:
            _transition_session_state(
                session,
                "degraded",
                summary="Jarvis hit an error before the streamed turn could finish.",
                reason="stream_route_error",
                event_type="turn_error",
                payload={"error": str(e)},
            )
        logger.error(f"Error in chat_message_stream: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/sessions/<session_id>/actions/execute", methods=["POST"])
def execute_safe_local_action(session_id):
    """Run a safe local action after the operator explicitly approves it."""
    try:
        session = conversation_memory.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found or expired"}), 404

        data = request.json or {}
        action_id = data.get("action_id")
        review_id = str(data.get("review_id") or "").strip()
        approved = bool(data.get("approved"))
        external_suggestion_details = _extract_external_suggestion_details(data)
        _set_session_persona_mode(session, data.get("persona_mode"))
        _set_session_preferred_provider(
            session,
            data.get("provider"),
            requested_provider_mode=data.get("provider_mode"),
        )
        _set_session_response_mode(session, data.get("response_mode"))
        _set_session_requested_specialists(session, data.get("requested_specialists"))
        _set_session_requested_specialist_preset(session, data.get("requested_specialist_preset"))

        if not action_id:
            return jsonify({"error": "action_id is required"}), 400
        action = jarvis_operator.resolve_action(action_id, review_id=review_id)
        if external_suggestion_details:
            action = {
                **dict(action or {}),
                **external_suggestion_details,
            }
        if action.get("blocked"):
            _store_pending_action(session, None)
            _set_action_lifecycle(
                session,
                stage="blocked",
                action=action,
                approval_state="awaiting" if not approved else "approved",
                execution_state="blocked",
                source="actions_execute_endpoint",
                response_mode="operator",
                error=action.get("blocked_reason") or "Local action blocked.",
            )
            _transition_session_state(
                session,
                "degraded",
                summary="A local action was blocked before execution.",
                reason="action_blocked",
                event_type="action_blocked",
                payload={"action_id": action_id, "blocked_reason": action.get("blocked_reason")},
            )
            _refresh_action_lifecycle(session)
            session.metadata["response_trace"] = _build_tool_response_trace(
                "operator",
                tool_result={"type": "action_request", "action": action},
                action_lifecycle=session.metadata.get("action_lifecycle"),
                session=session,
                runtime_context="operator_runtime",
            )
            return jsonify({
                "error": action.get("blocked_reason") or "Local action blocked.",
                "action": action,
            }), 403

        action, policy_status = _evaluate_action_policy(
            session,
            action_id,
            approved=approved,
            action=action,
        )
        if not approved:
            _store_pending_action(session, action)
            _set_action_lifecycle(
                session,
                stage="proposed",
                action=action,
                approval_state="awaiting",
                execution_state="pending",
                source="actions_execute_endpoint",
                response_mode="operator",
            )
            _transition_session_state(
                session,
                "awaiting_approval",
                summary="Jarvis is waiting for explicit approval before running a local action.",
                reason="awaiting_approval",
                event_type="action_waiting_for_approval",
                payload={"action_id": action_id, "policy_status": policy_status},
            )
            _refresh_action_lifecycle(session)
            session.metadata["response_trace"] = _build_tool_response_trace(
                "operator",
                tool_result={"type": "action_request", "action": action},
                action_lifecycle=session.metadata.get("action_lifecycle"),
                session=session,
                runtime_context="operator_runtime",
            )
            return jsonify({
                "error": "Explicit approval is required before running local actions.",
                "policy_status": policy_status,
            }), 400
        if not policy_status.get("allowed", True):
            _store_pending_action(session, None)
            _set_action_lifecycle(
                session,
                stage="blocked",
                action=action,
                approval_state="approved" if approved else "awaiting",
                execution_state="blocked",
                source="actions_execute_endpoint",
                response_mode="operator",
                error=policy_status.get("summary", "Local action blocked."),
            )
            _transition_session_state(
                session,
                "degraded",
                summary="A local action was blocked by the policy guardrails.",
                reason="action_blocked",
                event_type="action_blocked",
                payload={"action_id": action_id, "policy_status": policy_status},
            )
            _refresh_action_lifecycle(session)
            session.metadata["response_trace"] = _build_tool_response_trace(
                "operator",
                tool_result={"type": "action_request", "action": action},
                action_lifecycle=session.metadata.get("action_lifecycle"),
                session=session,
                runtime_context="operator_runtime",
            )
            return jsonify({
                "error": policy_status.get("summary", "Local action blocked."),
                "policy_status": policy_status,
            }), 403

        action_result = _execute_approved_local_action(
            session,
            action_id,
            action=action,
            approval_source="actions_execute_endpoint",
        )
        if str((action_result.get("tool_result") or {}).get("status") or "").strip().lower() == "blocked":
            return jsonify(
                {
                    "error": (action_result.get("tool_result") or {}).get("summary")
                    or "Local action blocked.",
                    "response": action_result["response"],
                    **_build_chat_runtime_payload(
                        session,
                        session_id,
                        tool_result=action_result["tool_result"],
                    ),
                }
            ), 403

        return jsonify({
            "response": action_result["response"],
            **_build_chat_runtime_payload(
                session,
                session_id,
                tool_result=action_result["tool_result"],
            ),
        })
    except ValueError as e:
        if "session" in locals() and session:
            _transition_session_state(
                session,
                "degraded",
                summary="A local action request could not be executed safely.",
                reason="action_error",
                event_type="action_error",
                payload={"error": str(e)},
            )
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        if "session" in locals() and session:
            _transition_session_state(
                session,
                "degraded",
                summary="Jarvis hit an error while running a local action.",
                reason="action_error",
                event_type="action_error",
                payload={"error": str(e)},
            )
        logger.error(f"Error executing safe local action: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Document / RAG
# ──────────────────────────────────────────────


def _resolve_document_upload_metadata(
    document_module,
    *,
    metadata=None,
    operator_context=None,
    explicit_role=None,
):
    """Normalize optional operator hints into traceable document metadata."""
    allowed_roles = {"source_of_truth", "input_artifact", "context"}
    normalized = dict(metadata or {}) if isinstance(metadata, dict) else {}
    context_text = " ".join(str(operator_context or "").split()).strip()
    role = " ".join(str(explicit_role or normalized.get("document_role") or "").split()).strip().lower()
    if role not in allowed_roles:
        role = ""

    if not role and context_text:
        role = document_module.infer_document_role(context_text)

    if context_text:
        normalized["operator_context"] = context_text
    normalized["document_role"] = role or "context"
    return normalized


@app.route("/api/documents", methods=["GET"])
def list_documents():
    """List all ingested documents"""
    document_module = _load_module("src.document_rag")
    document_store = document_module.document_store
    return jsonify({"documents": document_store.list_documents()})


@app.route("/api/documents/upload/text", methods=["POST"])
def upload_text_document():
    """Ingest a plain text document"""
    try:
        data = request.json or {}
        text = data.get("text")
        doc_id = data.get("doc_id")

        if not text:
            return jsonify({"error": "Text content is required"}), 400

        document_module = _load_module("src.document_rag")
        document_store = document_module.document_store
        metadata = _resolve_document_upload_metadata(
            document_module,
            metadata=data.get("metadata"),
            operator_context=data.get("operator_context"),
            explicit_role=data.get("role"),
        )
        result_id = document_store.ingest_text(text, doc_id=doc_id, metadata=metadata)
        return jsonify({
            "doc_id": result_id,
            "message": "Document ingested",
            "document_role": metadata.get("document_role", "context"),
        }), 201

    except Exception as e:
        logger.error(f"Error ingesting text: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/upload/pdf", methods=["POST"])
def upload_pdf_document():
    """Ingest a PDF document"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "PDF file is required"}), 400

        pdf_file = request.files["file"]
        doc_id = request.form.get("doc_id")
        raw_metadata = request.form.get("metadata")
        parsed_metadata = {}
        if raw_metadata:
            try:
                parsed_metadata = json.loads(raw_metadata)
            except (TypeError, ValueError):
                return jsonify({"error": "metadata must be valid JSON"}), 400
        document_module = _load_module("src.document_rag")
        metadata = _resolve_document_upload_metadata(
            document_module,
            metadata=parsed_metadata,
            operator_context=request.form.get("operator_context"),
            explicit_role=request.form.get("role"),
        )

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_file.save(tmp)
            tmp_path = tmp.name

        document_store = document_module.document_store
        try:
            result_id = document_store.ingest_pdf(tmp_path, doc_id=doc_id, metadata=metadata)
            return jsonify({
                "doc_id": result_id,
                "message": "PDF ingested",
                "document_role": metadata.get("document_role", "context"),
            }), 201
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error ingesting PDF: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/upload/url", methods=["POST"])
def upload_url_document():
    """Ingest a document from a URL"""
    try:
        data = request.json or {}
        url = data.get("url")
        doc_id = data.get("doc_id")

        if not url:
            return jsonify({"error": "URL is required"}), 400

        document_module = _load_module("src.document_rag")
        document_store = document_module.document_store
        metadata = _resolve_document_upload_metadata(
            document_module,
            metadata=data.get("metadata"),
            operator_context=data.get("operator_context"),
            explicit_role=data.get("role"),
        )
        result_id = document_store.ingest_url(url, doc_id=doc_id, metadata=metadata)
        return jsonify({
            "doc_id": result_id,
            "message": "URL content ingested",
            "document_role": metadata.get("document_role", "context"),
        }), 201

    except Exception as e:
        logger.error(f"Error ingesting URL: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Delete an ingested document"""
    document_module = _load_module("src.document_rag")
    document_store = document_module.document_store
    if document_store.delete_document(doc_id):
        return jsonify({"message": "Document deleted"})
    return jsonify({"error": "Document not found"}), 404


@app.route("/api/documents/search", methods=["POST"])
def search_documents():
    """Search across ingested documents"""
    try:
        data = request.json or {}
        query = data.get("query")
        top_k = data.get("top_k", 5)
        doc_id = data.get("doc_id")

        if not query:
            return jsonify({"error": "Query is required"}), 400

        document_module = _load_module("src.document_rag")
        document_store = document_module.document_store
        results = document_store.search(query, top_k=top_k, doc_id=doc_id)
        return jsonify({"results": results})

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/ask", methods=["POST"])
def ask_documents():
    """Ask a question grounded in ingested documents (RAG)"""
    try:
        data = request.json or {}
        query = data.get("query")
        top_k = data.get("top_k", 5)
        doc_id = data.get("doc_id")
        max_length = _coerce_max_length(data.get("max_length"))

        if not query:
            return jsonify({"error": "Query is required"}), 400

        document_module = _load_module("src.document_rag")
        document_store = document_module.document_store
        build_rag_prompt = document_module.build_rag_prompt

        # Retrieve relevant chunks
        context_chunks = document_store.search(query, top_k=top_k, doc_id=doc_id)

        if not context_chunks:
            return jsonify({
                "answer": "No relevant documents found. Please ingest documents first.",
                "sources": [],
            })

        # Build RAG prompt and generate answer
        rag_prompt = build_rag_prompt(query, context_chunks)
        answer = _run_with_inference_lock(
            lambda: init_ai()[0].generate_text(rag_prompt, max_length=max_length, temperature=0.3)
        )

        return jsonify({
            "answer": answer,
            "sources": [
                {"doc_id": c["doc_id"], "score": c["score"], "excerpt": c["chunk"][:200]}
                for c in context_chunks
            ],
        })

    except Exception as e:
        logger.error(f"Error in ask_documents: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Speech-to-Text (Whisper)
# ──────────────────────────────────────────────

@app.route("/api/audio/transcribe", methods=["POST"])
def transcribe_audio():
    """Transcribe audio file to text"""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "Audio file is required"}), 400

        speech_module = _load_module("src.speech")
        speech_to_text = speech_module.speech_to_text
        audio_file = request.files["audio"]
        language = request.form.get("language")

        # Determine file extension
        filename = audio_file.filename or "audio.wav"
        suffix = os.path.splitext(filename)[1] or ".wav"

        audio_bytes = audio_file.read()
        result = speech_to_text.transcribe_bytes(
            audio_bytes, suffix=suffix, language=language
        )
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in transcribe_audio: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/audio/voice-query", methods=["POST"])
def voice_query():
    """Transcribe audio and use it as a text prompt for AI generation"""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "Audio file is required"}), 400

        speech_module = _load_module("src.speech")
        speech_to_text = speech_module.speech_to_text
        audio_file = request.files["audio"]
        filename = audio_file.filename or "audio.wav"
        suffix = os.path.splitext(filename)[1] or ".wav"
        language = request.form.get("language")
        max_length = _coerce_max_length(request.form.get("max_length"))

        # Transcribe
        audio_bytes = audio_file.read()
        transcription = speech_to_text.transcribe_bytes(
            audio_bytes, suffix=suffix, language=language
        )

        # Generate response from transcribed text
        response_text = _run_with_inference_lock(
            lambda: init_ai()[0].generate_text(
                transcription["text"],
                max_length=max_length,
            )
        )

        return jsonify({
            "transcription": transcription["text"],
            "response": response_text,
            "language": transcription["language"],
        })

    except Exception as e:
        logger.error(f"Error in voice_query: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Text-to-Speech
# ──────────────────────────────────────────────

@app.route("/api/audio/synthesize", methods=["POST"])
def synthesize_speech():
    """Convert text to speech audio (returns WAV)"""
    try:
        data = request.json or {}
        text = data.get("text")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        speech_module = _load_module("src.speech")
        text_to_speech = speech_module.text_to_speech
        wav_bytes = text_to_speech.synthesize_to_wav_bytes(text)
        wav_base64 = base64.b64encode(wav_bytes).decode()

        return jsonify({
            "audio": wav_base64,
            "format": "wav",
            "encoding": "base64",
        })

    except Exception as e:
        logger.error(f"Error in synthesize_speech: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/audio/synthesize/download", methods=["POST"])
def synthesize_speech_download():
    """Convert text to speech and return WAV file directly"""
    try:
        data = request.json or {}
        text = data.get("text")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        speech_module = _load_module("src.speech")
        text_to_speech = speech_module.text_to_speech
        wav_bytes = text_to_speech.synthesize_to_wav_bytes(text)

        return Response(
            wav_bytes,
            mimetype="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"},
        )

    except Exception as e:
        logger.error(f"Error in synthesize_speech_download: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Sentiment Analysis & Text Classification
# ──────────────────────────────────────────────

@app.route("/api/text/sentiment", methods=["POST"])
def analyze_sentiment():
    """Analyze sentiment of text"""
    try:
        data = request.json or {}
        text = data.get("text")
        texts = data.get("texts")  # For batch
        classifier_module = _load_module("src.text_classifier")
        text_classifier = classifier_module.text_classifier

        if texts:
            results = text_classifier.analyze_sentiment_batch(texts)
            return jsonify({"results": results})
        elif text:
            result = text_classifier.analyze_sentiment(text)
            return jsonify(result)
        else:
            return jsonify({"error": "'text' or 'texts' is required"}), 400

    except Exception as e:
        logger.error(f"Error in analyze_sentiment: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/text/classify", methods=["POST"])
def classify_text():
    """Classify text into custom categories (zero-shot)"""
    try:
        data = request.json or {}
        text = data.get("text")
        texts = data.get("texts")  # For batch
        labels = data.get("labels") or data.get("candidate_labels")
        multi_label = data.get("multi_label", False)
        classifier_module = _load_module("src.text_classifier")
        text_classifier = classifier_module.text_classifier

        if not labels:
            return jsonify({"error": "'labels' list is required"}), 400

        if texts:
            results = text_classifier.classify_batch(texts, labels, multi_label=multi_label)
            return jsonify({"results": results})
        elif text:
            result = text_classifier.classify(text, labels, multi_label=multi_label)
            return jsonify(result)
        else:
            return jsonify({"error": "'text' or 'texts' is required"}), 400

    except Exception as e:
        logger.error(f"Error in classify_text: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/audio/extract-features", methods=["POST"])
def extract_audio_features():
    """Extract lightweight audio features for the web UI."""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "Audio file is required"}), 400

        audio_module = _load_module("src.audio_processor")
        audio_processor = audio_module.AudioProcessor
        audio_file = request.files["audio"]
        filename = audio_file.filename or "audio.wav"
        suffix = os.path.splitext(filename)[1] or ".wav"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            audio_file.save(tmp)
            tmp_path = tmp.name

        try:
            features = audio_processor.extract_features(tmp_path)
            return jsonify(features)
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error in extract_audio_features: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/audio/detect-silence", methods=["POST"])
def detect_audio_silence():
    """Detect silent regions in an uploaded audio file."""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "Audio file is required"}), 400

        audio_module = _load_module("src.audio_processor")
        audio_processor = audio_module.AudioProcessor
        audio_file = request.files["audio"]
        filename = audio_file.filename or "audio.wav"
        suffix = os.path.splitext(filename)[1] or ".wav"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            audio_file.save(tmp)
            tmp_path = tmp.name

        try:
            silent_segments = audio_processor.detect_silence(tmp_path)
            return jsonify({"silent_segments": silent_segments})
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error in detect_audio_silence: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/batch/text-generate", methods=["POST"])
def batch_generate_text():
    """Generate text for multiple prompts in one request."""
    try:
        data = request.json or {}
        prompts = data.get("prompts") or []
        max_length = _coerce_max_length(data.get("max_length"))
        temperature = _coerce_temperature(data.get("temperature"))

        cleaned_prompts = [prompt.strip() for prompt in prompts if isinstance(prompt, str) and prompt.strip()]
        if not cleaned_prompts:
            return jsonify({"error": "At least one prompt is required"}), 400

        def _run_batch():
            model, _ = init_ai()
            return [
                {
                    "prompt": prompt,
                    "generated_text": model.generate_text(
                        prompt,
                        max_length=max_length,
                        temperature=temperature,
                    ),
                }
                for prompt in cleaned_prompts
            ]

        results = _run_with_inference_lock(_run_batch)

        return jsonify({"results": results, "count": len(results)})

    except Exception as e:
        logger.error(f"Error in batch_generate_text: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Video Processing
# ──────────────────────────────────────────────

@app.route("/api/video/info", methods=["POST"])
def video_info():
    """Get video metadata"""
    try:
        if "video" not in request.files:
            return jsonify({"error": "Video file is required"}), 400

        video_module = _load_module("src.video_processor")
        video_processor = video_module.video_processor
        video_file = request.files["video"]
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            video_file.save(tmp)
            tmp_path = tmp.name

        try:
            info = video_processor.get_video_info(tmp_path)
            return jsonify(info)
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error in video_info: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/video/extract-frames", methods=["POST"])
def extract_video_frames():
    """Extract frames from a video"""
    try:
        if "video" not in request.files:
            return jsonify({"error": "Video file is required"}), 400

        video_module = _load_module("src.video_processor")
        video_processor = video_module.video_processor
        video_file = request.files["video"]
        num_frames = int(request.form.get("num_frames", 10))

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            video_file.save(tmp)
            tmp_path = tmp.name

        try:
            frames = video_processor.extract_frames(tmp_path, num_frames=num_frames)

            # Convert frame images to base64
            frame_results = []
            for frame in frames:
                with open(frame["path"], "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                frame_results.append({
                    "timestamp": frame["timestamp"],
                    "frame_index": frame["frame_index"],
                    "image": img_b64,
                    "format": "jpg",
                })

            return jsonify({"frames": frame_results, "count": len(frame_results)})
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error in extract_video_frames: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/video/analyze", methods=["POST"])
def analyze_video():
    """Analyze video: extract key frames, analyze each, and generate summary"""
    try:
        if "video" not in request.files:
            return jsonify({"error": "Video file is required"}), 400

        video_module = _load_module("src.video_processor")
        video_processor = video_module.video_processor
        video_file = request.files["video"]
        num_frames = int(request.form.get("num_frames", 8))

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            video_file.save(tmp)
            tmp_path = tmp.name

        try:
            info = video_processor.get_video_info(tmp_path)
            frames = video_processor.extract_frames(tmp_path, num_frames=num_frames)
            def _analyze_video_with_model():
                model, _ = init_ai()
                analyzed_frames = video_processor.analyze_frames(frames, model)
                return analyzed_frames, video_processor.generate_summary(analyzed_frames, model)

            analyzed, summary = _run_with_inference_lock(_analyze_video_with_model)

            return jsonify({
                "video_info": info,
                "summary": summary,
                "frames_analyzed": len(analyzed),
            })
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error in analyze_video: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Error Handlers
# ──────────────────────────────────────────────

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


def run_api(host="0.0.0.0", port=5000, debug=False):
    """Run the Flask API"""
    logger.info(f"Starting API server on {host}:{port}")
    should_run_startup_bootstrap = not debug or os.getenv("WERKZEUG_RUN_MAIN") == "true"
    if should_run_startup_bootstrap:
        try:
            from src.governance_organs import Alt4Runtime

            Alt4Runtime.boot_validate()
        except Exception as exc:
            if os.getenv("AAIS_GENOME_BOOT", "fail").strip().lower() not in {
                "warn",
                "warning",
                "skip",
            }:
                raise
            logger.warning("Alt-4 genome boot validation (run_api): %s", exc)
        bootstrap_ai_runtime(reason="run_api")
    should_boot_dreamspace = os.getenv("AAIS_ENABLE_DREAMSPACE", "0").strip().lower() in {"1", "true", "yes", "on"}
    if should_boot_dreamspace and should_run_startup_bootstrap:
        dreamspace.start(reason="Dreamspace auto-started from AAIS runtime configuration.")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_api(debug=config.DEBUG)
