"""Register universal gap-path adapters on CapabilityServiceBridge."""

from __future__ import annotations

from typing import Any

from src.capabilities.action_lane import ACTION_LANE_COMPONENT_ID, ActionLaneCapability
from src.capabilities.beatbox_score import BEATBOX_LANE_COMPONENT_ID, BeatboxScoreCapability
from src.capabilities.document_vision import DOCUMENT_VISION_COMPONENT_ID, DocumentVisionCapability
from src.capabilities.forge_lane import FORGE_LANE_COMPONENT_ID, ForgeLaneCapability
from src.capabilities.media_processor import (
    MEDIA_PROCESSOR_COMPONENT_ID,
    AudioAnalyzeCapability,
    ImageTransformCapability,
    VideoAnalyzeCapability,
)
from src.capabilities.memory_lane import MEMORY_LANE_COMPONENT_ID, MemoryLaneCapability
from src.capabilities.speakers_mix import SPEAKERS_LANE_COMPONENT_ID, SpeakersMixCapability
from src.capabilities.ui_vision import UI_VISION_COMPONENT_ID, UiVisionCapability
from src.capabilities.workspace_lane import WORKSPACE_LANE_COMPONENT_ID, WorkspaceLaneCapability
from src.capability_service_bridge import DEFAULT_GOVERNANCE_MODES, CapabilityServiceBridge
from src.forge_client import forge_client
from src.evolve_client import evolve_client


def _normalize_name(value: str | None) -> str:
    return " ".join(str(value or "").replace("-", "_").split()).strip().lower()


def attach_universal_gap_adapters(
    bridge: CapabilityServiceBridge,
    *,
    memory_enforcer: Any,
    workspace_tools: Any,
    profile_detector: Any,
    governance_layer: Any,
    patchforge: Any,
) -> None:
    """Extend bridge routes for memory/workspace/action/forge and media/story lanes."""
    if getattr(bridge, "_universal_adapters_attached", False):
        return

    bridge._memory_lane_module = MemoryLaneCapability(memory_enforcer=memory_enforcer)
    bridge._workspace_lane_module = WorkspaceLaneCapability(
        workspace_tools=workspace_tools,
        profile_detector=profile_detector,
    )
    bridge._action_lane_module = ActionLaneCapability(governance_layer=governance_layer)
    bridge._forge_lane_module = ForgeLaneCapability(patchforge=patchforge)
    bridge._document_vision_module = DocumentVisionCapability()
    bridge._ui_vision_module = UiVisionCapability()
    bridge._audio_module = AudioAnalyzeCapability()
    bridge._video_module = VideoAnalyzeCapability()
    bridge._image_module = ImageTransformCapability()
    bridge._beatbox_module = BeatboxScoreCapability()
    bridge._speakers_module = SpeakersMixCapability()
    bridge._story_forge_audio_module = ConfiguredStoryForgeAudioModule()

    extra_specs = [
        _spec("memory", "memory_lane", "memory_list", "list", bridge._memory_lane_module, ("memory_list",)),
        _spec("workspace", "workspace_lane", "workspace_projects", "list_projects", bridge._workspace_lane_module, ("workspace_projects",)),
        _spec("action", "action_lane", "action_status", "status", bridge._action_lane_module, ("action_status",)),
        _spec("forge", "forge_lane", "forge_status", "status", bridge._forge_lane_module, ("forge_status",)),
        _spec("document_vision", "document_vision", "document_vision_extract", "extract_text", bridge._document_vision_module, ("document_vision",)),
        _spec("ui_vision", "ui_vision", "ui_vision_analyze", "analyze_screenshot", bridge._ui_vision_module, ("ui_vision",)),
        _spec("media", "audio_analyze", "audio_analyze", "analyze", bridge._audio_module, ("audio_analyze",)),
        _spec("media", "video_analyze", "video_analyze", "analyze", bridge._video_module, ("video_analyze",)),
        _spec("media", "image_transform", "image_transform", "transform", bridge._image_module, ("image_transform",)),
        _spec("beatbox", "beatbox_score", "beatbox_score", "score", bridge._beatbox_module, ("beatbox_score",)),
        _spec("speakers", "speakers_mix", "speakers_mix", "mix", bridge._speakers_module, ("speakers_mix",)),
        _spec(
            "story_forge",
            "story_forge_audio",
            "story_forge_audio",
            "run",
            bridge._story_forge_audio_module,
            ("story_forge_audio",),
        ),
    ]

    for spec in extra_specs:
        spec["handler"] = _generic_handler(bridge, spec)
        bridge._route_specs.append(spec)

    bridge._routes = {
        _normalize_name(alias): spec
        for spec in bridge._route_specs
        for alias in spec["aliases"]
    }
    bridge._selection_routes = {
        (spec["capability_id"], spec["action"]): spec for spec in bridge._route_specs
    }
    bridge._universal_adapters_attached = True


def universal_bridge_enforced(bridge: CapabilityServiceBridge) -> bool:
    return bool(getattr(bridge, "_universal_adapters_attached", False))


