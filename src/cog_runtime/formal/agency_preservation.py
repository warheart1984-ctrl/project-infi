"""Runtime agency preservation checks — Theorem 8.1 enforcement sketch."""

from __future__ import annotations

from typing import Any

from src.cog_runtime.intent_core import CONSTITUTIONAL_PROTECTED_VALUES

NOVA_CORE_IDENTITY = (
    "Nova is a governed companion inside AAIS; Jarvis retains executive authority."
)


def _commitment_key(item: dict[str, Any]) -> str:
    cid = str(item.get("id") or item.get("commitment_id") or "").strip()
    if cid:
        return cid
    return str(item.get("commitment") or "").strip().lower()[:120]


def check_agency_preservation(
    prior_intent: dict[str, Any] | None,
    intent: dict[str, Any] | None,
    narrative: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Runtime Theorem 8.1 check:
    - constitutional protected values persist
    - active commitments are not silently dropped (usurpation)
    - narrative core identity unchanged
    """
    prior = dict(prior_intent or {})
    current = dict(intent or {})
    story = dict(narrative or {})
    issues: list[str] = []

    protected = {str(v) for v in (current.get("protected_values") or [])}
    for value in CONSTITUTIONAL_PROTECTED_VALUES:
        if value not in protected:
            issues.append(f"usurpation:missing_protected_value:{value}")

    prior_active = {
        _commitment_key(item): item
        for item in (prior.get("active_commitments") or [])
        if isinstance(item, dict) and str(item.get("status") or "active").lower() == "active"
    }
    current_keys = {
        _commitment_key(item)
        for item in (current.get("active_commitments") or [])
        if isinstance(item, dict)
    }
    unified = dict(current.get("unified_closure") or {})
    closed_ids = {
        str(item.get("id") or item.get("commitment_id") or _commitment_key(item))
        for item in (unified.get("closed_commitments") or [])
        if isinstance(item, dict)
    }
    for key, item in prior_active.items():
        if not key:
            continue
        if key in current_keys:
            continue
        if key in closed_ids:
            continue
        issues.append(f"usurpation:dropped_commitment:{key[:48]}")

    core = str(story.get("core_identity") or "").strip()
    if core and core != NOVA_CORE_IDENTITY:
        issues.append("distortion:core_identity_changed")

    return {
        "valid": not issues,
        "issues": issues,
        "theorem": "8.1_agency_preservation_runtime",
        "protected_value_count": len(protected),
        "prior_active_commitments": len(prior_active),
    }
