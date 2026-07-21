"""Read-only Intent consult helpers for cortex lobes."""

from __future__ import annotations

from typing import Any

PULL_OPTION_HINTS: dict[str, tuple[str, ...]] = {
    "safety": ("safe", "defer", "verify", "cautious", "slow", "rollback"),
    "exploration": ("explore", "compare", "new", "fast", "direct", "experimental", "pilot"),
    "certainty": ("commit", "direct", "default", "decide", "close"),
    "curiosity": ("compare", "gather", "defer", "research", "learn"),
    "comfort": ("stable", "defer", "minimal", "hold", "pause"),
    "growth": ("stretch", "improve", "expand", "adjust", "tighten"),
    "present": ("now", "direct", "immediate", "this turn"),
    "future": ("long", "horizon", "continue", "arc", "next session"),
    "self": ("operator", "user", "focus"),
    "others": ("policy", "governance", "constraint", "external"),
}

OPPOSING_PULLS: tuple[tuple[str, str], ...] = (
    ("safety", "exploration"),
    ("comfort", "growth"),
    ("certainty", "curiosity"),
    ("present", "future"),
)


def normalize_intent_context(context: dict[str, Any] | None) -> dict[str, Any]:
    ctx = dict(context or {})
    if ctx.get("intent_tensions") or ctx.get("intent_commitments"):
        return {
            "intent_commitments": list(ctx.get("intent_commitments") or []),
            "intent_tensions": list(ctx.get("intent_tensions") or []),
            "intent_horizon_goals": list(ctx.get("intent_horizon_goals") or []),
            "intent_protected_values": list(ctx.get("intent_protected_values") or []),
            "intent_agency_note": ctx.get("intent_agency_note"),
        }
    return {}


def primary_intent_pull(intent_context: dict[str, Any] | None) -> str:
    payload = dict(intent_context or {})
    tensions = list(payload.get("intent_tensions") or [])
    if not tensions:
        return ""
    return str(dict(tensions[0]).get("pull") or "").strip()


def score_option_intent_alignment(option: str, intent_context: dict[str, Any] | None) -> float:
    """Score how well an deliberation option aligns with current intent pull."""
    payload = normalize_intent_context(intent_context)
    if not payload:
        return 0.5
    lowered = str(option or "").lower()
    pull = primary_intent_pull(payload)
    if not pull:
        return 0.5
    hints = PULL_OPTION_HINTS.get(pull, ())
    if hints and any(hint in lowered for hint in hints):
        return 0.88
    for pole_a, pole_b in OPPOSING_PULLS:
        if pull == pole_a:
            opposite = PULL_OPTION_HINTS.get(pole_b, ())
            if opposite and any(hint in lowered for hint in opposite):
                return 0.28
        if pull == pole_b:
            opposite = PULL_OPTION_HINTS.get(pole_a, ())
            if opposite and any(hint in lowered for hint in opposite):
                return 0.28
    return 0.5


def score_chain_intent_alignment(
    chain: dict[str, Any],
    intent_context: dict[str, Any] | None,
) -> float:
    """Score planning chain against active commitments and intent pull."""
    payload = normalize_intent_context(intent_context)
    if not payload:
        return 0.0
    bonus = 0.0
    steps_text = " ".join(str(step) for step in chain.get("steps") or []).lower()
    active_commitments = [
        item
        for item in payload.get("intent_commitments") or []
        if isinstance(item, dict) and item.get("status") in {"active", "in_tension", "deferred"}
    ]
    for item in active_commitments:
        commitment = str(item.get("commitment") or "").lower()
        if not commitment:
            continue
        tokens = [token for token in commitment.split() if len(token) >= 4][:4]
        if tokens and any(token in steps_text for token in tokens):
            bonus += 1.75
    pull = primary_intent_pull(payload)
    chain_id = str(chain.get("chain_id") or "")
    if pull == "future" and chain_id in {"continuation", "subgoal"}:
        bonus += 1.25
    elif pull == "present" and chain_id == "primary":
        bonus += 1.0
    elif pull == "safety" and chain_id == "primary":
        bonus += 0.75
    return round(bonus, 3)


def intent_influence_summary(
    *,
    intent_context: dict[str, Any] | None,
    applied_to: str,
    detail: str,
) -> dict[str, Any]:
    pull = primary_intent_pull(intent_context)
    if not pull:
        return {}
    return {
        "applied_to": applied_to,
        "primary_pull": pull,
        "detail": detail[:160],
    }