def _spec(
    capability_id: str,
    label: str,
    tool: str,
    action: str,
    module: Any,
    aliases: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "capability_label": label.replace("_", " ").title(),
        "capability_summary": f"Governed {label} adapter.",
        "tool": tool,
        "tool_label": tool.replace("_", " ").title(),
        "action": action,
        "action_label": action.replace("_", " ").title(),
        "module": module,
        "aliases": aliases,
        "endpoint": "/api/jarvis/capability-bridge/execute",
        "provider_modes": ("deterministic",),
        "default_provider_mode": "deterministic",
        "governance_modes": DEFAULT_GOVERNANCE_MODES,
        "default_governance_mode": "strict",
        "input_fields": (),
    }


def _generic_handler(bridge: CapabilityServiceBridge, spec: dict[str, Any]):
    def handler(
        args: dict[str, Any],
        *,
        execution_profile: dict[str, Any] | None = None,
        phase_gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = dict(args or {})
        tool = spec.get("tool", "")
        cap_id = spec.get("capability_id", "")

        # MVP wiring for non-OTEM capability bridge flows: delegate forge/evolve to live contractors if reachable.
        # This makes direct capability.execute (used by some agents/workflows) use the live services (6060/6062)
        # and records the via + results for observability, falling back to local module otherwise.
        if "forge" in tool.lower() or "forge" in cap_id.lower():
            try:
                forge_client.health()
                kind = payload.get("kind", "generate_diff")
                ctx = payload.get("context") or payload
                result = forge_client.request(kind=kind, context=dict(ctx))
                cap_res = {"ok": True, "data": result, "via": "live_forge"}
                return bridge._finalize_result(
                    spec=spec,
                    tool_result={
                        "type": spec["tool"],
                        "tool": spec["tool"],
                        "status": "completed",
                        "args": payload,
                        "result": result,
                        "via": "live_forge",
                    },
                    capability_result=cap_res,
                    response=f"{spec['tool']} completed via live Forge.",
                    execution_profile=execution_profile,
                    phase_gate=phase_gate,
                )
            except Exception:
                pass  # fall to local
        if "evolve" in tool.lower() or "evolve" in cap_id.lower():
            try:
                evolve_client.health()
                task = payload.get("task") or payload.get("goal") or "evolve"
                result = evolve_client.evolve(task=task, config=dict(payload.get("config") or {}))
                cap_res = {"ok": True, "data": result, "via": "live_evolve"}
                return bridge._finalize_result(
                    spec=spec,
                    tool_result={
                        "type": spec["tool"],
                        "tool": spec["tool"],
                        "status": "completed",
                        "args": payload,
                        "result": result,
                        "via": "live_evolve",
                    },
                    capability_result=cap_res,
                    response=f"{spec['tool']} completed via live Evolve.",
                    execution_profile=execution_profile,
                    phase_gate=phase_gate,
                )
            except Exception:
                pass  # fall to local

        capability_result = spec["module"].execute(spec["action"], payload)
        response = (
            f"{spec['tool']} completed."
            if capability_result.get("ok")
            else f"{spec['tool']} failed: {capability_result.get('message', 'error')}"
        )
        return bridge._finalize_result(
            spec=spec,
            tool_result={
                "type": spec["tool"],
                "tool": spec["tool"],
                "status": "completed" if capability_result.get("ok") else "failed",
                "args": payload,
                "result": capability_result.get("data") or {},
            },
            capability_result=capability_result,
            response=response,
            execution_profile=execution_profile,
            phase_gate=phase_gate,
        )

    return handler


GAP_COMPONENT_IDS = (
    MEMORY_LANE_COMPONENT_ID,
    WORKSPACE_LANE_COMPONENT_ID,
    ACTION_LANE_COMPONENT_ID,
    FORGE_LANE_COMPONENT_ID,
    DOCUMENT_VISION_COMPONENT_ID,
    UI_VISION_COMPONENT_ID,
    MEDIA_PROCESSOR_COMPONENT_ID,
    BEATBOX_LANE_COMPONENT_ID,
    SPEAKERS_LANE_COMPONENT_ID,
)


class ConfiguredStoryForgeAudioModule:
    """Story Forge audio capability module.

    This follows the same shape as other capability modules so that
    CapabilityServiceBridge / _spec / generic handlers can read
    .provider_name, .module_name, .supported_actions etc. on the *instance*.
    """

    module_name = "story_forge_audio"
    provider_name = "aais_story_forge"
    supported_actions = frozenset({"run"})

    def __init__(self) -> None:
        # Ensure instance attributes exist (some bridge code does getattr on instances).
        self.module_name = self.module_name
        self.provider_name = self.provider_name
        self.supported_actions = self.supported_actions

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        from src.capabilities.story_forge_audio import run_story_forge_audio_capability

        if action != "run":
            return {"ok": False, "message": f"unsupported action: {action}"}
        try:
            result = run_story_forge_audio_capability(dict(payload or {}))
            return {"ok": True, "data": result, "message": "ok"}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
