"""Chat-turn UL substrate and Project Infi admission with CISIV staging."""

from __future__ import annotations

from typing import Any

from src.cisiv import CISIV_STAGE_SEQUENCE, normalize_cisiv_stage
from src.aais_ul_substrate import attach_ul_substrate

CHAT_TURN_SURFACE = "chat_turn"
CHAT_TURN_CONTRACT_VERSION = "aais.chat_turn_governance.v1"


def infer_chat_turn_cisiv_stage(*, phase: str = "generate") -> str:
    """Map one chat-turn phase to a canonical CISIV stage."""
    mapping = {
        "ingress": "concept",
        "bridge": "identity",
        "gather": "structure",
        "generate": "implementation",
        "admit": "verification",
    }
    return normalize_cisiv_stage(mapping.get(str(phase or "").strip().lower(), "implementation"))


def provider_messages_from_preview(preview: dict[str, Any]) -> list[Any]:
    """Convert one modular preview into provider-facing Jarvis messages."""
    from src.jarvis_protocol import JarvisMessage

    messages: list[Any] = []
    for raw in list(preview.get("provider_messages") or []):
        if isinstance(raw, JarvisMessage):
            messages.append(raw)
        else:
            messages.append(JarvisMessage.from_dict(dict(raw)))
    return messages


