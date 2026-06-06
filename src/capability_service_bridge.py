"""Governed service-lane bridge for AAIS capability modules."""

# Mythic: Capability service bridge
# Engineering: CapabilityServiceBridge
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from src.datetime_compat import UTC

from src.capability_module import AAISCapabilityModule
from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    Phase,
    PhaseGateError,
    PhaseViolationError,
    assert_executable,
    assert_routable,
    get_component,
    is_executable,
    is_routable,
    list_phase_events,
    register_component,
)


BRIDGE_ID = "aais.capability_service_bridge"
BRIDGE_VERSION = "0.2"
BRIDGE_COMPONENT_ID = "jarvis.capability_service_bridge"
MAX_AUDIT_EVENTS = 50
DEFAULT_GOVERNANCE_MODES = ("strict", "assist", "experimental")
DEFAULT_PHASE_CONTEXT = "live_runtime"
OPERATOR_PHASE_CONTEXT = "operator_runtime"
DEFAULT_PHASE_ALLOWED_CONTEXTS = (DEFAULT_PHASE_CONTEXT, OPERATOR_PHASE_CONTEXT)
DEFAULT_SERVICE_PATH = [
    "selection",
    "capability_registry",
    "capability_service_bridge",
    "module.execute",
    "tool_result",
    "response_trace",
]


def _normalize_name(value: str | None) -> str:
    return " ".join(str(value or "").replace("-", "_").split()).strip().lower()


def _clean_text(value: Any, default: str) -> str:
    text = " ".join(str(value or "").split()).strip()
    return text or default


def _normalize_characters(value: Any) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [part.strip() for part in value.replace("\n", ",").split(",")]
    else:
        items = [value]
    return [text for text in (" ".join(str(item or "").split()).strip() for item in items) if text]


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    normalized = _normalize_name(value)
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    return None


def _normalize_runtime_context(value: Any, default: str = DEFAULT_PHASE_CONTEXT) -> str:
    normalized = _normalize_name(value)
    return normalized or default


class ConfiguredCapabilityModule(AAISCapabilityModule):
    """Small configurable wrapper around the governed capability base class."""

    def __init__(
        self,
        *,
        module_name: str,
        provider_name: str,
        supported_actions: set[str] | frozenset[str],
        required_fields_by_action: dict[str, tuple[str, ...]] | None = None,
        handlers: dict[str, Callable[[dict[str, Any]], Any]] | None = None,
    ):
        super().__init__(provider_name=provider_name, handlers=handlers)
        self.module_name = module_name
        self.supported_actions = frozenset(supported_actions)
        self.required_fields_by_action = dict(required_fields_by_action or {})


