"""Shared CISIV stage helpers for AAIS operating surfaces."""

# Mythic: Cisiv
# Engineering: CisivEngine
from __future__ import annotations

from typing import Any


CISIV_STAGE_SEQUENCE = [
    "concept",
    "identity",
    "structure",
    "implementation",
    "verification",
]

CISIV_STAGE_LABELS = {
    "concept": "Concept",
    "identity": "Identity",
    "structure": "Structure",
    "implementation": "Implementation",
    "verification": "Verification",
}

CISIV_STAGE_ALIASES = {
    "verify": "verification",
    "verified": "verification",
    "test": "verification",
    "build": "implementation",
    "implemented": "implementation",
}

# Backward-compatible alias used by run ledger logbook normalization.
CISIV_LOGBOOK_STAGES = frozenset(CISIV_STAGE_SEQUENCE)


def normalize_cisiv_stage(value: str | None, *, default: str = "implementation") -> str:
    """Return a canonical CISIV stage name with alias and fallback handling."""
    normalized_default = _canonicalize_token(default, fallback="implementation")
    normalized = _canonicalize_token(value)
    normalized = CISIV_STAGE_ALIASES.get(normalized, normalized)
    if normalized in CISIV_STAGE_LABELS:
        return normalized
    return normalized_default


def cisiv_stage_label(value: str | None, *, default: str = "implementation") -> str:
    stage = normalize_cisiv_stage(value, default=default)
    return CISIV_STAGE_LABELS[stage]


def infer_lifecycle_cisiv_stage(
    lifecycle: dict[str, Any] | None,
    *,
    default: str = "implementation",
) -> str:
    """Infer one CISIV stage from an action lifecycle payload."""
    lifecycle = dict(lifecycle or {})
    explicit = str(lifecycle.get("cisiv_stage") or "").strip()
    if explicit:
        return normalize_cisiv_stage(explicit, default=default)
    action_text = " ".join(
        str(item or "")
        for item in (
            lifecycle.get("action_id"),
            lifecycle.get("action_label"),
            lifecycle.get("source"),
        )
    ).lower()
    if any(token in action_text for token in ("test", "verify", "verification", "smoke", "lint", "check", "eval")):
        return "verification"
    return normalize_cisiv_stage(default, default="implementation")


def _canonicalize_token(value: str | None, *, fallback: str = "") -> str:
    return str(value or fallback).strip().lower().replace("-", "_").replace(" ", "_")
