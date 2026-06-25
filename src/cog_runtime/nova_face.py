"""Nova Face — companion surface bridge to Nova Cortex and Tri-Core."""

# Mythic: Nova Face Organ
# Engineering: NovaFaceEngine
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.conversation_memory import companion_lane_identity, normalize_response_mode
from src.cog_runtime.memory import normalize_cortex_memory_cues
from src.cog_runtime.nova import (
    NOVA_CORTEX_ID,
    NovaCognitiveSession,
    configure_nova_cognitive_turn,
)


NOVA_FACE_BRIDGE_ID = "nova.face.bridge"
NOVA_FACE_BRIDGE_VERSION = "1.0"
TRI_CORE_AUTHORITY = "tri_core"


@dataclass(slots=True)
class NovaFaceEnvelope:
    """Visible companion surface for one turn."""

    face_id: str
    label: str
    response_mode: str
    tone: str
    companion_turn: bool
    scope: str
    authority_lane: str = TRI_CORE_AUTHORITY
    surface_priority: str = "delegated_surface"
    self_description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "face_id": self.face_id,
            "label": self.label,
            "response_mode": self.response_mode,
            "tone": self.tone,
            "companion_turn": self.companion_turn,
            "scope": self.scope,
            "authority_lane": self.authority_lane,
            "surface_priority": self.surface_priority,
            "self_description": self.self_description,
        }


@dataclass
class NovaFaceBridgeResult:
    """End-to-end binding: Face → Cortex → Tri-Core."""

    face: NovaFaceEnvelope
    cortex_session: NovaCognitiveSession | None
    tri_core_binding: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bridge_id": NOVA_FACE_BRIDGE_ID,
            "bridge_version": NOVA_FACE_BRIDGE_VERSION,
            "face": self.face.to_dict(),
            "cortex": self.cortex_session.to_dict() if self.cortex_session else None,
            "tri_core": dict(self.tri_core_binding),
            "pipeline": ["nova_face", "nova_cortex", "tri_core"],
        }


def resolve_nova_face(
    *,
    persona_mode: str | None,
    response_mode: str | None,
    companion_turn: bool,
    surface_profile: dict[str, Any] | None = None,
) -> NovaFaceEnvelope:
    """Resolve the active Nova face from session persona and companion lane."""
    identity = companion_lane_identity(persona_mode, response_mode)
    profile = dict(surface_profile or {})
    if profile:
        continuity = dict(profile.get("continuity_profile") or {})
        return NovaFaceEnvelope(
            face_id=str(profile.get("identity") or identity or "jarvis"),
            label=str(profile.get("label") or identity or "Jarvis"),
            response_mode=normalize_response_mode(
                profile.get("response_mode") or response_mode or "operator"
            ),
            tone=str(continuity.get("tone") or "neutral"),
            companion_turn=companion_turn,
            scope=str(continuity.get("scope") or identity or "operator"),
            self_description=str(continuity.get("self_description") or ""),
        )

    if companion_turn and identity:
        return NovaFaceEnvelope(
            face_id=identity,
            label=identity.replace("_", " ").title(),
            response_mode=normalize_response_mode(response_mode or "tiny"),
            tone="companion",
            companion_turn=True,
            scope=identity,
        )

    return NovaFaceEnvelope(
        face_id="jarvis",
        label="Jarvis",
        response_mode=normalize_response_mode(response_mode or "operator"),
        tone="operator",
        companion_turn=False,
        scope="operator_task",
        surface_priority="authority_surface",
        self_description="Jarvis remains the visible surface and authority core.",
    )


