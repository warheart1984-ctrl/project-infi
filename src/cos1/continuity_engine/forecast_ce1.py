"""CE-Forecast-1 — unified steward emergence forecast."""

from __future__ import annotations

import math

from pydantic import BaseModel, Field

from src.cos1.continuity_engine.spec import (
    CE_FORECAST_ALPHA,
    CE_FORECAST_BETA,
    CE_FORECAST_DELTA,
    CE_FORECAST_GAMMA,
    CE_FORECAST_STEWARDSHIP_THRESHOLD,
    ContinuityPhase,
)
from src.cos1.continuity_engine.state_model import ContinuityStateVector


def _logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class CEForecastResult(BaseModel):
    """S(t) = σ(αP + βC + γA + δL) — stewardship emergence probability."""

    probability: float = Field(ge=0.0, le=1.0)
    phase: ContinuityPhase = "propagation"
    stewardship_likely: bool = False
    linear_score: float = 0.0
    state: ContinuityStateVector
    approaching_steward_emergence: bool = False


class StewardshipEmergenceSignals(BaseModel):
    """Signals beyond axis counts — required for Phase 4/5 classification."""

    successor_stewards: bool = False
    identity_conflicts_resolved: bool = False
    governance_events: bool = False
    continuity_mode: bool = False


def forecast_ce1(
    state: ContinuityStateVector,
    *,
    signals: StewardshipEmergenceSignals | None = None,
    alpha: float = CE_FORECAST_ALPHA,
    beta: float = CE_FORECAST_BETA,
    gamma: float = CE_FORECAST_GAMMA,
    delta: float = CE_FORECAST_DELTA,
    stewardship_threshold: float = CE_FORECAST_STEWARDSHIP_THRESHOLD,
) -> CEForecastResult:
    """
    CE-Forecast-1: logistic squashing of weighted axis counts and chain length.

    Stewardship becomes likely when S(t) > 0.75 (structural readiness).
    Phase 5 (stewardability) additionally requires successor stewards.
    """
    sig = signals or StewardshipEmergenceSignals()
    linear = (
        alpha * state.P
        + beta * state.C
        + gamma * state.A
        + delta * state.avg_chain_length
    )
    scaled = (
        alpha * math.log1p(state.P)
        + beta * math.log1p(state.C)
        + gamma * math.log1p(state.A)
        + delta * state.avg_chain_length
    )
    probability = _logistic(scaled * 2)

    phase = _resolve_phase(state, probability, sig)
    approaching = (
        sig.continuity_mode
        and not sig.successor_stewards
        and probability > 0.5
    )

    return CEForecastResult(
        probability=probability,
        phase=phase,
        stewardship_likely=probability > stewardship_threshold,
        linear_score=linear,
        state=state,
        approaching_steward_emergence=approaching,
    )


def _resolve_phase(
    state: ContinuityStateVector,
    probability: float,
    signals: StewardshipEmergenceSignals,
) -> ContinuityPhase:
    """Map metrics + stewardship signals to compounding-curve phase."""
    if signals.successor_stewards and probability > CE_FORECAST_STEWARDSHIP_THRESHOLD:
        return "stewardability"
    if signals.continuity_mode and (
        signals.identity_conflicts_resolved or signals.governance_events
    ):
        return "steward_emergence"
    if state.A >= 1 or state.avg_chain_length >= 1:
        return "accumulation"
    if state.C >= 2:
        return "convergence"
    return "propagation"
