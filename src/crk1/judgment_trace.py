"""Minimal judgment trace schema — substrate for reconstruction operator R."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

JUDGMENT_DIMENSIONS = (
    "perception",
    "interpretation",
    "valuation",
    "deliberation",
    "commitment",
    "reflection",
)


class TraceEvidence(BaseModel):
    """Decoded input e_t from observable evidence."""

    raw: dict[str, Any] | str | float | int | bool = Field(default_factory=dict)

    def decode(self) -> dict[str, Any]:
        if isinstance(self.raw, dict):
            return dict(self.raw)
        return {"value": self.raw, "signal": float(self.raw) if _is_numeric(self.raw) else 0.0}


class TraceContext(BaseModel):
    """Prior judgment state w_t."""

    stateSummary: dict[str, float] = Field(default_factory=dict)

    @field_validator("stateSummary")
    @classmethod
    def _clamp_dimensions(cls, value: dict[str, float]) -> dict[str, float]:
        return {key: _clamp01(float(item)) for key, item in value.items()}


class TraceReasoning(BaseModel):
    interpretation: str = ""
    justification: str = ""


class TraceUncertainty(BaseModel):
    level: float = Field(default=0.0, ge=0.0, le=1.0)
    dimensions: dict[str, float] = Field(default_factory=dict)


class TraceThresholds(BaseModel):
    values: dict[str, float] = Field(default_factory=dict)


class TraceOutcomes(BaseModel):
    result: dict[str, Any] = Field(default_factory=dict)


class TraceCorrection(BaseModel):
    postCorrectionState: dict[str, float] = Field(default_factory=dict)

    @field_validator("postCorrectionState")
    @classmethod
    def _clamp_dimensions(cls, value: dict[str, float]) -> dict[str, float]:
        return {key: _clamp01(float(item)) for key, item in value.items()}


class JudgmentTrace(BaseModel):
    """
    Single trace τ_t in the minimal schema.

    τ_t = (evidence, context, reasoning, uncertainty, thresholds, outcomes, correction)
    """

    evidence: TraceEvidence = Field(default_factory=TraceEvidence)
    context: TraceContext = Field(default_factory=TraceContext)
    reasoning: TraceReasoning = Field(default_factory=TraceReasoning)
    uncertainty: TraceUncertainty = Field(default_factory=TraceUncertainty)
    thresholds: TraceThresholds = Field(default_factory=TraceThresholds)
    outcomes: TraceOutcomes = Field(default_factory=TraceOutcomes)
    correction: TraceCorrection = Field(default_factory=TraceCorrection)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def _is_numeric(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
