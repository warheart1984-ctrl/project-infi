"""RA-COS-1 recalibration trigger detector — threshold-aware."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from src.continuity.css2.threshold import SystemState, Threshold
from src.continuity.css2.threshold_governance import find_relevant_thresholds

RecalibrationTriggerReason = Literal[
    "systematic_misclassification",
    "late_intervention",
    "over_intervention",
    "drift_signal",
    "failure_pattern",
]


class RecalibrationTrigger(BaseModel):
    threshold_id: str
    reason: RecalibrationTriggerReason
    evidence: list[Any] = Field(default_factory=list)


def detect_recalibration_triggers(
    event: dict[str, Any],
    drift_signals: dict[str, Any] | None,
    validation: dict[str, Any] | None,
    state: SystemState,
) -> list[RecalibrationTrigger]:
    """
    Before evaluateProposal() runs, detect Δ-threshold candidates from mismatch.

    Operates on explicit Threshold objects (CSS-2 threshold governance).
    """
    triggers: list[RecalibrationTrigger] = []
    validation = validation or {}
    drift_signals = drift_signals or {}

    relevant = find_relevant_thresholds(event, state.thresholds)
    for th in relevant:
        if _is_systematic_misclassification(event, th, validation):
            triggers.append(
                RecalibrationTrigger(
                    threshold_id=th.id,
                    reason="systematic_misclassification",
                    evidence=[event, validation],
                )
            )
        if _is_late_intervention(event, th, validation):
            triggers.append(
                RecalibrationTrigger(
                    threshold_id=th.id,
                    reason="late_intervention",
                    evidence=[event, validation],
                )
            )
        if _is_over_intervention(event, th, validation):
            triggers.append(
                RecalibrationTrigger(
                    threshold_id=th.id,
                    reason="over_intervention",
                    evidence=[event, validation],
                )
            )

    if _has_strong_drift_signal(drift_signals):
        for th in _infer_impacted_thresholds(drift_signals, state.thresholds):
            triggers.append(
                RecalibrationTrigger(
                    threshold_id=th.id,
                    reason="drift_signal",
                    evidence=[drift_signals],
                )
            )

    if _is_continuity_failure_pattern(validation):
        for th in _infer_impacted_from_failures(validation, state.thresholds):
            triggers.append(
                RecalibrationTrigger(
                    threshold_id=th.id,
                    reason="failure_pattern",
                    evidence=[validation],
                )
            )

    return _dedupe_triggers(triggers)


def _is_systematic_misclassification(
    event: dict[str, Any],
    th: Threshold,
    validation: dict[str, Any],
) -> bool:
    return bool(
        validation.get("misclassification_count", 0) >= 3
        and validation.get("metric") == th.metric
    )


def _is_late_intervention(
    event: dict[str, Any],
    th: Threshold,
    validation: dict[str, Any],
) -> bool:
    return bool(
        validation.get("late_intervention")
        and event.get("metric") == th.metric
    )


def _is_over_intervention(
    event: dict[str, Any],
    th: Threshold,
    validation: dict[str, Any],
) -> bool:
    return bool(
        validation.get("over_intervention_count", 0) >= 3
        and event.get("metric") == th.metric
    )


def _has_strong_drift_signal(drift_signals: dict[str, Any]) -> bool:
    psd = drift_signals.get("psd_score")
    if psd is not None and float(psd) >= 0.6:
        return True
    return bool(drift_signals.get("strong_drift"))


def _infer_impacted_thresholds(
    drift_signals: dict[str, Any],
    thresholds: list[Threshold],
) -> list[Threshold]:
    domain = drift_signals.get("domain")
    if domain:
        return [t for t in thresholds if t.domain == domain]
    metric = drift_signals.get("metric")
    if metric:
        return [t for t in thresholds if t.metric == metric]
    return thresholds[:1] if thresholds else []


def _is_continuity_failure_pattern(validation: dict[str, Any]) -> bool:
    return bool(
        validation.get("continuity_failure")
        or validation.get("failure_pattern")
    )


def _infer_impacted_from_failures(
    validation: dict[str, Any],
    thresholds: list[Threshold],
) -> list[Threshold]:
    ids = validation.get("impacted_threshold_ids") or []
    if ids:
        return [t for t in thresholds if t.id in ids]
    domain = validation.get("failed_domain")
    if domain:
        return [t for t in thresholds if t.domain == domain]
    return []


def _dedupe_triggers(triggers: list[RecalibrationTrigger]) -> list[RecalibrationTrigger]:
    seen: set[tuple[str, str]] = set()
    out: list[RecalibrationTrigger] = []
    for tr in triggers:
        key = (tr.threshold_id, tr.reason)
        if key in seen:
            continue
        seen.add(key)
        out.append(tr)
    return out
