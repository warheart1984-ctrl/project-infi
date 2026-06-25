"""Edge-case detectors — hidden recalibration, threshold-camouflage, etc."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.continuity.css2.threshold import Threshold, ThresholdDelta


class EdgeCaseFinding(BaseModel):
    kind: str
    message: str
    threshold_ids: list[str] = Field(default_factory=list)
    severity: str = "medium"


def detect_hidden_recalibration(
    thresholds_before: list[Threshold],
    thresholds_after: list[Threshold],
    *,
    registered_deltas: list[ThresholdDelta],
) -> list[EdgeCaseFinding]:
    """Thresholds changed without a governed ThresholdDelta."""
    findings: list[EdgeCaseFinding] = []
    before_by_id = {t.id: t for t in thresholds_before}
    after_by_id = {t.id: t for t in thresholds_after}
    governed_ids = {d.threshold_id for d in registered_deltas}

    for tid, after in after_by_id.items():
        before = before_by_id.get(tid)
        if before is None:
            continue
        if before.model_dump() != after.model_dump() and tid not in governed_ids:
            findings.append(
                EdgeCaseFinding(
                    kind="hidden_recalibration",
                    message=f"Threshold {tid} changed without registered Δ-threshold",
                    threshold_ids=[tid],
                    severity="high",
                )
            )
    return findings


def detect_false_recalibration(
    label: str,
    *,
    threshold_delta: ThresholdDelta | None,
) -> EdgeCaseFinding | None:
    """Vocabulary changes but thresholds do not."""
    if threshold_delta is None:
        return None
    if not threshold_delta.is_recalibration:
        return EdgeCaseFinding(
            kind="false_recalibration",
            message=f"Labeled recalibration ({label}) but no threshold mutation",
            threshold_ids=[threshold_delta.threshold_id],
            severity="low",
        )
    return None


def detect_threshold_camouflage(
    *,
    claimed_operation: str,
    belief_delta: dict[str, Any] | None,
    threshold_delta: ThresholdDelta | None,
) -> EdgeCaseFinding | None:
    """Belief updates masquerading as threshold updates or vice versa."""
    if claimed_operation == "learning" and threshold_delta and threshold_delta.is_recalibration:
        return EdgeCaseFinding(
            kind="threshold_camouflage",
            message="Operation labeled learning but threshold changed",
            threshold_ids=[threshold_delta.threshold_id],
            severity="high",
        )
    if claimed_operation == "recalibration" and belief_delta and not (
        threshold_delta and threshold_delta.is_recalibration
    ):
        return EdgeCaseFinding(
            kind="over_learning",
            message="Operation labeled recalibration but only beliefs changed",
            severity="medium",
        )
    return None


def detect_recalibration_by_exception(
    exception_count: int,
    *,
    threshold_id: str,
    exception_limit: int = 3,
) -> EdgeCaseFinding | None:
    """Repeated exceptions effectively shift thresholds."""
    if exception_count > exception_limit:
        return EdgeCaseFinding(
            kind="recalibration_by_exception",
            message=(
                f"{exception_count} exceptions for {threshold_id} — "
                "effective threshold drift without Δ-threshold"
            ),
            threshold_ids=[threshold_id],
            severity="high",
        )
    return None


def detect_recalibration_by_silence(
    threshold: Threshold,
    *,
    reaffirmation_overdue_days: int,
    days_since_update: int,
) -> EdgeCaseFinding | None:
    """Failure to reaffirm thresholds allows implicit drift."""
    if days_since_update > reaffirmation_overdue_days:
        return EdgeCaseFinding(
            kind="recalibration_by_silence",
            message=(
                f"Threshold {threshold.id} not reaffirmed in {days_since_update}d "
                f"(limit {reaffirmation_overdue_days}d)"
            ),
            threshold_ids=[threshold.id],
            severity="medium",
        )
    return None
