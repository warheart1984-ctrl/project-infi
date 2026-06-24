"""Continuity Failure Equation (CFE) — formal continuity collapse detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

FailureMode = Literal[
    "evidence_blocked",
    "no_contradiction",
    "no_surprise",
    "no_correction",
    "lineage_blocked",
    "corrigibility_zero",
]


@dataclass(frozen=True)
class CFEInputs:
    """Operational inputs for continuity failure evaluation."""

    ce: float
    contradiction_magnitude: float
    surprise_response: float
    calibration_delta: float
    lineage_transmission_rate: float = 1.0
    corrigibility: float | None = None
    epsilon: float = 1e-6


@dataclass(frozen=True)
class CFEReport:
    """CFE evaluation — continuity fails if any operational condition holds."""

    continuity_intact: bool
    failure_modes: tuple[FailureMode, ...]
    cfe_triggered: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "continuity_intact": self.continuity_intact,
            "failure_modes": list(self.failure_modes),
            "cfe_triggered": self.cfe_triggered,
        }


def evaluate_continuity_failure(inputs: CFEInputs) -> CFEReport:
    """
    CFE — continuity fails when C(t) → 0 or operational form holds.

    Expanded: (dC/dt = 0) ∧ (Reality > 0) while contradiction persists uncorrected.
    """
    modes: list[FailureMode] = []

    if inputs.ce <= inputs.epsilon:
        modes.append("evidence_blocked")

    reality_active = inputs.contradiction_magnitude > inputs.epsilon or inputs.ce > inputs.epsilon

    if reality_active and inputs.contradiction_magnitude <= inputs.epsilon:
        modes.append("no_contradiction")

    if inputs.contradiction_magnitude > inputs.epsilon and inputs.surprise_response <= inputs.epsilon:
        modes.append("no_surprise")

    if inputs.contradiction_magnitude > inputs.epsilon and abs(inputs.calibration_delta) <= inputs.epsilon:
        modes.append("no_correction")

    if abs(inputs.calibration_delta) > inputs.epsilon and inputs.lineage_transmission_rate <= inputs.epsilon:
        modes.append("lineage_blocked")

    if inputs.corrigibility is not None and inputs.corrigibility <= inputs.epsilon and reality_active:
        modes.append("corrigibility_zero")

    cfe = len(modes) > 0
    return CFEReport(
        continuity_intact=not cfe,
        failure_modes=tuple(modes),
        cfe_triggered=cfe,
    )