def build_face_to_cortex_context(
    face: NovaFaceEnvelope,
    *,
    session_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Translate Nova Face into Nova Cortex turn context."""
    metadata = dict(session_metadata or {})
    return {
        "nova_face": face.to_dict(),
        "face_id": face.face_id,
        "companion_turn": face.companion_turn,
        "response_mode": face.response_mode,
        "speaking_runtime_enabled": True if face.companion_turn else bool(
            metadata.get("speaking_runtime_enabled")
        ),
        "require_speaking": face.companion_turn or bool(metadata.get("speaking_runtime_enabled")),
        "memory_cues": normalize_cortex_memory_cues(
            metadata.get("memory_board_snapshot") or metadata.get("memory_board") or metadata,
            companion_turn=face.companion_turn,
            metadata=metadata,
        ),
        "cognitive_runtime_enabled": metadata.get("cognitive_runtime_enabled", face.companion_turn),
        "nova_face": face.to_dict(),
        "deliberation_llm": bool(metadata.get("deliberation_llm_enabled")),
        "policy_status": dict(metadata.get("policy_status") or {}),
        "policy_posture": (metadata.get("policy_status") or {}).get("posture"),
    }


def build_tri_core_binding(
    face: NovaFaceEnvelope,
    cortex_session: NovaCognitiveSession | None,
) -> dict[str, Any]:
    """Upward binding from Nova Face/Cortex into Tri-Core authority plane."""
    binding = {
        "authority_lane": TRI_CORE_AUTHORITY,
        "routing_authority": TRI_CORE_AUTHORITY,
        "state_authority": TRI_CORE_AUTHORITY,
        "surface_identity": face.face_id,
        "surface_priority": face.surface_priority,
        "surface_replaces_authority": False,
        "nova_cortex_id": NOVA_CORTEX_ID,
        "companion_turn": face.companion_turn,
        "authority_summary": (
            f"{face.label} leads the companion surface; Tri-Core retains routing, state, and safety."
            if face.companion_turn
            else "Tri-Core is both visible surface and authority for this turn."
        ),
    }
    if cortex_session is not None:
        binding.update(
            {
                "nova_cortex_session_id": cortex_session.session_id,
                "active_cognitive_runtimes": list(cortex_session.active_runtimes),
                "cortex_frame_kind": cortex_session.frame_kind,
                "cortex_artifact_keys": sorted(cortex_session.artifacts.keys()),
            }
        )
    return binding


def bridge_nova_face_to_cortex_and_tri_core(
    session,
    request_payload: dict[str, Any] | None,
    user_message: str,
    *,
    companion_turn: bool = False,
    surface_profile: dict[str, Any] | None = None,
) -> NovaFaceBridgeResult | None:
    """Run Face → Cortex → Tri-Core bridge for the active turn."""
    metadata = getattr(session, "metadata", {}) or {}
    face = resolve_nova_face(
        persona_mode=metadata.get("persona_mode"),
        response_mode=metadata.get("response_mode") or metadata.get("requested_response_mode"),
        companion_turn=companion_turn,
        surface_profile=surface_profile,
    )
    session.metadata["nova_face"] = face.to_dict()

    payload = dict(request_payload or {})
    if "cognitive_runtime" in payload and not payload.get("cognitive_runtime"):
        session.metadata["cognitive_runtime_enabled"] = False
        binding = build_tri_core_binding(face, None)
        session.metadata["tri_core_binding"] = binding
        session.metadata["nova_face_bridge"] = NovaFaceBridgeResult(face, None, binding).to_dict()
        return NovaFaceBridgeResult(face, None, binding)

    cortex_context = build_face_to_cortex_context(face, session_metadata=metadata)
    session.metadata["cognitive_runtime_enabled"] = bool(
        payload.get("cognitive_runtime", companion_turn)
    )
    deliberation_llm = bool(
        payload.get("deliberation_llm", companion_turn)
    )
    session.metadata["deliberation_llm_enabled"] = deliberation_llm
    if deliberation_llm and payload.get("deliberate_fn"):
        session.metadata["deliberate_fn"] = payload.get("deliberate_fn")
    elif deliberation_llm and session.metadata.get("deliberate_fn") is None:
        from src.cog_runtime.deliberation_llm import build_session_deliberate_fn

        session.metadata["deliberate_fn"] = build_session_deliberate_fn(session)
    if not session.metadata["cognitive_runtime_enabled"]:
        binding = build_tri_core_binding(face, None)
        session.metadata["tri_core_binding"] = binding
        session.metadata["nova_face_bridge"] = NovaFaceBridgeResult(face, None, binding).to_dict()
        return NovaFaceBridgeResult(face, None, binding)

    cortex_session = configure_nova_cognitive_turn(
        session,
        {**payload, "cognitive_runtime": True},
        user_message,
        companion_turn=companion_turn,
    )
    binding = build_tri_core_binding(face, cortex_session)
    session.metadata["tri_core_binding"] = binding
    bridge_payload = NovaFaceBridgeResult(face, cortex_session, binding).to_dict()
    session.metadata["nova_face_bridge"] = bridge_payload

    turn_contract = dict(session.metadata.get("turn_contract") or {})
    turn_contract["nova_face_id"] = face.face_id
    turn_contract["tri_core_binding"] = binding
    session.metadata["turn_contract"] = turn_contract

    if cortex_session is not None:
        cortex_session.context.update(cortex_context)
    return NovaFaceBridgeResult(face, cortex_session, binding)


def summarize_nova_face_bridge(session) -> dict[str, Any] | None:
    """Project bridge state for API payloads."""
    bridge = session.metadata.get("nova_face_bridge")
    if isinstance(bridge, dict):
        return {
            "face_id": (bridge.get("face") or {}).get("face_id"),
            "pipeline": bridge.get("pipeline"),
            "active_cognitive_runtimes": (bridge.get("tri_core") or {}).get(
                "active_cognitive_runtimes"
            ),
            "nova_cortex_session_id": (bridge.get("tri_core") or {}).get(
                "nova_cortex_session_id"
            ),
        }
    face = session.metadata.get("nova_face")
    if isinstance(face, dict):
        return {"face_id": face.get("face_id")}
    return None


# Deprecated aliases (Jarvis Core → Tri-Core thalamus identity)
JARVIS_CORE_AUTHORITY = TRI_CORE_AUTHORITY
build_jarvis_core_binding = build_tri_core_binding
bridge_nova_face_to_cortex_and_jarvis = bridge_nova_face_to_cortex_and_tri_core
