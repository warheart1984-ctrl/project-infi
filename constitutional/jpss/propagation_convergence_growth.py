"""Propagation–convergence growth curve metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SignalType = Literal["PROPAGATION", "CONVERGENCE"]


class SignalEvent(BaseModel):
    timestamp: datetime
    type: SignalType


class GrowthPoint(BaseModel):
    time: datetime
    propagation_count: int
    convergence_count: int


class BalancedGrowthAssessment(BaseModel):
    balanced: bool
    ratio: float | None = None
    last_propagation_count: int = 0
    last_convergence_count: int = 0


def compute_growth_curve(events: list[SignalEvent]) -> list[GrowthPoint]:
    sorted_events = sorted(events, key=lambda event: event.timestamp)
    propagation = 0
    convergence = 0
    curve: list[GrowthPoint] = []

    for event in sorted_events:
        if event.type == "PROPAGATION":
            propagation += 1
        if event.type == "CONVERGENCE":
            convergence += 1
        curve.append(
            GrowthPoint(
                time=event.timestamp,
                propagation_count=propagation,
                convergence_count=convergence,
            )
        )
    return curve


def assess_balanced_growth(
    curve: list[GrowthPoint],
    *,
    max_ratio: float = 3.0,
) -> BalancedGrowthAssessment:
    """Both curves must be non-zero and within max_ratio of each other."""
    if not curve:
        return BalancedGrowthAssessment(balanced=False)

    last = curve[-1]
    if last.propagation_count == 0 or last.convergence_count == 0:
        return BalancedGrowthAssessment(
            balanced=False,
            last_propagation_count=last.propagation_count,
            last_convergence_count=last.convergence_count,
        )

    ratio = (
        last.propagation_count / last.convergence_count
        if last.propagation_count >= last.convergence_count
        else last.convergence_count / last.propagation_count
    )
    return BalancedGrowthAssessment(
        balanced=ratio <= max_ratio,
        ratio=round(ratio, 4),
        last_propagation_count=last.propagation_count,
        last_convergence_count=last.convergence_count,
    )
