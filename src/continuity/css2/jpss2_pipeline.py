"""JPSS-2 pipeline — threshold lookup through governed update."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.continuity.css2.operations import apply_threshold, classify_operation
from src.continuity.css2.recalibration_governance import (
    RecalibrationLegitimacyResult,
    evaluate_threshold_delta_legitimacy,
)
from src.continuity.css2.spec import JPSS2_PIPELINE
from src.continuity.css2.threshold import SystemState, Threshold, ThresholdDelta
from src.continuity.css2.threshold_governance import find_relevant_thresholds


class CalibrationResult(BaseModel):
    threshold_id: str
    observed: Any
    classification: str


class MismatchSignal(BaseModel):
    threshold_id: str
    kind: str
    detail: str


class JPSS2PipelineResult(BaseModel):
    stages_executed: list[str] = Field(default_factory=list)
    calibrations: list[CalibrationResult] = Field(default_factory=list)
    mismatches: list[MismatchSignal] = Field(default_factory=list)
    proposed_deltas: list[ThresholdDelta] = Field(default_factory=list)
    legitimacy: RecalibrationLegitimacyResult | None = None
    thresholds_after: list[Threshold] = Field(default_factory=list)


def run_jpss2_slice(
    event: dict[str, Any],
    state: SystemState,
    *,
    observed_values: dict[str, Any] | None = None,
    mismatch_signals: list[MismatchSignal] | None = None,
    proposed_delta: ThresholdDelta | None = None,
    adversarial_results: list | None = None,
) -> JPSS2PipelineResult:
    """
    Execute JPSS-2 stages 4–12 for one event (threshold lookup → update).

    Earlier stages (environment, perception, salience) are caller-supplied via event.
    """
    result = JPSS2PipelineResult()
    values = observed_values or {}
    thresholds = list(state.thresholds)

    # 4. Threshold lookup
    relevant = find_relevant_thresholds(event, thresholds)
    result.stages_executed.append(JPSS2_PIPELINE[3])

    # 5. Calibration
    for th in relevant:
        obs = values.get(th.metric, event.get(th.metric))
        if obs is not None:
            cls = apply_threshold(th, obs)
            result.calibrations.append(
                CalibrationResult(
                    threshold_id=th.id,
                    observed=obs,
                    classification=cls,
                )
            )
    result.stages_executed.append(JPSS2_PIPELINE[4])

    # 6–8 decision / outcome / reflection — recorded on event if present
    for stage in JPSS2_PIPELINE[5:8]:
        result.stages_executed.append(stage)

    # 9. Threshold mismatch detection
    for sig in mismatch_signals or []:
        result.mismatches.append(sig)
    result.stages_executed.append(JPSS2_PIPELINE[8])

    # 10. Recalibration proposal
    if proposed_delta is not None:
        result.proposed_deltas.append(proposed_delta)
    result.stages_executed.append(JPSS2_PIPELINE[9])

    # 11–12. Governance + update
    if proposed_delta is not None:
        result.legitimacy = evaluate_threshold_delta_legitimacy(
            proposed_delta,
            rule=state.recalibration_rule,
            adversarial_results=adversarial_results,
        )
        result.stages_executed.append(JPSS2_PIPELINE[10])
        if result.legitimacy.legitimate:
            from src.continuity.css2.recalibration_governance import apply_approved_delta

            thresholds = apply_approved_delta(proposed_delta, thresholds)
            classify_operation(threshold_delta=proposed_delta)
        result.stages_executed.append(JPSS2_PIPELINE[11])

    result.thresholds_after = thresholds
    return result
