"""LLM-assisted deliberation for the Deliberation lobe."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Callable

DELIBERATION_LLM_SYSTEM = """You are the Deliberation lobe inside Nova Cortex.
Return ONLY valid JSON with this exact shape:
{
  "options": ["string"],
  "tradeoffs": [{"option": "string", "pros": "string", "cons": "string", "risk": "low|medium|high"}],
  "chosen_option": "string",
  "rationale": "string",
  "assumptions": ["string"],
  "criteria_scores": {"option": {"focus_alignment": 0.0, "risk": 0.0, "policy_fit": 0.0, "testability": 0.0, "user_goal": 0.0}}
}
criteria_scores is optional; if omitted the deterministic scorer backfills.
No markdown. No prose outside JSON. No tools. Stay bounded to the user message and focus signals."""

JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}", re.MULTILINE)

DeliberationFn = Callable[[dict[str, Any]], dict[str, Any] | None]


def build_deliberation_prompt(
    user_message: str,
    *,
    focus_artifact: dict[str, Any] | None = None,
    frame_kind: str = "decision",
) -> dict[str, str]:
    focus = dict(focus_artifact or {})
    focus_lines = [
        f"Primary focus: {focus.get('primary_focus', '')}",
        f"Focus signals: {', '.join(focus.get('focus_signals') or [])}",
        f"Frame kind: {frame_kind}",
    ]
    user = (
        f"User message:\n{user_message.strip()}\n\n"
        f"Attention focus:\n" + "\n".join(focus_lines)
    ).strip()
    return {"system": DELIBERATION_LLM_SYSTEM, "user": user}


def parse_deliberation_response(text: str) -> dict[str, Any]:
    body = (text or "").strip()
    if not body:
        raise ValueError("empty_deliberation_response")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        match = JSON_BLOCK_RE.search(body)
        if not match:
            raise ValueError("invalid_deliberation_json") from None
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("deliberation_payload_not_object")
    options = payload.get("options")
    if not isinstance(options, list) or not options:
        raise ValueError("missing_options")
    chosen = str(payload.get("chosen_option") or "").strip()
    if not chosen:
        raise ValueError("missing_chosen_option")
    tradeoffs = payload.get("tradeoffs")
    if tradeoffs is not None and not isinstance(tradeoffs, list):
        raise ValueError("tradeoffs_not_list")
    rationale = str(payload.get("rationale") or "").strip()
    if not rationale:
        raise ValueError("missing_rationale")
    assumptions = payload.get("assumptions")
    if assumptions is not None and not isinstance(assumptions, list):
        raise ValueError("assumptions_not_list")
    criteria_scores = payload.get("criteria_scores")
    if criteria_scores is not None and not isinstance(criteria_scores, dict):
        raise ValueError("criteria_scores_not_object")
    result = {
        "options": [str(item).strip() for item in options if str(item).strip()],
        "tradeoffs": tradeoffs or [],
        "chosen_option": chosen,
        "rationale": rationale,
        "assumptions": [str(item).strip() for item in (assumptions or []) if str(item).strip()],
    }
    if isinstance(criteria_scores, dict):
        result["criteria_scores"] = criteria_scores
    return result


def invoke_deliberation_provider(
    prompt: dict[str, str],
    *,
    provider_name: str | None = None,
) -> dict[str, Any] | None:
    """Call a remote-capable provider for bounded JSON deliberation."""
    from src.jarvis_protocol import JarvisMessage
    from src.provider_registry import provider_registry

    preferred = []
    if provider_name:
        preferred.append(provider_name)
    preferred.extend(["openrouter", "claude"])
    adapter = None
    chosen_name = None
    for name in preferred:
        if provider_registry.can_invoke(name):
            adapter = provider_registry.get(name)
            if adapter is not None:
                chosen_name = name
                break
    if adapter is None:
        return None

    messages = [
        JarvisMessage(role="system", content=prompt["system"]),
        JarvisMessage(role="user", content=prompt["user"]),
    ]

    async def _run() -> str:
        response = await adapter.invoke(
            messages,
            max_tokens=512,
            temperature=0.2,
            mode="fast",
        )
        if hasattr(response, "content"):
            return str(response.content or "")
        if isinstance(response, dict):
            return str(response.get("content") or response.get("text") or "")
        return str(response or "")

    try:
        text = asyncio.run(_run())
        parsed = parse_deliberation_response(text)
        parsed["commit_source"] = "llm"
        parsed["provider"] = chosen_name
        return parsed
    except Exception:
        return None


def build_session_deliberate_fn(session) -> DeliberationFn:
    """Bind deliberation LLM calls to the session's preferred provider."""

    def deliberate(prompt: dict[str, str]) -> dict[str, Any] | None:
        from src.conversation_memory import normalize_provider_identifier

        preferred = normalize_provider_identifier(
            getattr(session, "metadata", {}).get("preferred_provider"),
            default="local",
        )
        provider_name = None if preferred in {"local", "auto", ""} else preferred
        return invoke_deliberation_provider(prompt, provider_name=provider_name)

    return deliberate


def default_deliberate_fn(prompt: dict[str, str]) -> dict[str, Any] | None:
    """Default LLM deliberation; returns None to trigger deterministic fallback."""
    return invoke_deliberation_provider(prompt)


def run_deliberation_llm(
    prompt: dict[str, str],
    deliberate_fn: DeliberationFn | None = None,
) -> dict[str, Any] | None:
    fn = deliberate_fn or default_deliberate_fn
    try:
        result = fn(prompt)
    except Exception:
        return None
    if not isinstance(result, dict):
        return None
    try:
        parsed = parse_deliberation_response(json.dumps(result))
        parsed["commit_source"] = result.get("commit_source") or "llm"
        return parsed
    except Exception:
        if validate_llm_payload(result):
            result.setdefault("commit_source", "llm")
            return result
        return None


def validate_llm_payload(payload: dict[str, Any]) -> bool:
    try:
        parse_deliberation_response(json.dumps(payload))
        return True
    except Exception:
        return False