class CapabilityServiceBridge:
    """Route governed service-lane tool intents through AAIS capability modules."""

    def __init__(
        self,
        *,
        spatial_query: Callable[..., dict[str, Any]],
        render_spatial: Callable[[dict[str, Any], dict[str, Any]], str],
        mystic_read: Callable[[str], dict[str, Any]],
        render_mystic: Callable[[dict[str, Any]], str],
        v9_run: Callable[..., dict[str, Any]],
        render_v9: Callable[[dict[str, Any]], str],
        v10_run: Callable[..., dict[str, Any]],
        render_v10: Callable[[dict[str, Any]], str],
    ):
        self._spatial_query = spatial_query
        self._render_spatial = render_spatial
        self._mystic_read = mystic_read
        self._render_mystic = render_mystic
        self._v9_run = v9_run
        self._render_v9 = render_v9
        self._v10_run = v10_run
        self._render_v10 = render_v10
        self._event_counter = 0
        self._events: list[dict[str, Any]] = []

        self._spatial_module = ConfiguredCapabilityModule(
            module_name="spatial",
            provider_name="local_spatial_engine",
            supported_actions={"query"},
            handlers={"query": self._execute_spatial},
        )
        self._mystic_module = ConfiguredCapabilityModule(
            module_name="mystic",
            provider_name="local_mystic_engine",
            supported_actions={"read"},
            required_fields_by_action={"read": ("state", "next_action")},
            handlers={"read": self._execute_mystic},
        )
        self._v9_module = ConfiguredCapabilityModule(
            module_name="v9_core",
            provider_name="v9_runtime",
            supported_actions={"generate_scene"},
            required_fields_by_action={"generate_scene": ("status", "location")},
            handlers={"generate_scene": self._execute_v9},
        )
        self._v10_module = ConfiguredCapabilityModule(
            module_name="v10_core",
            provider_name="v10_runtime",
            supported_actions={"generate_scene"},
            required_fields_by_action={"generate_scene": ("status", "location")},
            handlers={"generate_scene": self._execute_v10},
        )
        self._recipe_module = ConfiguredCapabilityModule(
            module_name="recipe_module",
            provider_name="aais_recipe",
            supported_actions={"create_mission"},
        )
        self._imagine_module = ConfiguredCapabilityModule(
            module_name="imagine_generator",
            provider_name="aais_imagine",
            supported_actions={"emit", "handoff", "grok_render"},
        )
        self._human_voice_module = ConfiguredCapabilityModule(
            module_name="human_voice_extraction",
            provider_name="aais_human_voice",
            supported_actions={"extract", "signoff", "handoff"},
        )
        self._forensic_triangulation_module = ConfiguredCapabilityModule(
            module_name="forensic_triangulation",
            provider_name="aais_triangulation",
            supported_actions={"correlate"},
        )
        self._narrative_trust_pack_module = ConfiguredCapabilityModule(
            module_name="narrative_trust_pack",
            provider_name="aais_narrative",
            supported_actions={"pack", "verify", "signoff"},
        )
        self._story_forge_launcher_module = ConfiguredCapabilityModule(
            module_name="story_forge_launcher",
            provider_name="aais_story_forge",
            supported_actions={"intake"},
        )
        self._movie_renderer_lane_module = ConfiguredCapabilityModule(
            module_name="movie_renderer_lane",
            provider_name="aais_story_forge",
            supported_actions={"propose_render"},
        )
        self._text_game_to_video_module = ConfiguredCapabilityModule(
            module_name="text_game_to_video",
            provider_name="aais_story_forge",
            supported_actions={"propose_render_plan"},
        )
        self._game_front_door_module = ConfiguredCapabilityModule(
            module_name="game_front_door",
            provider_name="aais_story_forge",
            supported_actions={"admit_session"},
        )
        self._text_to_3d_world_lane_module = ConfiguredCapabilityModule(
            module_name="text_to_3d_world_lane",
            provider_name="aais_story_forge",
            supported_actions={"world_lane_route"},
        )
        self._world_pack_lane_module = ConfiguredCapabilityModule(
            module_name="world_pack_lane",
            provider_name="aais_story_forge",
            supported_actions={"inspect_manifest"},
        )

        self._route_specs = [
            {
                "capability_id": "spatial",
                "capability_label": "Spatial",
                "capability_summary": "Run governed line-of-sight, path, distance, and spatial-state checks.",
                "tool": "spatial_reason",
                "tool_label": "Spatial Reason",
                "action": "reason",
                "action_label": "Reason",
                "module": self._spatial_module,
                "aliases": ("spatial_reason",),
                "handler": self._handle_spatial_reason,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "mode",
                        "label": "Reasoning Mode",
                        "type": "select",
                        "required": True,
                        "default": "visibility",
                        "options": [
                            {"value": "visibility", "label": "Visibility"},
                            {"value": "distance", "label": "Distance"},
                            {"value": "path", "label": "Path"},
                        ],
                    },
                    {
                        "id": "space_id",
                        "label": "Space Id",
                        "type": "text",
                        "required": True,
                        "default": "operator_grid",
                        "placeholder": "operator_grid",
                    },
                    {
                        "id": "from",
                        "label": "From",
                        "type": "text",
                        "required": False,
                        "placeholder": "origin node",
                    },
                    {
                        "id": "to",
                        "label": "To",
                        "type": "text",
                        "required": False,
                        "placeholder": "target node",
                    },
                    {
                        "id": "line_of_sight",
                        "label": "Line Of Sight",
                        "type": "boolean",
                        "required": False,
                        "default": True,
                    },
                ),
            },
            {
                "capability_id": "mystic",
                "capability_label": "Mystic",
                "capability_summary": "Run the deterministic mystic engine for symbolic state reading and next-step guidance.",
                "tool": "mystic_reading",
                "tool_label": "Mystic Reading",
                "action": "reading",
                "action_label": "Reading",
                "module": self._mystic_module,
                "aliases": ("mystic", "mythic", "mystic_reading", "mythic_reading"),
                "handler": self._handle_mystic_reading,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "input",
                        "label": "Reading Prompt",
                        "type": "textarea",
                        "required": True,
                        "default": "my current state and the next move I need to make",
                        "placeholder": "I feel stuck and need direction.",
                    },
                ),
            },
            {
                "capability_id": "v9_core",
                "capability_label": "V9 Core",
                "capability_summary": "Run the governed V9 narrative core for direct scene continuation.",
                "tool": "v9_core",
                "tool_label": "V9 Core",
                "action": "generate_scene",
                "action_label": "Generate Scene",
                "module": self._v9_module,
                "aliases": ("v9", "v9_core", "divine_core", "god_engine"),
                "handler": self._handle_v9_core,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("llm",),
                "default_provider_mode": "llm",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "input",
                        "label": "Scene Prompt",
                        "type": "textarea",
                        "required": True,
                        "default": "continue the scene through the V9 Core",
                        "placeholder": "Continue the scene after the betrayal.",
                    },
                    {
                        "id": "context",
                        "label": "Context",
                        "type": "textarea",
                        "required": False,
                        "placeholder": "The queen has just found the hidden letter.",
                    },
                    {
                        "id": "location",
                        "label": "Location",
                        "type": "text",
                        "required": False,
                        "default": "Unknown",
                        "placeholder": "Throne Room",
                    },
                    {
                        "id": "characters",
                        "label": "Characters",
                        "type": "text",
                        "required": False,
                        "placeholder": "Queen Seris, Captain Vale",
                    },
                ),
            },
            {
                "capability_id": "v10_core",
                "capability_label": "V10 Core",
                "capability_summary": "Run the governed V10 scene stack with critic scoring and readiness feedback.",
                "tool": "v10_core",
                "tool_label": "V10 Core",
                "action": "generate_scene",
                "action_label": "Generate Scene",
                "module": self._v10_module,
                "aliases": ("v10", "v10_core", "core_v10"),
                "handler": self._handle_v10_core,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("llm",),
                "default_provider_mode": "llm",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "input",
                        "label": "Scene Prompt",
                        "type": "textarea",
                        "required": True,
                        "default": "continue the next scene beat and score whether the draft is strong enough to keep",
                        "placeholder": "Continue the scene after the betrayal.",
                    },
                    {
                        "id": "context",
                        "label": "Context",
                        "type": "textarea",
                        "required": False,
                        "placeholder": "The queen has just found the hidden letter.",
                    },
                    {
                        "id": "location",
                        "label": "Location",
                        "type": "text",
                        "required": False,
                        "default": "Unknown",
                        "placeholder": "Throne Room",
                    },
                    {
                        "id": "characters",
                        "label": "Characters",
                        "type": "text",
                        "required": False,
                        "placeholder": "Queen Seris, Captain Vale",
                    },
                ),
            },
            {
                "capability_id": "recipe_module",
                "capability_label": "Recipe Module",
                "capability_summary": "Create a Mission Board mission from a governed recipe pack.",
                "tool": "recipe_module",
                "tool_label": "Recipe Module",
                "action": "create_mission",
                "action_label": "Create Mission",
                "module": self._recipe_module,
                "aliases": ("recipe_module", "recipe_create_mission"),
                "handler": self._handle_recipe_module_create_mission,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "recipe_id",
                        "label": "Recipe Id",
                        "type": "text",
                        "required": True,
                        "default": "onboarding-v1",
                    },
                    {
                        "id": "signoff_ack",
                        "label": "Human Signoff Ack",
                        "type": "boolean",
                        "required": True,
                        "default": True,
                    },
                ),
            },
            {
                "capability_id": "imagine_generator",
                "capability_label": "Imagine Generator",
                "capability_summary": "Emit a governed imagination pattern artifact.",
                "tool": "imagine_generator_emit",
                "tool_label": "Imagine Emit",
                "action": "emit",
                "action_label": "Emit Pattern",
                "module": self._imagine_module,
                "aliases": ("imagine_emit", "imagine_generator_emit"),
                "handler": self._handle_imagine_emit,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "fixture",
                        "label": "Fixture",
                        "type": "text",
                        "required": False,
                        "default": "scene-seed-demo",
                    },
                    {
                        "id": "prompt_frame",
                        "label": "Prompt Frame",
                        "type": "textarea",
                        "required": False,
                    },
                    {
                        "id": "pattern_type",
                        "label": "Pattern Type",
                        "type": "text",
                        "required": False,
                        "default": "scene_seed",
                    },
                ),
            },
            {
                "capability_id": "imagine_generator",
                "capability_label": "Imagine Generator",
                "capability_summary": "Admit an imagine pattern to the Story Forge handoff path.",
                "tool": "imagine_generator_handoff",
                "tool_label": "Imagine Handoff",
                "action": "handoff",
                "action_label": "Story Forge Handoff",
                "module": self._imagine_module,
                "aliases": ("imagine_handoff", "imagine_generator_handoff"),
                "handler": self._handle_imagine_handoff,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "pattern_id",
                        "label": "Pattern Id",
                        "type": "text",
                        "required": True,
                    },
                ),
            },
            {
                "capability_id": "imagine_generator",
                "capability_label": "Imagine Generator",
                "capability_summary": "Render pattern via xAI Grok (requires env API key).",
                "tool": "imagine_generator_grok_render",
                "tool_label": "Imagine Grok Render",
                "action": "grok_render",
                "action_label": "Grok Render",
                "module": self._imagine_module,
                "aliases": ("imagine_grok_render", "imagine_generator_grok"),
                "handler": self._handle_imagine_grok_render,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "pattern_id",
                        "label": "Pattern Id",
                        "type": "text",
                        "required": True,
                    },
                ),
            },
            {
                "capability_id": "human_voice_extraction",
                "capability_label": "Human Voice Extraction",
                "capability_summary": "Extract governed voice traits from human notes.",
                "tool": "human_voice_extract",
                "tool_label": "Extract Voice",
                "action": "extract",
                "action_label": "Extract",
                "module": self._human_voice_module,
                "aliases": ("human_voice_extract", "human_voice_extraction"),
                "handler": self._handle_human_voice_extract,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "fixture",
                        "label": "Fixture",
                        "type": "text",
                        "required": False,
                        "default": "notes-demo-redacted",
                    },
                    {
                        "id": "notes_text",
                        "label": "Notes Text",
                        "type": "textarea",
                        "required": False,
                    },
                ),
            },
            {
                "capability_id": "human_voice_extraction",
                "capability_label": "Human Voice Extraction",
                "capability_summary": "Apply operator signoff to a voice extraction pack.",
                "tool": "human_voice_signoff",
                "tool_label": "Voice Signoff",
                "action": "signoff",
                "action_label": "Signoff",
                "module": self._human_voice_module,
                "aliases": ("human_voice_signoff",),
                "handler": self._handle_human_voice_signoff,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "extraction_id",
                        "label": "Extraction Id",
                        "type": "text",
                        "required": True,
                    },
                    {
                        "id": "signoff_by",
                        "label": "Signoff By",
                        "type": "text",
                        "required": False,
                        "default": "operator",
                    },
                ),
            },
            {
                "capability_id": "human_voice_extraction",
                "capability_label": "Human Voice Extraction",
                "capability_summary": "Admit voice constraints to the Speakers lane.",
                "tool": "human_voice_handoff",
                "tool_label": "Speakers Handoff",
                "action": "handoff",
                "action_label": "Handoff",
                "module": self._human_voice_module,
                "aliases": ("human_voice_handoff",),
                "handler": self._handle_human_voice_handoff,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "extraction_id",
                        "label": "Extraction Id",
                        "type": "text",
                        "required": True,
                    },
                ),
            },
            {
                "capability_id": "forensic_triangulation",
                "capability_label": "Forensic Triangulation",
                "capability_summary": "Correlate Mechanic, Scorpion, and Slingshot claims per case_id.",
                "tool": "forensic_triangulation",
                "tool_label": "Forensic Triangulation",
                "action": "correlate",
                "action_label": "Correlate Case",
                "module": self._forensic_triangulation_module,
                "aliases": ("forensic_triangulation", "triangulation_correlate"),
                "handler": self._handle_forensic_triangulation_correlate,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "case_id",
                        "label": "Case Id",
                        "type": "text",
                        "required": True,
                    },
                    {
                        "id": "fixture",
                        "label": "Fixture",
                        "type": "text",
                        "required": False,
                        "placeholder": "tri-demo-001",
                    },
                ),
            },
            {
                "capability_id": "narrative_trust_pack",
                "capability_label": "Narrative Trust Pack",
                "capability_summary": "Build, verify, and sign off governed narrative export packs.",
                "tool": "narrative_trust_pack_pack",
                "tool_label": "NTP Pack",
                "action": "pack",
                "action_label": "Build Pack",
                "module": self._narrative_trust_pack_module,
                "aliases": ("narrative_trust_pack", "narrative_pack"),
                "handler": self._handle_narrative_trust_pack_pack,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "pack_id",
                        "label": "Pack Id",
                        "type": "text",
                        "required": True,
                    },
                    {
                        "id": "from_capability_result",
                        "label": "Capability Result Path",
                        "type": "text",
                        "required": False,
                    },
                ),
            },
            {
                "capability_id": "narrative_trust_pack",
                "capability_label": "Narrative Trust Pack",
                "capability_summary": "Verify stage artifact hashes in a narrative trust pack.",
                "tool": "narrative_trust_pack_verify",
                "tool_label": "NTP Verify",
                "action": "verify",
                "action_label": "Verify Pack",
                "module": self._narrative_trust_pack_module,
                "aliases": ("narrative_trust_pack_verify",),
                "handler": self._handle_narrative_trust_pack_verify,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "pack_id",
                        "label": "Pack Id",
                        "type": "text",
                        "required": True,
                    },
                ),
            },
            {
                "capability_id": "narrative_trust_pack",
                "capability_label": "Narrative Trust Pack",
                "capability_summary": "Apply human signoff to a verified narrative trust pack.",
                "tool": "narrative_trust_pack_signoff",
                "tool_label": "NTP Signoff",
                "action": "signoff",
                "action_label": "Sign Off Pack",
                "module": self._narrative_trust_pack_module,
                "aliases": ("narrative_trust_pack_signoff",),
                "handler": self._handle_narrative_trust_pack_signoff,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "pack_id",
                        "label": "Pack Id",
                        "type": "text",
                        "required": True,
                    },
                    {
                        "id": "signoff_by",
                        "label": "Signoff By",
                        "type": "text",
                        "required": True,
                    },
                ),
            },
            {
                "capability_id": "story_forge_launcher",
                "capability_label": "Story Forge Launcher",
                "capability_summary": "Structured Story Forge source intake (governed admission gate).",
                "tool": "story_forge_launcher_intake",
                "tool_label": "Story Forge Intake",
                "action": "intake",
                "action_label": "Intake Source",
                "module": self._story_forge_launcher_module,
                "aliases": ("story_forge_launcher_intake", "story_forge_intake"),
                "handler": self._handle_story_forge_launcher_intake,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "source_ref",
                        "label": "Structured Source Ref",
                        "type": "text",
                        "required": True,
                    },
                ),
            },
            {
                "capability_id": "movie_renderer_lane",
                "capability_label": "Movie Renderer Lane",
                "capability_summary": "Propose movie render step post-BackendBuildArtifact.",
                "tool": "movie_renderer_lane_propose",
                "tool_label": "Propose Render",
                "action": "propose_render",
                "action_label": "Propose Render",
                "module": self._movie_renderer_lane_module,
                "aliases": ("movie_renderer_propose", "movie_renderer_lane"),
                "handler": self._handle_movie_renderer_lane_propose,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "backend_build_artifact_ref",
                        "label": "Backend Build Artifact Ref",
                        "type": "text",
                        "required": True,
                    },
                ),
            },
            {
                "capability_id": "text_game_to_video",
                "capability_label": "Text-Game-to-Video",
                "capability_summary": "Propose governed render plan (proposal-only).",
                "tool": "text_game_to_video_plan",
                "tool_label": "Propose Plan",
                "action": "propose_render_plan",
                "action_label": "Propose Render Plan",
                "module": self._text_game_to_video_module,
                "aliases": ("text_game_to_video_plan",),
                "handler": self._handle_text_game_to_video_plan,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "script_ref",
                        "label": "Script Ref",
                        "type": "text",
                        "required": True,
                    },
                ),
            },
            {
                "capability_id": "game_front_door",
                "capability_label": "Game Front Door",
                "capability_summary": "Operator-gated game session admission.",
                "tool": "game_front_door_admit",
                "tool_label": "Admit Session",
                "action": "admit_session",
                "action_label": "Admit Session",
                "module": self._game_front_door_module,
                "aliases": ("game_front_door_admit",),
                "handler": self._handle_game_front_door_admit,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "session_id",
                        "label": "Session Id",
                        "type": "text",
                        "required": True,
                    },
                    {
                        "id": "operator_ack",
                        "label": "Operator Ack",
                        "type": "checkbox",
                        "required": True,
                    },
                ),
            },
            {
                "capability_id": "text_to_3d_world_lane",
                "capability_label": "Text-to-3D World Lane",
                "capability_summary": "Read-only world lane route (stub until configured).",
                "tool": "text_to_3d_world_route",
                "tool_label": "World Lane Route",
                "action": "world_lane_route",
                "action_label": "World Lane Route",
                "module": self._text_to_3d_world_lane_module,
                "aliases": ("text_to_3d_world_route",),
                "handler": self._handle_text_to_3d_world_route,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (),
            },
            {
                "capability_id": "world_pack_lane",
                "capability_label": "World Pack Lane",
                "capability_summary": "Inspect world pack manifest (bounded read-only).",
                "tool": "world_pack_lane_inspect",
                "tool_label": "Inspect Manifest",
                "action": "inspect_manifest",
                "action_label": "Inspect Manifest",
                "module": self._world_pack_lane_module,
                "aliases": ("world_pack_inspect", "world_pack_lane"),
                "handler": self._handle_world_pack_lane_inspect,
                "endpoint": "/api/jarvis/capability-bridge/execute",
                "provider_modes": ("deterministic",),
                "default_provider_mode": "deterministic",
                "governance_modes": DEFAULT_GOVERNANCE_MODES,
                "default_governance_mode": "strict",
                "input_fields": (
                    {
                        "id": "pack_id",
                        "label": "Pack Id",
                        "type": "text",
                        "required": False,
                    },
                ),
            },
        ]
        self._routes = {
            _normalize_name(alias): spec
            for spec in self._route_specs
            for alias in spec["aliases"]
        }
        self._selection_routes = {
            (spec["capability_id"], spec["action"]): spec
            for spec in self._route_specs
        }

    def _module_action_for_spec(self, spec: dict[str, Any]) -> str:
        actions = tuple(spec["module"].supported_actions)
        if actions:
            return actions[0]
        return spec["action"]

    def _phase_component_id(self, spec: dict[str, Any]) -> str:
        return f"jarvis.capability.{spec['capability_id']}"

    def _ensure_phase_component(
        self,
        component_id: str,
        *,
        name: str,
        component_type: str,
        notes: str,
        validation_metadata: dict[str, Any] | None = None,
    ) -> None:
        try:
            get_component(component_id)
            return
        except ComponentNotRegisteredError:
            pass

        try:
            register_component(
                GovernedComponent(
                    component_id=component_id,
                    name=name,
                    component_type=component_type,
                    phase=Phase.ACTIVE,
                    allowed_contexts=list(DEFAULT_PHASE_ALLOWED_CONTEXTS),
                    notes=notes,
                    validation_metadata=dict(validation_metadata or {}),
                )
            )
        except PhaseGateError:
            # Another caller may have registered the same component concurrently.
            pass

    def _ensure_phase_gate_components(self) -> None:
        self._ensure_phase_component(
            BRIDGE_COMPONENT_ID,
            name="Capability Service Bridge",
            component_type="service_bridge",
            notes="Governed adapter bridge for service-lane capability execution.",
            validation_metadata={
                "bridge_id": BRIDGE_ID,
                "service_lane": "service_tools",
            },
        )
        for spec in self._route_specs:
            self._ensure_phase_component(
                self._phase_component_id(spec),
                name=spec["capability_label"],
                component_type="capability",
                notes=spec["capability_summary"],
                validation_metadata={
                    "tool": spec["tool"],
                    "endpoint": spec["endpoint"],
                    "module": spec["module"].module_name,
                    "action": self._module_action_for_spec(spec),
                },
            )

    def _phase_component_state(self, component_id: str, runtime_context: str) -> dict[str, Any]:
        normalized_context = _normalize_runtime_context(runtime_context)
        try:
            component = get_component(component_id)
        except ComponentNotRegisteredError:
            return {
                "component_id": component_id,
                "phase": "unregistered",
                "allowed_contexts": [],
                "runtime_context": normalized_context,
                "routable": False,
                "executable": False,
            }

        last_transition = component.history[-1] if component.history else None
        return {
            "component_id": component.component_id,
            "name": component.name,
            "component_type": component.component_type,
            "phase": component.phase.value,
            "allowed_contexts": list(component.allowed_contexts),
            "runtime_context": normalized_context,
            "routable": is_routable(component.component_id, normalized_context),
            "executable": is_executable(component.component_id, normalized_context),
            "last_transition_reason": last_transition.reason if last_transition else None,
            "last_transition_at": last_transition.recorded_at if last_transition else None,
        }

    def _phase_gate_recent_events(self, limit: int = 10) -> list[dict[str, Any]]:
        component_ids = {BRIDGE_COMPONENT_ID}
        component_ids.update(self._phase_component_id(spec) for spec in self._route_specs)
        return [
            event
            for event in list_phase_events(limit=max(limit * 4, limit))
            if event.get("component_id") in component_ids
        ][-limit:]

    def _evaluate_phase_gate(self, spec: dict[str, Any], runtime_context: str) -> dict[str, Any]:
        normalized_context = _normalize_runtime_context(runtime_context)
        self._ensure_phase_gate_components()
        bridge_state = self._phase_component_state(BRIDGE_COMPONENT_ID, normalized_context)
        capability_component_id = self._phase_component_id(spec)
        capability_state = self._phase_component_state(capability_component_id, normalized_context)
        checks = (
            ("routing", BRIDGE_COMPONENT_ID, bridge_state),
            ("routing", capability_component_id, capability_state),
            ("execution", BRIDGE_COMPONENT_ID, bridge_state),
            ("execution", capability_component_id, capability_state),
        )

        for check, component_id, state in checks:
            try:
                if check == "routing":
                    assert_routable(component_id, normalized_context)
                else:
                    assert_executable(component_id, normalized_context)
            except PhaseViolationError as exc:
                return {
                    "decision": "BLOCK",
                    "reason": str(exc),
                    "check": check,
                    "runtime_context": normalized_context,
                    "bridge_component": bridge_state,
                    "component": capability_state,
                    "blocked_component": state,
                }

        return {
            "decision": "ALLOW",
            "reason": None,
            "check": None,
            "runtime_context": normalized_context,
            "bridge_component": bridge_state,
            "component": capability_state,
        }

    def _build_phase_gate_block(
        self,
        spec: dict[str, Any],
        *,
        args: dict[str, Any],
        execution_profile: dict[str, Any] | None,
        phase_gate: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_profile = self._normalize_execution_profile(spec, execution_profile)
        capability_meta = {
            "bridge_id": BRIDGE_ID,
            "bridge_version": BRIDGE_VERSION,
            "tool_type": spec["tool"],
            "tool_label": spec["tool_label"],
            "capability": spec["capability_id"],
            "capability_label": spec["capability_label"],
            "module": spec["module"].module_name,
            "action": self._module_action_for_spec(spec),
            "action_label": spec["action_label"],
            "ok": False,
            "provider": spec["module"].provider_name,
            "model": None,
            "timestamp": None,
            "trace_id": None,
            "result_size": 0,
            "error_type": "PhaseViolationError",
            "service_lane": True,
            "path": "capability_service_bridge",
            "endpoint": spec["endpoint"],
            "requested_provider_mode": normalized_profile["provider_mode"],
            "governance_mode": normalized_profile["governance_mode"],
            "phase_gate": phase_gate,
        }
        event = self._record_event(capability_meta)
        capability_meta["audit_sequence"] = event["sequence"]
        response = (
            f"{spec['capability_label']} is blocked by phase gate: {phase_gate['reason']}"
        )
        return {
            "response": response,
            "tool_result": {
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "blocked",
                "args": dict(args),
                "result": {
                    "error": phase_gate["reason"],
                    "phase_gate": phase_gate,
                },
                "summary": response,
                "capability": capability_meta,
            },
            "execution_preview": self._build_execution_preview(
                spec,
                execution_profile,
                runtime_context=phase_gate["runtime_context"],
                phase_gate=phase_gate,
            ),
            "phase_gate": phase_gate,
        }

    def _build_genome_block(
        self,
        spec: dict[str, Any],
        reason: str,
        *,
        args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        capability_meta = {
            "bridge_id": BRIDGE_ID,
            "bridge_version": BRIDGE_VERSION,
            "tool_type": spec["tool"],
            "capability": spec["capability_id"],
            "module": spec["module"].module_name,
            "ok": False,
            "error_type": "GenomeValidationError",
            "service_lane": True,
            "path": "capability_service_bridge",
        }
        self._record_event(capability_meta)
        response = f"{spec['capability_label']} blocked by genome engine: {reason}"
        return {
            "response": response,
            "tool_result": {
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "blocked",
                "args": dict(args or {}),
                "result": {"error": reason, "genome_gate": True},
                "summary": response,
                "capability": capability_meta,
            },
        }

    def _execute_spec(
        self,
        spec: dict[str, Any],
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        runtime_context: str = DEFAULT_PHASE_CONTEXT,
    ) -> dict[str, Any]:
        from src.governance_organs import GenomeEngine, GenomeValidationError

        bridge_stage = (
            (GenomeEngine.registry().genomes.get("capability_service_bridge") or {})
            .get("identity", {})
            .get("stage", "")
        )
        if bridge_stage in {"mvp", "governed"}:
            try:
                GenomeEngine.assert_gene_callable("capability_service_bridge", stage_min="mvp")
            except GenomeValidationError as exc:
                return self._build_genome_block(spec, str(exc), args=args)

        gene_hint = spec.get("gene") or spec.get("capability_id") or spec.get("module")
        if isinstance(gene_hint, object) and hasattr(gene_hint, "module_name"):
            gene_hint = getattr(gene_hint, "module_name", gene_hint)
        gene = GenomeEngine.resolve_gene(str(gene_hint or ""))
        if gene and gene != "capability_service_bridge":
            gene_stage = (
                (GenomeEngine.registry().genomes.get(gene) or {}).get("identity", {}).get("stage", "")
            )
            if gene_stage in {"mvp", "governed"}:
                try:
                    GenomeEngine.assert_gene_callable(gene, stage_min="mvp")
                except GenomeValidationError as exc:
                    return self._build_genome_block(spec, str(exc), args=args)

        route_key = (spec["capability_id"], spec["action"])
        if route_key not in self._selection_routes:
            return self._build_genome_block(
                spec,
                f"unregistered bridge action: {spec['capability_id']}/{spec['action']}",
                args=args,
            )

        from src.governance_organs.adaptive_engine import AdaptiveEngine

        ctx_result = AdaptiveEngine().evaluate_context(
            runtime_context,
            spec.get("capability_id"),
            gene=gene,
        )
        if ctx_result.blocked:
            return self._build_genome_block(
                spec,
                ctx_result.reason or "contextual gate blocked",
                args=args,
            )

        from src.adaptive_lane_organ import lane_authorizes_capability, resolve_lane_for_gene

        lane_resolution = lane_authorizes_capability(
            resolve_lane_for_gene(gene),
            spec.get("capability_id"),
        )
        if not lane_resolution.allowed:
            return self._build_genome_block(
                spec,
                lane_resolution.reason or "adaptive lane blocked",
                args=args,
            )

        from src.operator_cognition_coherence_fabric import (
            evaluate_bridge_coherence,
            coherence_inputs_for_bridge,
        )

        bridge_mode, _, fabric_aligned, safety_halt = coherence_inputs_for_bridge(
            self.snapshot(),
            gene=gene,
        )
        coherence = evaluate_bridge_coherence(
            capability_id=spec.get("capability_id"),
            lane_resolution=lane_resolution,
            bridge_governance_mode=bridge_mode,
            fabric_genes_aligned=fabric_aligned,
            safety_halt=safety_halt,
        )
        if not coherence.allowed:
            return self._build_genome_block(
                spec,
                coherence.reason or "coherence fabric blocked",
                args=args,
            )

        prepared_args = self._prepare_args_for_selection(spec, dict(args or {}))
        phase_gate = self._evaluate_phase_gate(spec, runtime_context)
        if phase_gate["decision"] == "BLOCK":
            return self._build_phase_gate_block(
                spec,
                args=prepared_args,
                execution_profile=execution_profile,
                phase_gate=phase_gate,
            )
        return spec["handler"](
            prepared_args,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _grouped_capabilities(self) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for spec in self._route_specs:
            capability = grouped.setdefault(
                spec["capability_id"],
                {
                    "id": spec["capability_id"],
                    "label": spec["capability_label"],
                    "summary": spec["capability_summary"],
                    "module": spec["module"].module_name,
                    "tool": spec["tool"],
                    "aliases": list(spec["aliases"]),
                    "default_action": spec["action"],
                    "actions": [],
                },
            )
            capability["actions"].append(
                {
                    "id": spec["action"],
                    "label": spec["action_label"],
                    "description": spec["capability_summary"],
                    "tool": spec["tool"],
                    "endpoint": spec["endpoint"],
                    "input_fields": [dict(field) for field in spec["input_fields"]],
                    "provider_modes": list(spec["provider_modes"]),
                    "default_provider_mode": spec["default_provider_mode"],
                    "governance_modes": list(spec["governance_modes"]),
                    "default_governance_mode": spec["default_governance_mode"],
                }
            )
        return list(grouped.values())

    def _module_health_snapshot(self) -> dict[str, Any]:
        self._ensure_phase_gate_components()
        health: dict[str, Any] = {}
        for spec in self._route_specs:
            capability_id = spec["capability_id"]
            phase_state = self._phase_component_state(self._phase_component_id(spec), OPERATOR_PHASE_CONTEXT)
            capability_events = [
                event
                for event in self._events
                if event.get("capability_id") == capability_id
            ]
            last_event = capability_events[-1] if capability_events else None
            status = "ready"
            if last_event and last_event.get("ok") is False:
                status = "degraded"
            health[capability_id] = {
                "module": spec["module"].module_name,
                "provider": spec["module"].provider_name,
                "status": status,
                "tool": spec["tool"],
                "action": spec["action"],
                "registered_actions": [spec["action"]],
                "phase": phase_state.get("phase"),
                "allowed_contexts": list(phase_state.get("allowed_contexts") or []),
                "recent_event_count": len(capability_events),
                "last_seen": last_event.get("timestamp") if last_event else None,
                "last_error_type": last_event.get("error_type") if last_event else None,
            }
        return health

    def snapshot(self) -> dict[str, Any]:
        """Expose governed capability bridge state for runtime inspection."""
        self._ensure_phase_gate_components()
        available_capabilities = self._grouped_capabilities()
        from src.aais_ul_substrate import wrap_runtime_snapshot

        return wrap_runtime_snapshot(
            {
                "bridge_id": BRIDGE_ID,
                "version": BRIDGE_VERSION,
                "path": "capability_service_bridge",
                "service_lane": "service_tools",
                "registry": {
                    capability["id"]: [action["id"] for action in capability["actions"]]
                    for capability in available_capabilities
                },
                "registered_tools": [
                    {
                        "tool": spec["tool"],
                        "module": spec["module"].module_name,
                        "action": spec["action"],
                        "capability": spec["capability_id"],
                        "aliases": list(spec["aliases"]),
                    }
                    for spec in self._route_specs
                ],
                "available_capabilities": available_capabilities,
                "module_health": self._module_health_snapshot(),
                "phase_gate": {
                    "bridge": self._phase_component_state(BRIDGE_COMPONENT_ID, OPERATOR_PHASE_CONTEXT),
                    "capabilities": {
                        spec["capability_id"]: self._phase_component_state(
                            self._phase_component_id(spec),
                            OPERATOR_PHASE_CONTEXT,
                        )
                        for spec in self._route_specs
                    },
                    "recent_events": self._phase_gate_recent_events(limit=10),
                },
                "event_count": len(self._events),
                "recent_events": list(self._events[-10:]),
            }
        )

    def handle_tool_request(
        self,
        tool_name: str,
        args: dict[str, Any] | None = None,
        *,
        runtime_context: str = DEFAULT_PHASE_CONTEXT,
    ):
        """Return a normalized direct-tool result when a capability route is registered."""
        spec = self._routes.get(_normalize_name(tool_name))
        if spec is None:
            return None
        return self._execute_spec(
            spec,
            dict(args or {}),
            runtime_context=runtime_context,
        )

    def execute_selection(
        self,
        capability_id: str,
        action: str,
        *,
        args: dict[str, Any] | None = None,
        execution_profile: dict[str, Any] | None = None,
        runtime_context: str = OPERATOR_PHASE_CONTEXT,
    ) -> dict[str, Any]:
        """Run one capability selection from the registry-facing UI surface."""
        spec = self._selection_routes.get((_normalize_name(capability_id), _normalize_name(action)))
        if spec is None:
            raise ValueError("Unsupported capability or action selection.")
        return self._execute_spec(
            spec,
            dict(args or {}),
            execution_profile=execution_profile,
            runtime_context=runtime_context,
        )

    def preview_selection(
        self,
        capability_id: str,
        action: str,
        *,
        execution_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Expose the deterministic preview for one capability selection."""
        spec = self._selection_routes.get((_normalize_name(capability_id), _normalize_name(action)))
        if spec is None:
            raise ValueError("Unsupported capability or action selection.")
        from src.aais_ul_substrate import wrap_runtime_snapshot

        return wrap_runtime_snapshot(
            self._build_execution_preview(spec, execution_profile)
        )

    def _prepare_args_for_selection(self, spec: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        capability_id = spec["capability_id"]
        payload = dict(args or {})
        if capability_id == "mystic":
            return {
                "input": _clean_text(
                    payload.get("input") or payload.get("text") or payload.get("message") or payload.get("prompt"),
                    "I need a mystic reading of my current state.",
                ),
            }
        if capability_id in {"v9_core", "v10_core"}:
            return {
                "input": _clean_text(
                    payload.get("input") or payload.get("text") or payload.get("message") or payload.get("prompt"),
                    "Continue this scene.",
                ),
                "context": _clean_text(payload.get("context"), ""),
                "location": _clean_text(payload.get("location"), "Unknown"),
                "characters": _normalize_characters(payload.get("characters") or []),
            }
        if capability_id == "spatial":
            prepared = dict(payload)
            prepared["mode"] = _clean_text(prepared.get("mode"), "visibility")
            prepared["space_id"] = _clean_text(prepared.get("space_id"), "operator_grid")
            bool_value = _coerce_bool(prepared.get("line_of_sight"))
            if bool_value is not None:
                prepared["line_of_sight"] = bool_value
            return prepared
        return payload

    def _normalize_execution_profile(
        self,
        spec: dict[str, Any],
        execution_profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        requested = dict(execution_profile or {})
        requested_provider_mode = _normalize_name(requested.get("provider_mode")) or spec["default_provider_mode"]
        if requested_provider_mode not in spec["provider_modes"]:
            requested_provider_mode = spec["default_provider_mode"]
        requested_governance_mode = (
            _normalize_name(requested.get("governance_mode"))
            or spec["default_governance_mode"]
        )
        if requested_governance_mode not in spec["governance_modes"]:
            requested_governance_mode = spec["default_governance_mode"]
        return {
            "provider_mode": requested_provider_mode,
            "governance_mode": requested_governance_mode,
        }

    def _build_execution_preview(
        self,
        spec: dict[str, Any],
        execution_profile: dict[str, Any] | None,
        *,
        runtime_context: str = OPERATOR_PHASE_CONTEXT,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_profile = self._normalize_execution_profile(spec, execution_profile)
        normalized_context = _normalize_runtime_context(runtime_context, default=OPERATOR_PHASE_CONTEXT)
        phase_snapshot = phase_gate or {
            "decision": "UNKNOWN",
            "reason": None,
            "runtime_context": normalized_context,
            "component": self._phase_component_state(self._phase_component_id(spec), normalized_context),
        }
        return {
            "capability": spec["capability_id"],
            "capability_label": spec["capability_label"],
            "action": spec["action"],
            "action_label": spec["action_label"],
            "tool": spec["tool"],
            "tool_label": spec["tool_label"],
            "module": spec["module"].module_name,
            "path": "capability_service_bridge",
            "flow": list(DEFAULT_SERVICE_PATH),
            "service_lane": "service_tools",
            "endpoint": spec["endpoint"],
            "provider_mode_requested": normalized_profile["provider_mode"],
            "provider_modes_supported": list(spec["provider_modes"]),
            "governance_mode": normalized_profile["governance_mode"],
            "governance_modes_supported": list(spec["governance_modes"]),
            "runtime_context": normalized_context,
            "phase_gate": phase_snapshot,
            "authority_note": "Selection is governed input only; bridge execution remains authoritative.",
        }

    def _execute_spatial(self, payload: dict[str, Any]):
        mode = payload.get("mode")
        query_args = {key: value for key, value in payload.items() if key != "mode"}
        return self._spatial_query(mode, **query_args)

    def _execute_mystic(self, payload: dict[str, Any]):
        return self._mystic_read(payload["input"])

    def _execute_v9(self, payload: dict[str, Any]):
        return self._v9_run(
            payload["input"],
            context=payload.get("context", ""),
            location=payload.get("location", "Unknown"),
            characters=payload.get("characters", []),
        )

    def _execute_v10(self, payload: dict[str, Any]):
        return self._v10_run(
            payload["input"],
            context=payload.get("context", ""),
            location=payload.get("location", "Unknown"),
            characters=payload.get("characters", []),
        )

    def _build_capability_meta(
        self,
        spec: dict[str, Any],
        capability_result: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        meta = dict(capability_result.get("meta") or {})
        details = dict(capability_result.get("details") or {})
        payload_result = dict(result or {})
        normalized_profile = self._normalize_execution_profile(spec, execution_profile)
        capability_meta = {
            "bridge_id": BRIDGE_ID,
            "bridge_version": BRIDGE_VERSION,
            "tool_type": spec["tool"],
            "tool_label": spec["tool_label"],
            "capability": spec["capability_id"],
            "capability_label": spec["capability_label"],
            "module": capability_result.get("module"),
            "action": capability_result.get("action"),
            "action_label": spec["action_label"],
            "ok": bool(capability_result.get("ok")),
            "provider": payload_result.get("provider") or meta.get("provider") or details.get("provider"),
            "model": payload_result.get("model"),
            "timestamp": meta.get("timestamp") or details.get("timestamp"),
            "trace_id": meta.get("trace_id") or details.get("trace_id"),
            "result_size": meta.get("result_size"),
            "error_type": capability_result.get("error_type"),
            "service_lane": True,
            "path": "capability_service_bridge",
            "endpoint": spec["endpoint"],
            "requested_provider_mode": normalized_profile["provider_mode"],
            "governance_mode": normalized_profile["governance_mode"],
            "phase_gate": dict(phase_gate or {}),
        }
        event = self._record_event(capability_meta)
        capability_meta["audit_sequence"] = event["sequence"]
        return capability_meta

    def _record_event(self, capability_meta: dict[str, Any]) -> dict[str, Any]:
        self._event_counter += 1
        event = {
            "sequence": self._event_counter,
            "tool_type": capability_meta.get("tool_type"),
            "tool_label": capability_meta.get("tool_label"),
            "capability_id": capability_meta.get("capability"),
            "capability_label": capability_meta.get("capability_label"),
            "module": capability_meta.get("module"),
            "action": capability_meta.get("action"),
            "provider": capability_meta.get("provider"),
            "model": capability_meta.get("model"),
            "timestamp": capability_meta.get("timestamp"),
            "trace_id": capability_meta.get("trace_id"),
            "ok": capability_meta.get("ok"),
            "error_type": capability_meta.get("error_type"),
            "requested_provider_mode": capability_meta.get("requested_provider_mode"),
            "governance_mode": capability_meta.get("governance_mode"),
        }
        self._events.append(event)
        if len(self._events) > MAX_AUDIT_EVENTS:
            self._events = self._events[-MAX_AUDIT_EVENTS:]
        if capability_meta.get("ok"):
            try:
                from src.ugr.rewards.reward_hooks import emit_capability_bridge_executed

                emit_capability_bridge_executed(
                    tenant_id=str(capability_meta.get("tenant_id") or "global"),
                    operator_id=str(capability_meta.get("operator_id") or "operator"),
                    trace_id=str(capability_meta.get("trace_id") or ""),
                    module=str(capability_meta.get("module") or ""),
                    action=str(capability_meta.get("action") or ""),
                    audit_sequence=event.get("sequence"),
                    ok=True,
                )
            except Exception:
                pass
        return event

    def _finalize_result(
        self,
        *,
        spec: dict[str, Any],
        capability_result: dict[str, Any],
        response: str,
        tool_result: dict[str, Any],
        execution_profile: dict[str, Any] | None = None,
        result_payload: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        finalized_tool_result = dict(tool_result)
        finalized_tool_result["summary"] = response
        finalized_tool_result["capability"] = self._build_capability_meta(
            spec,
            capability_result,
            execution_profile=execution_profile,
            result=result_payload,
            phase_gate=phase_gate,
        )
        from src.aais_ul_substrate import wrap_service_bridge_result

        wrapped = wrap_service_bridge_result(
            {
                "response": response,
                "tool_result": finalized_tool_result,
                "execution_preview": self._build_execution_preview(
                    spec,
                    execution_profile,
                    runtime_context=(phase_gate or {}).get("runtime_context", OPERATOR_PHASE_CONTEXT),
                    phase_gate=phase_gate,
                ),
                "phase_gate": dict(phase_gate or {}),
            }
        )
        try:
            from src.cisiv import normalize_cisiv_stage
            from src.ul_lineage import record_lineage_event

            session_id = str((execution_profile or {}).get("session_id") or "").strip() or None
            record_lineage_event(
                node_type="capability_call",
                cisiv_stage=normalize_cisiv_stage(
                    (phase_gate or {}).get("cisiv_stage") or "implementation"
                ),
                session_id=session_id,
                claim_label="asserted",
                source_module="src.capability_service_bridge",
                payload={"capability": spec.get("capability") or spec.get("name")},
            )
        except Exception:
            pass
        return wrapped

    def _handle_spatial_reason(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("spatial", "reason")]
        payload = dict(args or {})
        capability_result = self._spatial_module.execute("query", payload)
        if capability_result.get("ok"):
            result = dict(capability_result.get("data") or {})
            response = self._render_spatial(payload, result)
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": "spatial_reason",
                    "tool": "spatial_reason",
                    "status": "failed" if result.get("error") else "completed",
                    "mode": _normalize_name(payload.get("mode")),
                    "space_id": payload.get("space_id"),
                    "result": result,
                    "args": payload,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=result,
                phase_gate=phase_gate,
            )

        response = f"Spatial reasoning could not run: {capability_result.get('message', 'Unknown error')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": "spatial_reason",
                "tool": "spatial_reason",
                "status": "failed",
                "mode": _normalize_name(payload.get("mode")),
                "space_id": payload.get("space_id"),
                "result": {"error": capability_result.get("message", "Unknown error")},
                "args": payload,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_mystic_reading(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("mystic", "reading")]
        payload = dict(args or {})
        input_text = payload["input"]
        capability_result = self._mystic_module.execute("read", payload)
        if capability_result.get("ok"):
            result = dict(capability_result.get("data") or {})
            response = self._render_mystic(result)
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": "mystic_reading",
                    "tool": "mystic_reading",
                    "status": "completed",
                    "input": input_text,
                    "result": result,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=result,
                phase_gate=phase_gate,
            )

        response = f"Mystic reading could not run: {capability_result.get('message', 'Unknown error')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": "mystic_reading",
                "tool": "mystic_reading",
                "status": "failed",
                "input": input_text,
                "result": {
                    "input": input_text,
                    "error": capability_result.get("message", "Unknown error"),
                },
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_v9_core(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("v9_core", "generate_scene")]
        payload = dict(args or {})
        capability_result = self._v9_module.execute("generate_scene", payload)
        if capability_result.get("ok"):
            result = dict(capability_result.get("data") or {})
            response = self._render_v9(result)
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": "v9_core",
                    "tool": "v9_core",
                    "status": result.get("status", "completed"),
                    "input": payload["input"],
                    "result": result,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=result,
                phase_gate=phase_gate,
            )

        response = f"V9 Core could not run: {capability_result.get('message', 'Unknown error')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": "v9_core",
                "tool": "v9_core",
                "status": "failed",
                "input": payload["input"],
                "result": {
                    "status": "failed",
                    "input": payload["input"],
                    "context": payload["context"],
                    "location": payload["location"],
                    "characters": payload["characters"],
                    "error": capability_result.get("message", "Unknown error"),
                },
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_v10_core(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("v10_core", "generate_scene")]
        payload = dict(args or {})
        capability_result = self._v10_module.execute("generate_scene", payload)
        if capability_result.get("ok"):
            result = dict(capability_result.get("data") or {})
            response = self._render_v10(result)
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": "v10_core",
                    "tool": "v10_core",
                    "status": result.get("status", "completed"),
                    "input": payload["input"],
                    "result": result,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=result,
                phase_gate=phase_gate,
            )

        response = f"V10 Core could not run: {capability_result.get('message', 'Unknown error')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": "v10_core",
                "tool": "v10_core",
                "status": "failed",
                "input": payload["input"],
                "result": {
                    "status": "failed",
                    "input": payload["input"],
                    "context": payload["context"],
                    "location": payload["location"],
                    "characters": payload["characters"],
                    "error": capability_result.get("message", "Unknown error"),
                },
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _alt3_runtime_context(self, phase_gate: dict[str, Any] | None) -> str:
        return _normalize_runtime_context(
            (phase_gate or {}).get("runtime_context"),
            OPERATOR_PHASE_CONTEXT,
        )

    def _alt3_execution_profile_fields(
        self, execution_profile: dict[str, Any] | None
    ) -> dict[str, Any]:
        profile = dict(execution_profile or {})
        fields: dict[str, Any] = {}
        for key in (
            "session_id",
            "mission_id",
            "imagine_root",
            "story_forge_root",
            "extraction_root",
            "speakers_root",
            "recipe_root",
            "triangulation_root",
            "mechanic_root",
            "scorpion_root",
            "slingshot_root",
            "narrative_root",
        ):
            if profile.get(key):
                fields[key] = profile[key]
        return fields

    def _alt3_capability_result(
        self,
        cap: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "ok": bool(cap.get("ok")),
            "data": cap,
            "message": cap.get("message") or cap.get("error_type") or "",
        }

    def _handle_recipe_module_create_mission(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("recipe_module", "create_mission")]
        payload = dict(args or {})
        recipe_id = str(payload.get("recipe_id") or "").strip()
        signoff_ack = _coerce_bool(payload.get("signoff_ack"))
        if signoff_ack is None:
            signoff_ack = False
        try:
            from src.mission_board import mission_board

            profile = self._alt3_execution_profile_fields(execution_profile)
            snapshot = mission_board.create_from_recipe(
                recipe_id,
                session_id=profile.get("session_id"),
                signoff_ack=signoff_ack,
                recipe_root=profile.get("recipe_root"),
            )
            active = snapshot.get("active_mission") or {}
            response = f"Recipe mission created: {active.get('title', recipe_id)}"
            capability_result = {"ok": True, "data": {"mission_board": snapshot}}
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "recipe_id": recipe_id,
                    "result": {"active_mission_id": active.get("id"), "title": active.get("title")},
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload={"recipe_id": recipe_id, "mission_id": active.get("id")},
                phase_gate=phase_gate,
            )
        except Exception as exc:  # noqa: BLE001
            response = f"Recipe module could not create mission: {exc}"
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "failed",
                    "recipe_id": recipe_id,
                    "result": {"error": str(exc)},
                },
                capability_result={"ok": False, "message": str(exc)},
                response=response,
                execution_profile=execution_profile,
                phase_gate=phase_gate,
            )

    def _handle_imagine_emit(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("imagine_generator", "emit")]
        from src.capabilities.imagine_generator import run_imagine_generator_capability

        request = {
            "action": "emit",
            "runtime_context": self._alt3_runtime_context(phase_gate),
            **self._alt3_execution_profile_fields(execution_profile),
            **dict(args or {}),
        }
        cap = run_imagine_generator_capability(request)
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            pattern = cap.get("pattern") or {}
            response = f"Imagine pattern emitted: {pattern.get('pattern_id', '')}"
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "result": pattern,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=pattern,
                phase_gate=phase_gate,
            )
        response = f"Imagine emit failed: {cap.get('message', 'unknown')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "failed",
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_imagine_handoff(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("imagine_generator", "handoff")]
        from src.capabilities.imagine_generator import run_imagine_generator_capability

        request = {
            "action": "handoff",
            "runtime_context": self._alt3_runtime_context(phase_gate),
            **self._alt3_execution_profile_fields(execution_profile),
            **dict(args or {}),
        }
        cap = run_imagine_generator_capability(request)
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            response = "Imagine pattern admitted to Story Forge."
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "result": cap.get("result") or {},
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=cap.get("result"),
                phase_gate=phase_gate,
            )
        response = f"Imagine handoff failed: {cap.get('message', 'unknown')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "failed",
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_imagine_grok_render(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("imagine_generator", "grok_render")]
        from src.capabilities.imagine_generator import run_imagine_generator_capability

        request = {
            "action": "grok_render",
            "runtime_context": self._alt3_runtime_context(phase_gate),
            **self._alt3_execution_profile_fields(execution_profile),
            **dict(args or {}),
        }
        cap = run_imagine_generator_capability(request)
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            response = "Grok render completed for imagine pattern."
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "result": cap.get("result") or cap.get("artifact") or {},
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=cap,
                phase_gate=phase_gate,
            )
        err = cap.get("message") or cap.get("error_type") or "unknown"
        status = "blocked" if cap.get("error_type") == "KeysRequired" else "failed"
        response = f"Imagine grok render failed: {err}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": status,
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_human_voice_extract(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("human_voice_extraction", "extract")]
        from src.capabilities.human_voice_extraction import run_human_voice_extraction_capability

        request = {
            "action": "extract",
            "runtime_context": self._alt3_runtime_context(phase_gate),
            **self._alt3_execution_profile_fields(execution_profile),
            **dict(args or {}),
        }
        cap = run_human_voice_extraction_capability(request)
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            extraction = cap.get("extraction") or {}
            response = f"Voice extraction complete: {extraction.get('extraction_id', '')}"
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "result": extraction,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=extraction,
                phase_gate=phase_gate,
            )
        response = f"Human voice extract failed: {cap.get('message', 'unknown')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "failed",
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_human_voice_signoff(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("human_voice_extraction", "signoff")]
        from src.capabilities.human_voice_extraction import run_human_voice_extraction_capability

        request = {
            "action": "signoff",
            "runtime_context": self._alt3_runtime_context(phase_gate),
            **self._alt3_execution_profile_fields(execution_profile),
            **dict(args or {}),
        }
        cap = run_human_voice_extraction_capability(request)
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            response = "Voice extraction signed off."
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "result": cap.get("extraction") or {},
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=cap.get("extraction"),
                phase_gate=phase_gate,
            )
        response = f"Human voice signoff failed: {cap.get('message', 'unknown')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "failed",
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_human_voice_handoff(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("human_voice_extraction", "handoff")]
        from src.capabilities.human_voice_extraction import run_human_voice_extraction_capability

        request = {
            "action": "handoff",
            "runtime_context": self._alt3_runtime_context(phase_gate),
            **self._alt3_execution_profile_fields(execution_profile),
            **dict(args or {}),
        }
        cap = run_human_voice_extraction_capability(request)
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            response = "Voice constraints admitted to Speakers lane."
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "result": cap.get("result") or {},
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=cap.get("result"),
                phase_gate=phase_gate,
            )
        response = f"Human voice handoff failed: {cap.get('message', 'unknown')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "failed",
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_forensic_triangulation_correlate(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("forensic_triangulation", "correlate")]
        from src.capabilities.forensic_triangulation import run_forensic_triangulation_capability

        request = {
            "action": "correlate",
            "runtime_context": self._alt3_runtime_context(phase_gate),
            **self._alt3_execution_profile_fields(execution_profile),
            **dict(args or {}),
        }
        cap = run_forensic_triangulation_capability(request)
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            triangulation = cap.get("triangulation") or {}
            response = (
                f"Triangulation complete for {cap.get('case_id')}: "
                f"{cap.get('edge_count', 0)} correlation edge(s)"
            )
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "case_id": cap.get("case_id"),
                    "result": triangulation,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=triangulation,
                phase_gate=phase_gate,
            )
        response = f"Forensic triangulation failed: {cap.get('message', 'unknown')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "failed",
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_narrative_trust_pack_pack(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("narrative_trust_pack", "pack")]
        from src.capabilities.narrative_trust_pack import run_narrative_trust_pack_capability

        request = {
            "action": "pack",
            "runtime_context": self._alt3_runtime_context(phase_gate),
            **self._alt3_execution_profile_fields(execution_profile),
            **dict(args or {}),
        }
        cap = run_narrative_trust_pack_capability(request)
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            pack = cap.get("pack") or {}
            response = f"Narrative trust pack created: {pack.get('pack_id', '')}"
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "result": pack,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=pack,
                phase_gate=phase_gate,
            )
        response = f"Narrative trust pack build failed: {cap.get('message', 'unknown')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "failed",
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_narrative_trust_pack_verify(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("narrative_trust_pack", "verify")]
        from src.capabilities.narrative_trust_pack import run_narrative_trust_pack_capability

        request = {
            "action": "verify",
            "runtime_context": self._alt3_runtime_context(phase_gate),
            **self._alt3_execution_profile_fields(execution_profile),
            **dict(args or {}),
        }
        cap = run_narrative_trust_pack_capability(request)
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            response = f"Narrative trust pack verified: {cap.get('pack_id', '')}"
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "result": cap,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=cap,
                phase_gate=phase_gate,
            )
        response = f"Narrative trust pack verify failed: {cap.get('message', 'unknown')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "failed",
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_narrative_trust_pack_signoff(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[("narrative_trust_pack", "signoff")]
        from src.capabilities.narrative_trust_pack import run_narrative_trust_pack_capability

        request = {
            "action": "signoff",
            "runtime_context": self._alt3_runtime_context(phase_gate),
            **self._alt3_execution_profile_fields(execution_profile),
            **dict(args or {}),
        }
        cap = run_narrative_trust_pack_capability(request)
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            pack = cap.get("pack") or {}
            response = f"Narrative trust pack signed off: {pack.get('pack_id', '')}"
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "result": pack,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=pack,
                phase_gate=phase_gate,
            )
        response = f"Narrative trust pack signoff failed: {cap.get('message', 'unknown')}"
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "failed",
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_story_forge_organ_action(
        self,
        spec_key: tuple[str, str],
        runner: Callable[[dict[str, Any]], dict[str, Any]],
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = self._selection_routes[spec_key]
        cap = runner(dict(args or {}))
        capability_result = self._alt3_capability_result(cap)
        if cap.get("ok"):
            response = str(cap.get("message") or "Story Forge organ action completed")
            return self._finalize_result(
                spec=spec,
                tool_result={
                    "type": spec["tool"],
                    "tool": spec["tool"],
                    "status": "completed",
                    "result": cap,
                },
                capability_result=capability_result,
                response=response,
                execution_profile=execution_profile,
                result_payload=cap,
                phase_gate=phase_gate,
            )
        response = str(cap.get("message") or "Story Forge organ action blocked")
        return self._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "failed",
                "result": cap,
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_story_forge_launcher_intake(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from src.story_forge_launcher_organ import execute_story_forge_launcher_intake

        return self._handle_story_forge_organ_action(
            ("story_forge_launcher", "intake"),
            execute_story_forge_launcher_intake,
            args,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_movie_renderer_lane_propose(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from src.movie_renderer_lane_organ import execute_movie_renderer_lane_render

        return self._handle_story_forge_organ_action(
            ("movie_renderer_lane", "propose_render"),
            execute_movie_renderer_lane_render,
            args,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_text_game_to_video_plan(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from src.text_game_to_video_organ import execute_text_game_to_video_plan

        return self._handle_story_forge_organ_action(
            ("text_game_to_video", "propose_render_plan"),
            execute_text_game_to_video_plan,
            args,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_game_front_door_admit(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from src.game_front_door_organ import execute_game_front_door_admit

        return self._handle_story_forge_organ_action(
            ("game_front_door", "admit_session"),
            execute_game_front_door_admit,
            args,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_text_to_3d_world_route(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from src.text_to_3d_world_lane_organ import execute_text_to_3d_world_lane_route

        return self._handle_story_forge_organ_action(
            ("text_to_3d_world_lane", "world_lane_route"),
            execute_text_to_3d_world_lane_route,
            args,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    def _handle_world_pack_lane_inspect(
        self,
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from src.world_pack_lane_organ import execute_world_pack_lane_inspect

        return self._handle_story_forge_organ_action(
            ("world_pack_lane", "inspect_manifest"),
            execute_world_pack_lane_inspect,
            args,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def to_bridge_envelope(
    snapshot: dict[str, Any],
    *,
    cisiv_stage: str = "implementation",
    claim_label: str = "asserted",
) -> dict[str, Any]:
    """Map a bridge snapshot to capability_service_bridge.v1."""
    now = _utc_now_iso()
    recent_events = list(snapshot.get("recent_events") or [])
    last_event = recent_events[-1] if recent_events else {}
    governance_mode = str(
        last_event.get("governance_mode")
        or (snapshot.get("phase_gate") or {}).get("bridge", {}).get("governance_mode")
        or "strict"
    ).strip().lower()
    if governance_mode not in DEFAULT_GOVERNANCE_MODES:
        governance_mode = "strict"

    capability_call = None
    if last_event:
        capability_call = {
            "capability_id": str(last_event.get("capability_id") or last_event.get("tool_type") or ""),
            "module_path": str(last_event.get("module") or ""),
            "outcome": "allowed" if last_event.get("ok") else "error",
            "phase_context": OPERATOR_PHASE_CONTEXT,
            "audit_event_count": int(snapshot.get("event_count") or len(recent_events)),
            "claim_label": claim_label,
        }

    phase_events = []
    for index, event in enumerate((snapshot.get("phase_gate") or {}).get("recent_events") or []):
        if not isinstance(event, dict):
            continue
        phase_events.append(
            {
                "event_id": str(event.get("event_id") or f"phase-{index + 1}"),
                "phase": str(event.get("phase") or event.get("to_phase") or ""),
                "component_id": str(event.get("component_id") or BRIDGE_COMPONENT_ID),
                "context": str(event.get("context") or event.get("runtime_context") or DEFAULT_PHASE_CONTEXT),
                "claim_label": claim_label,
            }
        )

    envelope: dict[str, Any] = {
        "capability_service_bridge_version": "capability_service_bridge.v1",
        "bridge_id": str(snapshot.get("bridge_id") or BRIDGE_ID),
        "component_id": BRIDGE_COMPONENT_ID,
        "bridge_version": str(snapshot.get("version") or BRIDGE_VERSION),
        "governance_mode": governance_mode,
        "phase_context": str(
            (snapshot.get("phase_gate") or {}).get("bridge", {}).get("runtime_context")
            or DEFAULT_PHASE_CONTEXT
        ),
        "service_path": list(DEFAULT_SERVICE_PATH),
        "cisiv_stage": cisiv_stage,
        "claim_label": claim_label,
        "created_at_utc": now,
        "updated_at_utc": now,
    }
    if capability_call:
        envelope["capability_call"] = capability_call
    if phase_events:
        envelope["phase_events"] = phase_events
    return envelope