def _bounded_response_trace_for_preview(response_trace: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return a JSON-safe response trace summary for modular preview metadata."""
    if not isinstance(response_trace, dict):
        return None
    return {
        key: response_trace.get(key)
        for key in (
            "contract",
            "reasoning_objective",
            "plan_summary",
            "model_route",
            "governed_pipeline",
        )
        if response_trace.get(key) is not None
    }


def _bounded_ul_trace_for_export(ul_trace: dict[str, Any] | None) -> dict[str, Any]:
    """Strip cyclic metadata from one modular UL trace before JSON export."""
    if not isinstance(ul_trace, dict):
        return {}
    bounded_payloads: list[dict[str, Any]] = []
    for item in list(ul_trace.get("payloads") or []):
        if not isinstance(item, dict):
            continue
        cleaned = dict(item)
        metadata = dict(cleaned.get("metadata") or {})
        metadata.pop("response_trace", None)
        if metadata:
            cleaned["metadata"] = metadata
        else:
            cleaned.pop("metadata", None)
        bounded_payloads.append(cleaned)
    return {
        "count": ul_trace.get("count"),
        "sections": list(ul_trace.get("sections") or []),
        "payloads": bounded_payloads,
    }


def _bounded_modular_preview_for_export(preview: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return one modular preview safe for chat runtime JSON payloads."""
    if not isinstance(preview, dict):
        return preview
    safe = dict(preview)
    safe["ul_trace"] = _bounded_ul_trace_for_export(preview.get("ul_trace"))
    provider_payload = dict(preview.get("provider_payload") or {})
    metadata = dict(provider_payload.get("metadata") or {})
    metadata.pop("response_trace", None)
    if metadata:
        provider_payload["metadata"] = metadata
    else:
        provider_payload.pop("metadata", None)
    if provider_payload:
        safe["provider_payload"] = provider_payload
    return safe


def attach_modular_preview_to_response_trace(
    response_trace: dict[str, Any] | None,
    preview: dict[str, Any],
) -> None:
    """Mirror modular preview doctrine onto the active response trace."""
    if not isinstance(response_trace, dict):
        return
    response_trace["modular_preview"] = {
        "context_modules": list(preview.get("context_modules") or []),
        "pipeline_mode": preview.get("pipeline_mode"),
        "doctrine_summary": preview.get("doctrine_summary"),
        "guardrail_evaluation": preview.get("guardrail_evaluation"),
        "ul_trace": {
            "count": (preview.get("ul_trace") or {}).get("count"),
            "sections": list((preview.get("ul_trace") or {}).get("sections") or []),
        },
    }


def prepare_chat_turn_modular_package(
    session,
    *,
    protocol_messages: list[dict[str, Any]] | None,
    model: str,
    stream: bool,
    temperature: float,
    max_tokens: int,
    mode: str | None = None,
    tool_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one modular preview package for both local and remote generation."""
    preview = build_and_store_chat_turn_preview(
        session,
        model=model,
        messages=protocol_messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        mode=mode,
        tool_result=tool_result,
    )
    return {
        "preview": preview,
        "provider_messages": provider_messages_from_preview(preview),
    }


def build_chat_turn_modular_preview(
    session,
    *,
    model: str,
    messages: list[dict[str, Any]] | None,
    stream: bool,
    temperature: float,
    max_tokens: int,
    mode: str | None = None,
    tool_result: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the modular provider preview for one live chat turn."""
    from src.jarvis_modular import build_modular_provider_preview

    turn_metadata = dict(metadata or {})
    turn_metadata.setdefault("session_id", session.session_id)
    turn_metadata.setdefault("cisiv_stage", infer_chat_turn_cisiv_stage(phase="generate"))
    turn_metadata.setdefault("current_goal", getattr(getattr(session, "spiral_state", None), "current_goal", None))
    bounded_trace = _bounded_response_trace_for_preview(session.metadata.get("response_trace"))
    if bounded_trace:
        turn_metadata.setdefault("response_trace", bounded_trace)
    turn_metadata.setdefault("workspace_context", session.metadata.get("workspace_context"))
    turn_metadata.setdefault("cognitive_bridge", session.metadata.get("cognitive_bridge"))
    turn_metadata.setdefault("mission_board", session.metadata.get("mission_board"))
    turn_metadata.setdefault("model_route", session.metadata.get("model_route"))
    turn_metadata.setdefault("cognitive_runtime_enabled", session.metadata.get("cognitive_runtime_enabled"))
    turn_metadata.setdefault("nova_intent", session.metadata.get("nova_intent"))
    turn_metadata.setdefault("nova_narrative", session.metadata.get("nova_narrative"))
    turn_metadata.setdefault("cortex_arc", session.metadata.get("cortex_arc"))
    turn_metadata.setdefault("cognitive_runtime_artifacts", session.metadata.get("cognitive_runtime_artifacts"))
    turn_metadata.setdefault("nova_cognitive_session", session.metadata.get("nova_cognitive_session"))

    return build_modular_provider_preview(
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        mode=mode,
        tool_result=tool_result,
        metadata=turn_metadata,
    )


def store_chat_turn_modular_preview(session, preview: dict[str, Any]) -> dict[str, Any]:
    """Persist modular preview and UL trace on the active session."""
    session.metadata["modular_preview"] = dict(preview)
    ul_trace = dict(preview.get("ul_trace") or {})
    if ul_trace:
        session.metadata["ul_snapshot"] = ul_trace
    session.metadata["cisiv_stage"] = infer_chat_turn_cisiv_stage(phase="generate")
    return preview


def build_and_store_chat_turn_preview(
    session,
    *,
    model: str,
    messages: list[dict[str, Any]] | None,
    stream: bool,
    temperature: float,
    max_tokens: int,
    mode: str | None = None,
    tool_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    preview = build_chat_turn_modular_preview(
        session,
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        mode=mode,
        tool_result=tool_result,
    )
    return store_chat_turn_modular_preview(session, preview)


def _chat_turn_law():
    from src.jarvis_operator import jarvis_operator

    return jarvis_operator.project_infi_law


def _mirror_chat_turn_admission_trace(
    response_trace: dict[str, Any] | None,
    *,
    governed_status: str,
    truthful: bool,
    blocked: bool,
) -> None:
    """Record one bounded admission summary on the active response trace."""
    if not isinstance(response_trace, dict):
        return
    response_trace["chat_turn_admission"] = {
        "surface": CHAT_TURN_SURFACE,
        "contract_version": CHAT_TURN_CONTRACT_VERSION,
        "cisiv_stage": infer_chat_turn_cisiv_stage(phase="admit"),
        "governed_status": governed_status,
        "truthful": bool(truthful),
        "blocked": bool(blocked),
    }


def finalize_chat_turn_admission(
    session,
    *,
    user_message: str,
    response_text: str,
    response_trace: dict[str, Any] | None = None,
    tool_result: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """Pass one ordinary chat reply through Project Infi admission with CISIV verification."""
    project_infi_law = _chat_turn_law()
    bridge = dict(session.metadata.get("cognitive_bridge") or {})
    modular_preview = dict(session.metadata.get("modular_preview") or {})
    ul_trace = dict(session.metadata.get("ul_snapshot") or modular_preview.get("ul_trace") or {})
    details = {
        "contract_version": CHAT_TURN_CONTRACT_VERSION,
        "persona_mode": session.metadata.get("persona_mode"),
        "response_mode": session.metadata.get("response_mode"),
        "bridge_decision": bridge.get("decision"),
        "bridge_status": bridge.get("status"),
        "modular_preview_sections": list(ul_trace.get("sections") or []),
        "modular_preview_count": int(ul_trace.get("count") or 0),
        "user_message_preview": " ".join(str(user_message or "").split())[:180],
        "response_preview": " ".join(str(response_text or "").split())[:220],
        "tool_type": (tool_result or {}).get("type"),
        "cisiv_stage_sequence": list(CISIV_STAGE_SEQUENCE),
    }
    if response_trace:
        details["response_contract"] = response_trace.get("contract")
        details["model_route"] = response_trace.get("model_route")

    contract, ul_snapshot, _ = project_infi_law.require_contract(
        surface=CHAT_TURN_SURFACE,
        action_id="chat_reply",
        actor_id="jarvis_chat_runtime",
        actor_role="system",
        session_id=session.session_id,
        target=f"chat_session:{session.session_id}",
        repo_change=False,
        verification_plan=None,
        run_id=None,
        cisiv_stage=infer_chat_turn_cisiv_stage(phase="admit"),
        details=details,
    )
    law_enforcement, law_event_log = project_infi_law.finalize_runtime_action(
        contract,
        action_status="completed",
        summary=response_text,
        actor_id="jarvis_chat_runtime",
        actor_role="system",
        details={
            "response_mode": session.metadata.get("response_mode"),
            "bridge_decision": bridge.get("decision"),
            "cisiv_stage": infer_chat_turn_cisiv_stage(phase="admit"),
        },
    )
    session.metadata["law_enforcement"] = law_enforcement
    session.metadata["ul_snapshot"] = ul_snapshot or ul_trace
    session.metadata["law_event_log"] = law_event_log
    session.metadata["cisiv_stage"] = infer_chat_turn_cisiv_stage(phase="admit")

    governed_status = str((law_enforcement.get("governed_cycle") or {}).get("status") or "").strip().lower()
    truthful = bool((law_enforcement.get("governed_cycle") or {}).get("truthful"))
    admitted = governed_status in {"success", "partial", "overload"}
    _mirror_chat_turn_admission_trace(
        response_trace,
        governed_status=governed_status,
        truthful=truthful,
        blocked=not admitted,
    )
    if admitted:
        return response_text, None

    blocked_message = (
        ((law_enforcement.get("project_infi_layers") or {}).get("outcome") or {}).get("detail")
        or "Jarvis held the reply because it did not pass governed final-truth admission."
    )
    return blocked_message, {
        "error": blocked_message,
        "law_enforcement": law_enforcement,
        "cisiv_stage": session.metadata.get("cisiv_stage"),
        "status_code": 409,
    }


def apply_chat_turn_admission_block(session, blocked_payload: dict[str, Any] | None) -> None:
    """Merge one admission block payload onto the active session before runtime export."""
    if not isinstance(blocked_payload, dict):
        return
    if blocked_payload.get("law_enforcement") is not None:
        session.metadata["law_enforcement"] = blocked_payload["law_enforcement"]
    if blocked_payload.get("cisiv_stage") is not None:
        session.metadata["cisiv_stage"] = blocked_payload["cisiv_stage"]


def build_chat_runtime_ul_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a chat-runtime UL envelope from bridge, pipeline, and optional snapshots."""
    from src.aais_ul_substrate import aais_ul_substrate

    response_trace = dict(payload.get("response_trace") or {})
    governed_pipeline = dict(response_trace.get("governed_pipeline") or {})
    cognitive_bridge = dict(payload.get("cognitive_bridge") or {})
    ingress: list[dict[str, Any]] = []

    ul_snapshot = payload.get("ul_snapshot")
    if isinstance(ul_snapshot, dict) and ul_snapshot:
        ingress.append(dict(ul_snapshot))

    modular_preview = payload.get("modular_preview")
    if isinstance(modular_preview, dict) and modular_preview:
        ingress.append(dict(modular_preview))

    provider_preview = None
    if isinstance(modular_preview, dict):
        candidate = modular_preview.get("provider_payload")
        if isinstance(candidate, dict) and candidate.get("messages") and candidate.get("model"):
            provider_preview = candidate

    return aais_ul_substrate.build_envelope(
        bridge_results=[cognitive_bridge] if cognitive_bridge.get("bridge_id") else None,
        pipeline=governed_pipeline if governed_pipeline.get("protocol_id") else None,
        provider_preview=provider_preview,
        ingress=ingress or None,
    )


def wrap_chat_runtime_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach UL substrate envelope to one chat runtime payload."""
    bounded_preview = _bounded_modular_preview_for_export(payload.get("modular_preview"))
    envelope_source = dict(payload)
    if bounded_preview is not None:
        envelope_source["modular_preview"] = bounded_preview
    envelope = build_chat_runtime_ul_envelope(envelope_source)
    wrapped = dict(payload)
    wrapped["ul_substrate"] = envelope
    wrapped["ul_trace"] = envelope["ul_trace"]
    if bounded_preview is not None:
        if bounded_preview and not bounded_preview.get("ul_substrate"):
            wrapped["modular_preview"] = attach_ul_substrate(dict(bounded_preview))
        else:
            wrapped["modular_preview"] = bounded_preview
    return wrapped
