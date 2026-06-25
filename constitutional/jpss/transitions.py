"""JPSS-1 forward judgment-cycle transitions (JPSS-F)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from constitutional.eck1.models import EnvironmentState, PriorState
from constitutional.eck1.transitions import (
    calibration_transition,
    environment_state_from_inputs,
    judgment_transition,
    perception_transition,
    prior_state_from_inputs,
)
from constitutional.jpss.models import (
    CalibrationUpdateState,
    OutcomeState,
    PerceptionState,
    ReflectionState,
)


def perception_from_environment(
    environment: EnvironmentState,
    steward_inputs: dict[str, Any],
    *,
    captured_at: datetime | None = None,
) -> PerceptionState:
    """Environment → Perception."""
    now = captured_at or datetime.now(UTC).replace(microsecond=0)
    available = list(
        dict.fromkeys(
            steward_inputs.get("available_signals", [])
            + steward_inputs.get("expected_signals", [])
            + environment.environmental_factors
        )
    )
    missing = list(steward_inputs.get("missing_signals", []))
    return PerceptionState(
        available_signals=available,
        missing_signals=missing,
        intake_channels=steward_inputs.get("intake_channels", ["constitutional_runtime"]),
        noise_filtered=steward_inputs.get("noise_filtered", []),
        decision_id=steward_inputs.get("decision_id") or environment.decision_id,
        steward_id=steward_inputs.get("steward_id", "steward"),
        captured_at=now,
    )


def priors_from_perception(perception: PerceptionState) -> PriorState:
    """Perception → Priors (bridge to ECK-1 salience derivation)."""
    return PriorState(
        expected_signals=perception.available_signals,
        expected_risks=perception.missing_signals,
        ignored_possibilities=perception.noise_filtered,
        decision_id=perception.decision_id,
        steward_id=perception.steward_id,
        captured_at=perception.captured_at,
    )


def salience_from_perception(
    perception: PerceptionState,
    environment: EnvironmentState,
) -> Any:
    """Perception × Environment → Salience."""
    priors = priors_from_perception(perception)
    return perception_transition(
        priors,
        environment,
        decision_id=perception.decision_id,
        steward_id=perception.steward_id,
        captured_at=perception.captured_at,
    )


def outcome_from_decision(
    judgment,
    steward_inputs: dict[str, Any],
    *,
    captured_at: datetime | None = None,
) -> OutcomeState:
    """Decision → Outcome."""
    now = captured_at or datetime.now(UTC).replace(microsecond=0)
    observed = steward_inputs.get("observed_result", steward_inputs.get("outcome", judgment.outcome))
    expected = steward_inputs.get("expected_result")
    success = steward_inputs.get("success")
    if success is None and expected is not None:
        success = observed == expected
    return OutcomeState(
        decision_id=judgment.decision_id,
        observed_result=observed,
        expected_result=expected,
        success=success,
        steward_id=judgment.steward_id,
        captured_at=now,
    )


def reflection_from_outcome(
    outcome: OutcomeState,
    judgment,
    *,
    captured_at: datetime | None = None,
) -> ReflectionState:
    """Outcome → Reflection."""
    now = captured_at or datetime.now(UTC).replace(microsecond=0)
    if outcome.expected_result is None:
        delta = f"Observed {outcome.observed_result} without explicit expectation."
    elif outcome.success:
        delta = "Outcome matched expectation."
    else:
        delta = (
            f"Expected {outcome.expected_result} but observed {outcome.observed_result}."
        )
    lessons = [delta] if delta else []
    surprise = [] if outcome.success else [outcome.observed_result]
    return ReflectionState(
        decision_id=outcome.decision_id,
        expectation_delta=delta,
        lessons=lessons,
        surprise_signals=surprise,
        steward_id=judgment.steward_id,
        captured_at=now,
    )


def calibration_update_from_reflection(
    reflection: ReflectionState,
    calibration,
    *,
    captured_at: datetime | None = None,
) -> CalibrationUpdateState:
    """Reflection → Calibration Update."""
    now = captured_at or datetime.now(UTC).replace(microsecond=0)
    tighten = bool(reflection.surprise_signals)
    delta = 0.05 if tighten else -0.02
    new_threshold = min(0.95, max(0.1, calibration.evidence_threshold + delta))
    new_risk = max(0.1, min(0.9, calibration.risk_tolerance - (delta / 2)))
    rationale = (
        "Tightened calibration after surprising outcome."
        if tighten
        else "Relaxed calibration after expected outcome."
    )
    return CalibrationUpdateState(
        decision_id=reflection.decision_id,
        prior_evidence_threshold=calibration.evidence_threshold,
        new_evidence_threshold=new_threshold,
        prior_risk_tolerance=calibration.risk_tolerance,
        new_risk_tolerance=new_risk,
        adjustment_rationale=rationale,
        steward_id=reflection.steward_id,
        captured_at=now,
    )


def environment_from_steward_inputs(
    steward_inputs: dict[str, Any],
    *,
    captured_at: datetime | None = None,
) -> EnvironmentState:
    return environment_state_from_inputs(steward_inputs, captured_at=captured_at)


def decision_from_calibration(calibration, steward_inputs: dict[str, Any]):
    return judgment_transition(
        calibration,
        decision_id=steward_inputs.get("decision_id", "unknown"),
        outcome=steward_inputs.get("outcome", "pending"),
        rationale=steward_inputs.get("rationale", ""),
        applied_invariants=steward_inputs.get("applied_invariants"),
        applied_purpose_clauses=steward_inputs.get("applied_purpose_clauses"),
        steward_id=steward_inputs.get("steward_id", "steward"),
    )


def calibration_from_salience(salience, environment):
    return calibration_transition(salience, environment)


__all__ = [
    "calibration_from_salience",
    "calibration_update_from_reflection",
    "decision_from_calibration",
    "environment_from_steward_inputs",
    "outcome_from_decision",
    "perception_from_environment",
    "priors_from_perception",
    "reflection_from_outcome",
    "salience_from_perception",
]
