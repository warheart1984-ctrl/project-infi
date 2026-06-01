"""Live chat generation gate — verify finalized output and resample on failure."""

from __future__ import annotations

from typing import Any, Callable

OUTPUT_VERIFICATION_PROMPT_KEY = "output_verification_prompt_block"
OUTPUT_VERIFICATION_TRACE_KEY = "output_verification_trace"
DEFAULT_MAX_RESAMPLE_ATTEMPTS = 3


def resolve_focus_from_session(session) -> dict[str, Any] | None:
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


def generation_verification_enabled(session) -> bool:
    if session.metadata.get("output_verification_resample") is False:
        return False
    turn_contract = dict(session.metadata.get("turn_contract") or {})
    return bool(
        session.metadata.get("speaking_runtime_enabled")
        or session.metadata.get("cognitive_runtime_enabled")
        or turn_contract.get("companion_turn")
        or session.metadata.get("companion_turn")
    )


def resolve_max_resample_attempts(session) -> int:
    raw = session.metadata.get("output_verification_max_attempts")
    try:
        attempts = int(raw)
    except (TypeError, ValueError):
        attempts = DEFAULT_MAX_RESAMPLE_ATTEMPTS
    return max(1, min(attempts, 5))


def verify_finalized_response(session, user_message: str, text: str) -> dict[str, Any]:
    from src.speaking_runtime import verify_reply

    focus = resolve_focus_from_session(session)
    require_citations = bool(session.metadata.get("speaking_require_citations"))
    return verify_reply(
        text,
        focus_artifact=focus,
        require_citations=require_citations,
    )


def inject_verification_correction(session, verification: dict[str, Any]) -> None:
    issues = list(verification.get("issues") or [])
    if not issues:
        session.metadata.pop(OUTPUT_VERIFICATION_PROMPT_KEY, None)
        return
    focus = resolve_focus_from_session(session) or {}
    primary = str(focus.get("primary_focus") or "").strip()
    focus_hint = f" Reflect turn focus: {primary}." if primary else ""
    session.metadata[OUTPUT_VERIFICATION_PROMPT_KEY] = (
        "Your previous draft failed governed output verification: "
        + "; ".join(issues[:6])
        + "."
        + focus_hint
        + " Regenerate a complete reply with Listen, Frame, Plan, Speak, and Check stages "
        "and an alignment check at the end."
    )


def run_generation_with_verification(
    session,
    generate_fn: Callable[[], str],
    *,
    user_message: str,
    max_attempts: int | None = None,
) -> str:
    """Rejection sampling on finalized visible text (post-Speaking wrap path)."""
    attempts_n = resolve_max_resample_attempts(session) if max_attempts is None else max(1, max_attempts)
    trace: list[dict[str, Any]] = []
    last_text = ""

    session.metadata.pop(OUTPUT_VERIFICATION_PROMPT_KEY, None)
    for attempt in range(1, attempts_n + 1):
        last_text = str(generate_fn() or "").strip()
        verification = verify_finalized_response(session, user_message, last_text)
        trace.append({"attempt": attempt, **verification})
        if verification.get("valid"):
            session.metadata[OUTPUT_VERIFICATION_TRACE_KEY] = {
                "attempts": trace,
                "final_valid": True,
                "resampled": attempt > 1,
            }
            session.metadata.pop(OUTPUT_VERIFICATION_PROMPT_KEY, None)
            return last_text
        if attempt < attempts_n:
            inject_verification_correction(session, verification)

    session.metadata[OUTPUT_VERIFICATION_TRACE_KEY] = {
        "attempts": trace,
        "final_valid": False,
        "exhausted": True,
        "resampled": attempts_n > 1,
    }
    return last_text


def authoritative_emit_or_halt(
    session,
    user_message: str,
    text: str,
    *,
    max_attempts: int = 3,
    regenerate_fn=None,
) -> tuple[str, dict[str, Any]]:
    """
    Authoritative generation gate — refuse to emit unless verification passes.
    When regenerate_fn is provided, resample up to max_attempts.
    """
    attempts_n = max(1, min(int(max_attempts or 3), 5))
    trace: list[dict[str, Any]] = []
    current = str(text or "").strip()

    for attempt in range(1, attempts_n + 1):
        verification = verify_finalized_response(session, user_message, current)
        trace.append({"attempt": attempt, **verification})
        session.metadata["speaking_validation"] = verification
        if verification.get("valid"):
            session.metadata["generation_gate"] = {
                "authoritative": True,
                "attempts": trace,
                "final_valid": True,
                "emitted": True,
            }
            return current, session.metadata["generation_gate"]

        if regenerate_fn is not None and attempt < attempts_n:
            inject_verification_correction(session, verification)
            current = str(regenerate_fn() or "").strip()
            continue

        session.metadata["generation_gate"] = {
            "authoritative": True,
            "attempts": trace,
            "final_valid": False,
            "emitted": False,
            "halt_reason": "generation_gate_failed",
        }
        return "", session.metadata["generation_gate"]

    session.metadata["generation_gate"] = {
        "authoritative": True,
        "attempts": trace,
        "final_valid": False,
        "emitted": False,
    }
    return "", session.metadata["generation_gate"]
