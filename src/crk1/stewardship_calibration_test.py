"""Stewardship Calibration Test (SCT) — constitutional steward corrigibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

SCTResult = Literal["PASS", "FAIL"]


@dataclass(frozen=True)
class SCTInputs:
    """SCT.1 — inputs to the stewardship calibration test."""

    evidence: float
    calibration_prior: float
    calibration_post: float
    contradiction_magnitude: float | None = None
    surprise_response: float | None = None
    epsilon: float = 1e-6


@dataclass(frozen=True)
class SCTReport:
    """SCT outcome with per-clause diagnostics."""

    result: SCTResult
    contradiction_detected: bool
    surprise_nonzero: bool
    correction_applied: bool
    traceable: bool
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "contradiction_detected": self.contradiction_detected,
            "surprise_nonzero": self.surprise_nonzero,
            "correction_applied": self.correction_applied,
            "traceable": self.traceable,
            "failures": list(self.failures),
        }


def compute_contradiction_magnitude(
    evidence: float,
    calibration_prior: float,
) -> float:
    """SCT.2 — X = |E - C_prior|."""
    return abs(evidence - calibration_prior)


def compute_surprise_response(
    contradiction_magnitude: float,
    *,
    scale: float = 1.0,
) -> float:
    """SCT.3 — Sr = f(X); default linear."""
    return max(0.0, contradiction_magnitude * scale)


def run_stewardship_calibration_test(
    inputs: SCTInputs,
    *,
    evidence_trace_id: str | None = None,
) -> SCTReport:
    """
    SCT.0–SCT.6 — determine whether steward S remains corrigible to reality.

    Pass iff X > ε ⇒ Sr > 0 ⇒ ΔC > 0 and ΔC is traceable to E.
    """
    x = (
        inputs.contradiction_magnitude
        if inputs.contradiction_magnitude is not None
        else compute_contradiction_magnitude(inputs.evidence, inputs.calibration_prior)
    )
    sr = (
        inputs.surprise_response
        if inputs.surprise_response is not None
        else compute_surprise_response(x)
    )
    delta_c = inputs.calibration_post - inputs.calibration_prior

    failures: list[str] = []

    # SCT.2 — contradiction ignored
    contradiction_detected = x > inputs.epsilon
    if not contradiction_detected and x > 0:
        failures.append("SCT.2: contradiction below epsilon but non-zero — ignored")

    if x > inputs.epsilon and sr <= 0:
        failures.append("SCT.3: surprise response zero despite contradiction")

    if x > inputs.epsilon and abs(delta_c) <= inputs.epsilon:
        failures.append("SCT.4: calibration unchanged despite contradiction")

    traceable = evidence_trace_id is not None or abs(inputs.evidence - inputs.calibration_prior) > 0
    if x > inputs.epsilon and delta_c != 0 and not traceable:
        failures.append("SCT.5: calibration not traceable to evidence")

    # SCT.6 — stewardship continuity
    passed = (
        contradiction_detected
        and (x <= inputs.epsilon or (sr > 0 and abs(delta_c) > inputs.epsilon))
        and (x <= inputs.epsilon or traceable)
    )

    return SCTReport(
        result="PASS" if passed and not failures else "FAIL",
        contradiction_detected=contradiction_detected,
        surprise_nonzero=sr > 0,
        correction_applied=abs(delta_c) > inputs.epsilon,
        traceable=traceable,
        failures=tuple(failures),
    )
