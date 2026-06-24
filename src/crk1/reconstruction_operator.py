"""
Reconstruction operator R — trace τ_t to local judgment dynamics.

R(τ_t) = (ŵ_t, ŵ_{t+1}, F̂_t)

Recovers an approximation of Wave Math update:
    w_{t+1} ≈ F(w_t, R(w_t))

using only evidence, context, reasoning, uncertainty, thresholds, outcomes, correction.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, Field

from src.crk1.errors import ConstitutionalError
from src.crk1.judgment_trace import JUDGMENT_DIMENSIONS, JudgmentTrace
from src.crk1.reconstruction_trace import ReconstructionTrace, as_reconstruction_trace

TraceLike = JudgmentTrace | ReconstructionTrace


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True, slots=True)
class JudgmentState:
    """Local judgment vector w_t (Wave Math state)."""

    perception: float = 0.0
    interpretation: float = 0.0
    valuation: float = 0.0
    deliberation: float = 0.0
    commitment: float = 0.0
    reflection: float = 0.0

    @classmethod
    def from_mapping(cls, values: dict[str, float]) -> JudgmentState:
        return cls(
            **{
                dimension: _clamp01(float(values.get(dimension, 0.0)))
                for dimension in JUDGMENT_DIMENSIONS
            }
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "perception": self.perception,
            "interpretation": self.interpretation,
            "valuation": self.valuation,
            "deliberation": self.deliberation,
            "commitment": self.commitment,
            "reflection": self.reflection,
        }

    def l2_distance(self, other: JudgmentState) -> float:
        return math.sqrt(
            sum((getattr(self, dim) - getattr(other, dim)) ** 2 for dim in JUDGMENT_DIMENSIONS)
        )


@dataclass(frozen=True, slots=True)
class UpdateRule:
    """
    Local update operator F̂_t inferred from reasoning + thresholds + uncertainty.

    Form: if evidence signal >= threshold, adjust target_dimension by adjustment * scale.
    """

    rule_type: str
    target_dimension: str
    threshold_key: str
    threshold_value: float
    adjustment: float
    uncertainty_scale: float
    description: str = ""

    def apply(self, state: JudgmentState, evidence: dict[str, Any]) -> JudgmentState:
        signal = _evidence_signal(evidence)
        if signal < self.threshold_value:
            return state
        delta = self.adjustment * self.uncertainty_scale
        updated = state.to_dict()
        updated[self.target_dimension] = _clamp01(updated[self.target_dimension] + delta)
        return JudgmentState.from_mapping(updated)


class ReconstructionResult(BaseModel):
    """Codomain of R — local judgment dynamic for one trace."""

    w_hat_t: dict[str, float]
    w_hat_t_plus_1: dict[str, float]
    update_rule: dict[str, Any]
    evidence_decoded: dict[str, Any] = Field(default_factory=dict)
    coherent: bool = False
    reconstruction_error: float = 1.0

    @property
    def w_t(self) -> JudgmentState:
        return JudgmentState.from_mapping(self.w_hat_t)

    @property
    def w_t_plus_1(self) -> JudgmentState:
        return JudgmentState.from_mapping(self.w_hat_t_plus_1)

    @property
    def f_hat(self) -> UpdateRule:
        payload = self.update_rule
        return UpdateRule(
            rule_type=str(payload["rule_type"]),
            target_dimension=str(payload["target_dimension"]),
            threshold_key=str(payload["threshold_key"]),
            threshold_value=float(payload["threshold_value"]),
            adjustment=float(payload["adjustment"]),
            uncertainty_scale=float(payload["uncertainty_scale"]),
            description=str(payload.get("description", "")),
        )


def decode_evidence(trace: TraceLike) -> dict[str, Any]:
    """ê_t from τ_t.evidence."""
    normalized = as_reconstruction_trace(trace)
    return normalized.evidence.decode()


def decode_context(trace: TraceLike) -> JudgmentState:
    """ŵ_t from τ_t.context.stateSummary."""
    normalized = as_reconstruction_trace(trace)
    return JudgmentState.from_mapping(normalized.context.stateSummary)


def decode_outcome(trace: TraceLike) -> JudgmentState:
    """
    ŵ_{t+1} from τ_t.outcomes + τ_t.correction.

    postCorrectionState takes precedence when correction was applied.
    """
    normalized = as_reconstruction_trace(trace)
    if normalized.correction.veto and not normalized.correction.correctionApplied:
        return decode_context(trace)
    if normalized.correction.postCorrectionState:
        return JudgmentState.from_mapping(normalized.correction.postCorrectionState)
    result = normalized.outcomes.result
    if "state" in result and isinstance(result["state"], dict):
        return JudgmentState.from_mapping(
            {key: float(value) for key, value in result["state"].items()}
        )
    if all(dim in result for dim in JUDGMENT_DIMENSIONS):
        return JudgmentState.from_mapping({key: float(result[key]) for key in JUDGMENT_DIMENSIONS})
    delta = normalized.outcomes.deltaFromExpectation
    prior = decode_context(trace)
    updated = prior.to_dict()
    for dimension in JUDGMENT_DIMENSIONS:
        if dimension in result:
            updated[dimension] = _clamp01(float(result[dimension]))
        delta_key = f"{dimension}Delta"
        if delta_key in result:
            updated[dimension] = _clamp01(updated[dimension] + float(result[delta_key]))
        if isinstance(delta, dict) and dimension in delta:
            updated[dimension] = _clamp01(updated[dimension] + float(delta[dimension]))
    return JudgmentState.from_mapping(updated)


def infer_update_rule(trace: TraceLike) -> UpdateRule:
    """
    Infer F̂_t from reasoning + uncertainty + thresholds.

    Heuristic: pick target dimension from reasoning text, threshold from thresholds map,
    adjustment from outcome deltas or justification magnitude.
    """
    normalized = as_reconstruction_trace(trace)
    reasoning_text = f"{normalized.reasoning.interpretation} {normalized.reasoning.justification}".lower()
    target = _infer_target_dimension(reasoning_text)
    threshold_key = _infer_threshold_key(normalized.thresholds.parameters, target)
    threshold_value = float(normalized.thresholds.parameters.get(threshold_key, 0.5))
    adjustment = _infer_adjustment(normalized, target)
    uncertainty_scale = max(0.05, normalized.uncertainty.confidence)
    description = (
        f"if signal >= {threshold_key}({threshold_value:.3f}), "
        f"adjust {target} by {adjustment:.3f} * (1 - uncertainty)"
    )
    return UpdateRule(
        rule_type="threshold_adjustment",
        target_dimension=target,
        threshold_key=threshold_key,
        threshold_value=threshold_value,
        adjustment=adjustment,
        uncertainty_scale=uncertainty_scale,
        description=description,
    )


def reconstruct(trace: TraceLike, *, tolerance: float = 0.15) -> ReconstructionResult:
    """
    R(τ_t) → (ŵ_t, ŵ_{t+1}, F̂_t).

    Raises ConstitutionalError when coherence cannot be established within tolerance.
    """
    e_hat = decode_evidence(trace)
    w_hat_t = decode_context(trace)
    f_hat = infer_update_rule(trace)
    w_hat_t_plus_1 = decode_outcome(trace)
    predicted = f_hat.apply(w_hat_t, e_hat)
    error = predicted.l2_distance(w_hat_t_plus_1)
    coherent = error <= tolerance
    result = ReconstructionResult(
        w_hat_t=w_hat_t.to_dict(),
        w_hat_t_plus_1=w_hat_t_plus_1.to_dict(),
        update_rule={
            "rule_type": f_hat.rule_type,
            "target_dimension": f_hat.target_dimension,
            "threshold_key": f_hat.threshold_key,
            "threshold_value": f_hat.threshold_value,
            "adjustment": f_hat.adjustment,
            "uncertainty_scale": f_hat.uncertainty_scale,
            "description": f_hat.description,
        },
        evidence_decoded=e_hat,
        coherent=coherent,
        reconstruction_error=error,
    )
    if not coherent:
        raise ConstitutionalError(
            "Reconstruction failed: ŵ_{t+1} ≉ F̂_t(ŵ_t, ê_t) "
            f"(error={error:.4f}, tolerance={tolerance:.4f})"
        )
    return result


def reconstruct_or_report(trace: TraceLike, *, tolerance: float = 0.15) -> ReconstructionResult:
    """Non-throwing variant — returns coherent=False instead of raising."""
    e_hat = decode_evidence(trace)
    w_hat_t = decode_context(trace)
    f_hat = infer_update_rule(trace)
    w_hat_t_plus_1 = decode_outcome(trace)
    predicted = f_hat.apply(w_hat_t, e_hat)
    error = predicted.l2_distance(w_hat_t_plus_1)
    return ReconstructionResult(
        w_hat_t=w_hat_t.to_dict(),
        w_hat_t_plus_1=w_hat_t_plus_1.to_dict(),
        update_rule={
            "rule_type": f_hat.rule_type,
            "target_dimension": f_hat.target_dimension,
            "threshold_key": f_hat.threshold_key,
            "threshold_value": f_hat.threshold_value,
            "adjustment": f_hat.adjustment,
            "uncertainty_scale": f_hat.uncertainty_scale,
            "description": f_hat.description,
        },
        evidence_decoded=e_hat,
        coherent=error <= tolerance,
        reconstruction_error=error,
    )


def reconstruction_sufficient(
    traces: list[TraceLike],
    *,
    tolerance: float = 0.15,
    reconstructor: Callable[[TraceLike], ReconstructionResult] | None = None,
) -> bool:
    """
    Reconstruction sufficiency for a trace sequence {τ_t}:

    ∀t, ∃R(τ_t) such that ŵ_{t+1} ≈ F̂_t(ŵ_t, ê_t)
    """
    fn = reconstructor or (lambda trace: reconstruct_or_report(trace, tolerance=tolerance))
    if not traces:
        return False
    return all(fn(trace).coherent for trace in traces)


def _evidence_signal(evidence: dict[str, Any]) -> float:
    for key in ("signal", "value", "score", "magnitude"):
        if key in evidence:
            try:
                return float(evidence[key])
            except (TypeError, ValueError):
                continue
    return 0.0


def _infer_target_dimension(text: str) -> str:
    for dimension in JUDGMENT_DIMENSIONS:
        if dimension in text:
            return dimension
    return "valuation"


def _infer_threshold_key(thresholds: dict[str, float], target: str) -> str:
    for key in (f"{target}Threshold", target, "evidenceThreshold", "signalThreshold"):
        if key in thresholds:
            return key
    if thresholds:
        return next(iter(thresholds))
    return "evidenceThreshold"


def _infer_adjustment(trace: ReconstructionTrace, target: str) -> float:
    result = trace.outcomes.result
    delta_key = f"{target}Delta"
    if delta_key in result:
        return float(result[delta_key])
    if target in result and trace.context.stateSummary:
        try:
            return float(result[target]) - float(trace.context.stateSummary.get(target, 0.0))
        except (TypeError, ValueError):
            pass
    match = re.search(r"adjust(?:ment)?\s*(?:by)?\s*([-+]?\d*\.?\d+)", trace.reasoning.justification, re.I)
    if match:
        return float(match.group(1))
    return 0.1
