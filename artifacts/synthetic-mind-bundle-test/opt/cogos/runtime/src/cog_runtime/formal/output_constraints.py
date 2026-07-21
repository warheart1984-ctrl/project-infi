"""Bounded non-determinism — constraint checks on LLM-visible output before emit."""

from __future__ import annotations

import re
from typing import Any

OUTPUT_CONSTRAINT_IDS: tuple[str, ...] = (
    "speaking_stages",
    "alignment_check",
    "focus_non_contradiction",
    "required_citations",
    "no_action_leakage",
)

_ACTION_LEAKAGE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:I(?:'ve| have)? (?:run|executed|deleted|pushed|deployed))\b", re.I),
    re.compile(r"\b(?:running `?(?:rm|sudo|curl|wget|git push))\b", re.I),
)

_CITATION_MARKERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\[[^\]]+\]\([^)]+\)"),
    re.compile(r"\b(?:see|ref(?:erence)?|cite(?:d)?)\s+[`\[]?", re.I),
    re.compile(r"\b(?:docs/|\.md\b|proof bundle)\b", re.I),
)

_FOCUS_STOPWORDS = frozenset(
    {"the", "a", "an", "to", "for", "of", "and", "or", "on", "in", "with", "this", "that"}
)


def _focus_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if len(token) > 2 and token not in _FOCUS_STOPWORDS
    }


def _focus_reflected(primary: str, secondary: str, body: str, *, min_ratio: float = 0.34) -> bool:
    """Semantic overlap check — avoids brittle full-string substring matching."""
    body_tokens = _focus_tokens(body)
    if not body_tokens:
        return False
    for candidate in (primary, secondary):
        focus_tokens = _focus_tokens(candidate)
        if not focus_tokens:
            continue
        overlap = len(focus_tokens & body_tokens) / len(focus_tokens)
        if overlap >= min_ratio:
            return True
    return False


def verify_output_constraints(
    text: str,
    *,
    focus_artifact: dict[str, Any] | None = None,
    require_citations: bool = False,
    speaking_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check invariants on generated text before emission (verify stage)."""
    body = (text or "").strip()
    issues: list[str] = []
    constraints_checked: list[str] = []

    if speaking_validation is not None:
        constraints_checked.append("speaking_stages")
        if not speaking_validation.get("valid"):
            for item in speaking_validation.get("issues") or []:
                issues.append(f"speaking:{item}")
    else:
        constraints_checked.extend(("speaking_stages", "alignment_check"))

    primary = ""
    secondary = ""
    if isinstance(focus_artifact, dict):
        primary = str(focus_artifact.get("primary_focus") or "").strip()
        secondary = str(focus_artifact.get("secondary_focus") or "").strip()
    if primary or secondary:
        constraints_checked.append("focus_non_contradiction")
        if not _focus_reflected(primary, secondary, body):
            issues.append("focus_non_contradiction:primary_not_reflected")

    if require_citations:
        constraints_checked.append("required_citations")
        if not any(pattern.search(body) for pattern in _CITATION_MARKERS):
            issues.append("required_citations:missing")

    constraints_checked.append("no_action_leakage")
    for pattern in _ACTION_LEAKAGE_PATTERNS:
        if pattern.search(body):
            issues.append("no_action_leakage:claimed_execution")
            break

    return {
        "valid": not issues,
        "issues": issues,
        "constraints_checked": constraints_checked,
        "constraint_ids": list(OUTPUT_CONSTRAINT_IDS),
    }


def resample_until_valid(
    speak_fn,
    *,
    max_attempts: int = 3,
    focus_artifact: dict[str, Any] | None = None,
    require_citations: bool = False,
    validate_fn=None,
) -> tuple[str, dict[str, Any]]:
    """Rejection sampling: resample speak_fn until constraints pass or attempts exhaust."""
    if validate_fn is None:
        from src.speaking_runtime import validate_reply

        validate_fn = validate_reply

    attempts: list[dict[str, Any]] = []
    last_body = ""
    for attempt in range(1, max(1, max_attempts) + 1):
        last_body = str(speak_fn() or "").strip()
        speaking_validation = validate_fn(last_body)
        verification = verify_output_constraints(
            last_body,
            focus_artifact=focus_artifact,
            require_citations=require_citations,
            speaking_validation=speaking_validation,
        )
        attempts.append({"attempt": attempt, **verification})
        if verification["valid"]:
            return last_body, {
                "resampled": attempt > 1,
                "attempts": attempts,
                "final_valid": True,
            }
    return last_body, {
        "resampled": max_attempts > 1,
        "attempts": attempts,
        "final_valid": False,
        "exhausted": True,
    }
