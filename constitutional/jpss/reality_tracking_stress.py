"""JPSS reality-tracking stress test — toy systems with hidden drift."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ToySystem(BaseModel):
    id: str
    invariant_value: float
    drift_per_step: float
    failure_threshold: float


class JPSSPrediction(BaseModel):
    system_id: str
    predicted_failure_step: int


class ActualOutcome(BaseModel):
    system_id: str
    actual_failure_step: int


class RealityTrackingDetail(JPSSPrediction, ActualOutcome):
    squared_error: float


class RealityTrackingEvaluation(BaseModel):
    mse: float
    details: list[RealityTrackingDetail] = Field(default_factory=list)


def simulate_system(system: ToySystem, max_steps: int = 100) -> ActualOutcome:
    value = system.invariant_value
    drift = system.drift_per_step
    threshold = system.failure_threshold

    for step in range(1, max_steps + 1):
        value += drift
        if abs(value) >= threshold:
            return ActualOutcome(system_id=system.id, actual_failure_step=step)

    return ActualOutcome(system_id=system.id, actual_failure_step=max_steps)


def predict_failure(system: ToySystem) -> JPSSPrediction:
    """Naive JPSS-style predictor: steps until threshold breach."""
    drift = abs(system.drift_per_step) or 1.0
    remaining = system.failure_threshold - abs(system.invariant_value)
    steps = max(1, int((remaining / drift) + 0.999))
    return JPSSPrediction(system_id=system.id, predicted_failure_step=steps)


def evaluate_reality_tracking(systems: list[ToySystem]) -> RealityTrackingEvaluation:
    details: list[RealityTrackingDetail] = []
    sum_sq = 0.0

    for system in systems:
        prediction = predict_failure(system)
        actual = simulate_system(system)
        diff = prediction.predicted_failure_step - actual.actual_failure_step
        squared = diff * diff
        sum_sq += squared
        details.append(
            RealityTrackingDetail(
                system_id=system.id,
                predicted_failure_step=prediction.predicted_failure_step,
                actual_failure_step=actual.actual_failure_step,
                squared_error=squared,
            )
        )

    mse = sum_sq / len(systems) if systems else 0.0
    return RealityTrackingEvaluation(mse=round(mse, 4), details=details)
