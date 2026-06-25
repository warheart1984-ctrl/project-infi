"""Four operations — learning, calibration, recalibration, constitutional recalibration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.continuity.css2.spec import (
    OPERATION_CALIBRATION,
    OPERATION_CONSTITUTIONAL_RECALIBRATION,
    OPERATION_LEARNING,
    OPERATION_RECALIBRATION,
    ContinuityOperation,
)
from src.continuity.css2.threshold import (
    RecalibrationRuleDelta,
    Threshold,
    ThresholdDelta,
)


class OperationClassification(BaseModel):
    operation: ContinuityOperation
    minimal_unit: str | None = None
    threshold_changed: bool = False
    beliefs_changed: bool = False
    rules_changed: bool = False
    notes: list[str] = Field(default_factory=list)


def classify_operation(
    *,
    belief_delta: dict[str, Any] | None = None,
    threshold_delta: ThresholdDelta | None = None,
    rule_delta: RecalibrationRuleDelta | None = None,
    calibration_only: bool = False,
) -> OperationClassification:
    """
    Classify which of the four operations occurred.

    Boundary: recalibration only when a threshold changes; constitutional only
    when recalibration rules change.
    """
    if rule_delta is not None and _rule_changed(rule_delta):
        return OperationClassification(
            operation=OPERATION_CONSTITUTIONAL_RECALIBRATION,
            minimal_unit="Δ-recalibration-rule",
            rules_changed=True,
            notes=["Governance of recalibration legitimacy changed."],
        )

    if threshold_delta is not None and threshold_delta.is_recalibration:
        return OperationClassification(
            operation=OPERATION_RECALIBRATION,
            minimal_unit="Δ-threshold",
            threshold_changed=True,
            notes=[threshold_delta.rationale],
        )

    if calibration_only:
        return OperationClassification(
            operation=OPERATION_CALIBRATION,
            minimal_unit="judgment",
            notes=["Applied existing thresholds; no threshold mutation."],
        )

    if belief_delta:
        return OperationClassification(
            operation=OPERATION_LEARNING,
            minimal_unit="new fact or pattern",
            beliefs_changed=True,
            notes=["Internal models updated; thresholds unchanged."],
        )

    return OperationClassification(
        operation=OPERATION_CALIBRATION,
        minimal_unit="judgment",
        notes=["No belief, threshold, or rule change detected — treated as calibration."],
    )


def apply_threshold(threshold: Threshold, observed: Any) -> str:
    """Calibration — classify using current threshold without mutation."""
    crossed = threshold.classify(observed)
    return "intervention" if crossed else "normal"


# --- Formal tests A & B ---


def test_a_learn_without_recalibrate(
    *,
    beliefs_before: dict[str, Any],
    beliefs_after: dict[str, Any],
    thresholds_before: list[Threshold],
    thresholds_after: list[Threshold],
) -> bool:
    """System can learn indefinitely without recalibrating."""
    beliefs_changed = beliefs_before != beliefs_after
    thresholds_unchanged = [t.model_dump() for t in thresholds_before] == [
        t.model_dump() for t in thresholds_after
    ]
    return beliefs_changed and thresholds_unchanged


def test_b_recalibrate_without_learn(
    *,
    beliefs_before: dict[str, Any],
    beliefs_after: dict[str, Any],
    threshold_delta: ThresholdDelta,
) -> bool:
    """Steward can recalibrate without learning (facts/models unchanged)."""
    beliefs_unchanged = beliefs_before == beliefs_after
    threshold_changed = threshold_delta.is_recalibration
    return beliefs_unchanged and threshold_changed


def _rule_changed(delta: RecalibrationRuleDelta) -> bool:
    return delta.before.model_dump() != delta.after.model_dump(
        exclude={"created_at", "created_by"}
    )
