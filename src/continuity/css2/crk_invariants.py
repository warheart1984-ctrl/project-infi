"""CRK-1 non-derogable invariant checks on ThresholdDelta (mirrors continuity-engine INV_001–003)."""

from __future__ import annotations

from src.continuity.css2.threshold import Threshold, ThresholdDelta

INVARIANT_IDS = (
    "INV_001_HALT_ON_SAFETY",
    "INV_002_NO_SILENT_WEAKENING",
    "INV_003_IDENTITY_INTENT",
)


def check_crk_threshold_delta(delta: ThresholdDelta) -> list[str]:
    """Return violated non-derogable invariant ids, if any."""
    before = delta.before
    after = delta.after
    violations: list[str] = []

    if _violates_halt_on_safety(before, after):
        violations.append("INV_001_HALT_ON_SAFETY")
    if _violates_no_silent_weakening(before, after):
        violations.append("INV_002_NO_SILENT_WEAKENING")
    if _violates_identity_intent(before, after):
        violations.append("INV_003_IDENTITY_INTENT")

    return violations


def _violates_halt_on_safety(before: Threshold, after: Threshold) -> bool:
    if before.metric != "safety_violations_per_hour":
        return False
    return before.value == 0 and isinstance(after.value, (int, float)) and after.value > 0


def _violates_no_silent_weakening(before: Threshold, after: Threshold) -> bool:
    safety_like = (
        "safety" in before.metric
        or "trust" in before.metric
        or "Safety" in before.domain
        or "Trust" in before.domain
    )
    if not safety_like:
        return False
    if isinstance(before.value, (int, float)) and isinstance(after.value, (int, float)):
        return after.value > before.value
    return False


def _violates_identity_intent(before: Threshold, after: Threshold) -> bool:
    core_intent = (
        "mission" in before.intent
        or "identity" in before.intent
        or "Core" in before.domain
    )
    return core_intent and before.intent != after.intent
