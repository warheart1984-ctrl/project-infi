"""Minimal Reconstruction Trace Schema (v1) — substrate for operator R."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.crk1.judgment_trace import JUDGMENT_DIMENSIONS, JudgmentTrace

if False:  # TYPE_CHECKING without import cycle at runtime
    pass


class TraceEvidence(BaseModel):
    """What reality provided — e_t."""

    raw: dict[str, Any] | str | float | int | bool | list[Any] | None = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    timestamp: str = ""

    def decode(self) -> dict[str, Any]:
        if isinstance(self.raw, dict):
            return dict(self.raw)
        if self.raw is None:
            return {}
        return {"value": self.raw, "signal": float(self.raw) if _is_numeric(self.raw) else 0.0}


class TraceContext(BaseModel):
    """Semantic frame in which evidence was interpreted — w_t context."""

    stateSummary: dict[str, float] = Field(default_factory=dict)
    relevantHistory: list[dict[str, Any]] = Field(default_factory=list)
    environment: dict[str, Any] = Field(default_factory=dict)

    @field_validator("stateSummary")
    @classmethod
    def _clamp_dimensions(cls, value: dict[str, float]) -> dict[str, float]:
        return {key: _clamp01(float(item)) for key, item in value.items()}


class TraceReasoning(BaseModel):
    """How judgment updated — interpretive and justificatory record."""

    interpretation: str = ""
    justification: str = ""
    dependencies: list[str] = Field(default_factory=list)


class TraceUncertainty(BaseModel):
    """What was known, estimated, and explicitly unknown."""

    estimates: dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    unknowns: list[str] = Field(default_factory=list)


class TraceThresholds(BaseModel):
    """Decision rules and trigger conditions for correction."""

    decisionRule: str = ""
    triggered: bool = False
    parameters: dict[str, float] = Field(default_factory=dict)


class TraceOutcomes(BaseModel):
    """Ground-truth anchor — what happened after judgment."""

    result: dict[str, Any] = Field(default_factory=dict)
    measuredEvidence: dict[str, Any] = Field(default_factory=dict)
    deltaFromExpectation: dict[str, Any] = Field(default_factory=dict)


class TraceCorrection(BaseModel):
    """Corrigibility record — macro reflection stage."""

    veto: bool = False
    correctionApplied: bool = False
    correctionType: str = ""
    postCorrectionState: dict[str, float] = Field(default_factory=dict)

    @field_validator("postCorrectionState")
    @classmethod
    def _clamp_dimensions(cls, value: dict[str, float]) -> dict[str, float]:
        return {key: _clamp01(float(item)) for key, item in value.items()}


class ReconstructionTrace(BaseModel):
    """
    Minimal reconstructability trace τ_t (v1).

    Logs how judgment can be reconstructed, not a narrative log of judgment.
    τ_t = (evidence, context, reasoning, uncertainty, thresholds, outcomes, correction)
    indexed by (generation, cycle).
    """

    generation: int = 0
    cycle: int = 0
    evidence: TraceEvidence = Field(default_factory=TraceEvidence)
    context: TraceContext = Field(default_factory=TraceContext)
    reasoning: TraceReasoning = Field(default_factory=TraceReasoning)
    uncertainty: TraceUncertainty = Field(default_factory=TraceUncertainty)
    thresholds: TraceThresholds = Field(default_factory=TraceThresholds)
    outcomes: TraceOutcomes = Field(default_factory=TraceOutcomes)
    correction: TraceCorrection = Field(default_factory=TraceCorrection)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def from_judgment_trace(legacy: JudgmentTrace) -> ReconstructionTrace:
    """Lift legacy JudgmentTrace wire objects into v1 ReconstructionTrace."""
    sources: list[str] = []
    if isinstance(legacy.evidence.raw, dict):
        source = legacy.evidence.raw.get("source")
        if source is not None:
            sources = [str(source)]

    return ReconstructionTrace(
        generation=0,
        cycle=0,
        evidence=TraceEvidence(
            raw=legacy.evidence.raw,
            sources=sources,
            timestamp="",
        ),
        context=TraceContext(
            stateSummary=dict(legacy.context.stateSummary),
            relevantHistory=[],
            environment={},
        ),
        reasoning=TraceReasoning(
            interpretation=legacy.reasoning.interpretation,
            justification=legacy.reasoning.justification,
            dependencies=[],
        ),
        uncertainty=TraceUncertainty(
            estimates=dict(legacy.uncertainty.dimensions),
            confidence=_clamp01(1.0 - legacy.uncertainty.level),
            unknowns=[],
        ),
        thresholds=TraceThresholds(
            decisionRule=legacy.reasoning.justification,
            triggered=bool(legacy.thresholds.values),
            parameters=dict(legacy.thresholds.values),
        ),
        outcomes=TraceOutcomes(
            result=dict(legacy.outcomes.result),
            measuredEvidence={},
            deltaFromExpectation={},
        ),
        correction=TraceCorrection(
            veto=False,
            correctionApplied=bool(legacy.correction.postCorrectionState),
            correctionType="threshold_adjustment" if legacy.correction.postCorrectionState else "",
            postCorrectionState=dict(legacy.correction.postCorrectionState),
        ),
    )


def as_reconstruction_trace(trace: JudgmentTrace | ReconstructionTrace) -> ReconstructionTrace:
    if isinstance(trace, ReconstructionTrace):
        return trace
    return from_judgment_trace(trace)


def _is_numeric(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


__all__ = [
    "JUDGMENT_DIMENSIONS",
    "ReconstructionTrace",
    "TraceContext",
    "TraceCorrection",
    "TraceEvidence",
    "TraceOutcomes",
    "TraceReasoning",
    "TraceThresholds",
    "TraceUncertainty",
    "as_reconstruction_trace",
    "from_judgment_trace",
]
