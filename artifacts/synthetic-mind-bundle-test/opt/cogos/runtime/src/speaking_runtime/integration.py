"""Jarvis / AAIS integration for the Speaking Runtime."""

from __future__ import annotations

import re
from typing import Any

from src.speaking_runtime import (
    SPEAKING_RUNTIME_ID,
    build_frame_utterance,
    build_listen_utterance,
    build_plan_utterance,
    build_system_prompt,
    compose_reply,
    speaking_runtime_spec,
    validate_reply,
    verify_reply,
    SpeakingRuntimeSession,
)

SPEAKING_RUNTIME_TRIGGER_RE = re.compile(
    r"\b(?:use\s+)?speaking\s+runtime\b",
    re.IGNORECASE,
)


def resolve_speaking_runtime_enabled(
    session,
    request_payload: dict[str, Any] | None,
    user_message: str,
    *,
    companion_turn: bool = False,
    direct_challenge: bool = False,
    local_fallback: bool = False,
) -> bool:
    """Resolve whether this turn runs under the Speaking Runtime contract."""
    if companion_turn or direct_challenge or local_fallback:
        session.metadata["speaking_runtime_enabled"] = False
        return False

    payload = dict(request_payload or {})
    if "speaking_runtime" in payload:
        enabled = bool(payload["speaking_runtime"])
        session.metadata["speaking_runtime_enabled"] = enabled
        _sync_turn_contract(session, enabled)
        return enabled

    if session.metadata.get("speaking_runtime_enabled"):
        return True

    if SPEAKING_RUNTIME_TRIGGER_RE.search(user_message or ""):
        session.metadata["speaking_runtime_enabled"] = True
        _sync_turn_contract(session, True)
        return True

    return False


def speaking_runtime_active(session) -> bool:
    return bool(session.metadata.get("speaking_runtime_enabled"))


def build_speaking_runtime_prompt_block(session) -> dict[str, Any] | None:
    """Return a Jarvis prompt block when Speaking Runtime is active for this turn."""
    if not speaking_runtime_active(session):
        return None
    return {
        "identity": "speaking_runtime",
        "role": "system",
        "content": build_system_prompt(),
        "channel": "instruction",
        "source": "speaking_runtime",
        "priority": 22,
        "required": True,
    }


def apply_speaking_runtime_finalization(
    session,
    user_message: str,
    response_text: str,
    *,
    response_trace: dict[str, Any] | None = None,
) -> str:
    """Wrap or validate visible replies when Speaking Runtime is active."""
    if not speaking_runtime_active(session):
        return response_text

    body = str(response_text or "").strip()
    focus_artifact = _resolve_focus_artifact(session)
    require_citations = bool(session.metadata.get("speaking_require_citations"))
    validation = verify_reply(
        body,
        focus_artifact=focus_artifact,
        require_citations=require_citations,
    )
    if validation["valid"]:
        trace_payload = _build_trace_payload(
            wrapped=False,
            validation=validation,
            runtime_session=None,
        )
        _record_speaking_runtime_trace(session, response_trace, trace_payload)
        return body

    runtime_session = SpeakingRuntimeSession(user_message=user_message)
    build_listen_utterance(runtime_session)
    build_frame_utterance(runtime_session)
    build_plan_utterance(runtime_session)
    wrapped = compose_reply(runtime_session, body)
    validation_after = verify_reply(
        wrapped,
        focus_artifact=focus_artifact,
        require_citations=require_citations,
    )
    trace_payload = _build_trace_payload(
        wrapped=True,
        validation=validation_after,
        runtime_session=runtime_session,
        pre_wrap_issues=list(validation.get("issues") or []),
    )
    _record_speaking_runtime_trace(session, response_trace, trace_payload)
    session.metadata["speaking_runtime_trace"] = runtime_session.to_dict()
    return wrapped


def summarize_speaking_runtime_state(session) -> dict[str, Any] | None:
    """Project session speaking-runtime state for API payloads."""
    if not speaking_runtime_active(session) and not session.metadata.get("speaking_runtime_trace"):
        return None
    trace = dict(session.metadata.get("speaking_runtime_trace") or {})
    summary = {
        "enabled": speaking_runtime_active(session),
        "protocol_id": SPEAKING_RUNTIME_ID,
        "frame_kind": trace.get("frame_kind"),
        "goal": trace.get("goal"),
        "session_id": trace.get("session_id"),
        "stage_count": len(trace.get("utterances") or []),
    }
    return {key: value for key, value in summary.items() if value is not None}


def _resolve_focus_artifact(session) -> dict[str, Any] | None:
    artifacts = session.metadata.get("cognitive_runtime_artifacts")
    if isinstance(artifacts, dict):
        focus = artifacts.get("focus_artifact")
        if isinstance(focus, dict):
            return focus
    cog = session.metadata.get("nova_cognitive_session")
    if isinstance(cog, dict):
        cog_artifacts = cog.get("artifacts") or {}
        if isinstance(cog_artifacts, dict):
            focus = cog_artifacts.get("focus_artifact")
            if isinstance(focus, dict):
                return focus
    return None


def _sync_turn_contract(session, enabled: bool) -> None:
    turn_contract = dict(session.metadata.get("turn_contract") or {})
    turn_contract["speaking_runtime_enabled"] = bool(enabled)
    session.metadata["turn_contract"] = turn_contract


def _build_trace_payload(
    *,
    wrapped: bool,
    validation: dict[str, Any],
    runtime_session: SpeakingRuntimeSession | None,
    pre_wrap_issues: list[str] | None = None,
) -> dict[str, Any]:
    payload = {
        "protocol_id": SPEAKING_RUNTIME_ID,
        "wrapped": wrapped,
        "valid": bool(validation.get("valid")),
        "issues": list(validation.get("issues") or []),
        "stages_found": list(validation.get("stages_found") or []),
        "spec": speaking_runtime_spec(),
    }
    if pre_wrap_issues:
        payload["pre_wrap_issues"] = list(pre_wrap_issues)
    if runtime_session is not None:
        payload["runtime_session"] = runtime_session.to_dict()
    return payload


def _record_speaking_runtime_trace(
    session,
    response_trace: dict[str, Any] | None,
    trace_payload: dict[str, Any],
) -> None:
    session.metadata["speaking_runtime_trace"] = dict(trace_payload.get("runtime_session") or {})
    summary = {
        "enabled": True,
        "wrapped": trace_payload.get("wrapped"),
        "valid": trace_payload.get("valid"),
        "issues": trace_payload.get("issues"),
        "stages_found": trace_payload.get("stages_found"),
        "protocol_id": SPEAKING_RUNTIME_ID,
    }
    session.metadata["speaking_runtime_summary"] = summary
    if isinstance(response_trace, dict):
        response_trace["speaking_runtime"] = dict(trace_payload)
