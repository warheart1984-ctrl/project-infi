"""Provider-aware prompt estimation and dispatch budgeting helpers."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from typing import Any

from src.jarvis_protocol import JarvisMessage


def _normalize_provider(value: str | None) -> str:
    cleaned = " ".join(str(value or "").strip().lower().split()).replace("-", "_")
    return cleaned or "local"


def _estimate_text_tokens(value: Any) -> int:
    normalized = " ".join(str(value or "").split()).strip()
    if not normalized:
        return 0
    return max(1, (len(normalized) + 3) // 4)


def _normalize_messages(messages: list[JarvisMessage | dict[str, Any]] | None) -> list[JarvisMessage]:
    normalized: list[JarvisMessage] = []
    for message in messages or []:
        if isinstance(message, JarvisMessage):
            normalized.append(message)
        elif isinstance(message, dict):
            normalized.append(JarvisMessage.from_dict(message))
    return normalized


def _estimate_openai_compatible_prompt_tokens(
    provider_id: str,
    messages: list[JarvisMessage],
) -> dict[str, Any]:
    prompt_tokens = 2
    for message in messages:
        payload = message.to_provider_message()
        prompt_tokens += 4
        prompt_tokens += _estimate_text_tokens(payload.get("role"))
        prompt_tokens += _estimate_text_tokens(payload.get("content"))
        if message.name:
            prompt_tokens += _estimate_text_tokens(message.name)
    return _wrap_ul_payload({
        "provider": provider_id,
        "prompt_tokens": int(prompt_tokens),
        "estimator": "openai_compatible_message_heuristic",
        "exact": False,
        "message_count": len(messages),
    })


def _estimate_claude_prompt_tokens(messages: list[JarvisMessage]) -> dict[str, Any]:
    system_chunks: list[str] = []
    anthropic_messages: list[dict[str, Any]] = []
    for message in messages:
        if str(message.role or "").strip().lower() == "system":
            if str(message.content or "").strip():
                system_chunks.append(str(message.content))
            continue
        anthropic_messages.append(message.to_anthropic())

    prompt_tokens = 2
    if system_chunks:
        prompt_tokens += 12 + _estimate_text_tokens("\n\n".join(system_chunks))
    for message in anthropic_messages:
        prompt_tokens += 3
        prompt_tokens += _estimate_text_tokens(message.get("content"))

    return _wrap_ul_payload({
        "provider": "claude",
        "prompt_tokens": int(prompt_tokens),
        "estimator": "anthropic_message_heuristic",
        "exact": False,
        "message_count": len(messages),
        "system_message_count": len(system_chunks),
    })


def estimate_provider_prompt_tokens(
    provider_id: str | None,
    messages: list[JarvisMessage | dict[str, Any]] | None,
    *,
    provider_model: str | None = None,
) -> dict[str, Any]:
    """Estimate prompt tokens for one provider dispatch in a stable shape."""

    normalized_provider = _normalize_provider(provider_id)
    normalized_messages = _normalize_messages(messages)
    if normalized_provider == "claude":
        report = _estimate_claude_prompt_tokens(normalized_messages)
    else:
        report = _estimate_openai_compatible_prompt_tokens(normalized_provider, normalized_messages)
    report["provider_model"] = str(provider_model or "").strip() or None
    return _wrap_ul_payload(report)


def resolve_remote_output_budget(
    *,
    provider_id: str | None,
    provider_model: str | None,
    messages: list[JarvisMessage | dict[str, Any]] | None,
    requested_output_budget: int,
    prompt_token_budget: int,
    reply_budget_floor: int,
) -> dict[str, Any]:
    """Clamp remote output budget if the real provider prompt shape exceeds the planned budget."""

    requested_output_budget = max(32, int(requested_output_budget or 0))
    prompt_token_budget = max(0, int(prompt_token_budget or 0))
    reply_budget_floor = max(32, int(reply_budget_floor or 0))
    estimate = estimate_provider_prompt_tokens(
        provider_id,
        messages,
        provider_model=provider_model,
    )
    prompt_tokens_estimate = int(estimate.get("prompt_tokens") or 0)
    prompt_overflow_tokens = max(0, prompt_tokens_estimate - prompt_token_budget)
    effective_output_budget = max(32, requested_output_budget - prompt_overflow_tokens)
    return _wrap_ul_payload({
        "resolved_provider": _normalize_provider(provider_id),
        "provider_model": str(provider_model or "").strip() or None,
        "prompt_tokens_estimate": prompt_tokens_estimate,
        "prompt_tokens_estimator": str(estimate.get("estimator") or "unknown"),
        "prompt_tokens_exact": bool(estimate.get("exact")),
        "message_count": int(estimate.get("message_count") or 0),
        "prompt_token_budget": prompt_token_budget,
        "prompt_overflow_tokens": prompt_overflow_tokens,
        "requested_output_token_budget": requested_output_budget,
        "effective_output_token_budget": int(effective_output_budget),
        "reply_budget_floor": reply_budget_floor,
        "reply_floor_preserved": bool(effective_output_budget >= reply_budget_floor),
        "output_budget_clamped": bool(effective_output_budget < requested_output_budget),
    })
