"""ECK-1 canonical epistemic objects."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PriorState(BaseModel):
    """Expectations, predictions, assumptions."""

    expected_signals: list[str] = Field(default_factory=list)
    expected_risks: list[str] = Field(default_factory=list)
    assumed_stabilities: list[str] = Field(default_factory=list)
    assumed_volatilities: list[str] = Field(default_factory=list)
    ignored_possibilities: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    steward_id: str = "steward"
    captured_at: datetime | None = None


class SalienceState(BaseModel):
    """Foregrounded, backgrounded, and ignored signals."""

    primary_signals: list[str] = Field(default_factory=list)
    secondary_signals: list[str] = Field(default_factory=list)
    ignored_signals: list[str] = Field(default_factory=list)
    risk_salience: list[str] = Field(default_factory=list)
    deprioritized_risks: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    steward_id: str = "steward"
    captured_at: datetime | None = None


class EnvironmentState(BaseModel):
    """Constraints, incentives, uncertainties, pressures."""

    constraints_active: list[str] = Field(default_factory=list)
    incentives_present: list[str] = Field(default_factory=list)
    uncertainties_dominant: list[str] = Field(default_factory=list)
    environmental_factors: list[str] = Field(default_factory=list)
    failure_modes_feared: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    steward_id: str = "steward"
    captured_at: datetime | None = None


class CalibrationState(BaseModel):
    """Thresholds, evidence requirements, risk tolerances."""

    evidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    required_invariants: list[str] = Field(default_factory=list)
    required_purpose_links: list[str] = Field(default_factory=list)
    evidence_available: list[str] = Field(default_factory=list)
    evidence_missing: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    steward_id: str = "steward"
    captured_at: datetime | None = None


class JudgmentState(BaseModel):
    """Decision, rationale, applied invariants, applied purpose clauses."""

    decision_id: str
    outcome: str
    rationale: str
    applied_invariants: list[str] = Field(default_factory=list)
    applied_purpose_clauses: list[str] = Field(default_factory=list)
    steward_id: str = "steward"
    captured_at: datetime | None = None


class SignificanceState(BaseModel):
    """Per-judgment significance tier, rationale, lineage."""

    artifact_id: str
    tier: int = Field(ge=0, le=4)
    rationale: str
    lineage: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    steward_id: str = "steward"
    captured_at: datetime | None = None


class ContinuityState(BaseModel):
    """Receipts, lineage, registers, drift indices."""

    prior_drift_index: float = Field(default=1.0, ge=0.0, le=1.0)
    salience_index: float = Field(default=1.0, ge=0.0, le=1.0)
    perceptual_drift_index: float = Field(default=1.0, ge=0.0, le=1.0)
    environment_health_index: float = Field(default=1.0, ge=0.0, le=1.0)
    calibration_index: float = Field(default=1.0, ge=0.0, le=1.0)
    significance_continuity_index: float = Field(default=1.0, ge=0.0, le=1.0)
    failure_continuity_index: float = Field(default=1.0, ge=0.0, le=1.0)
    judgment_passed: bool = True
    receipts: list[str] = Field(default_factory=list)
    lineage: dict[str, Any] = Field(default_factory=dict)
    captured_at: datetime | None = None


class ECK1PipelineResult(BaseModel):
    """Output of a full ECK-1 epistemic pipeline run."""

    priors: PriorState
    salience: SalienceState
    environment: EnvironmentState
    calibration: CalibrationState
    judgment: JudgmentState
    significance: SignificanceState
    continuity: ContinuityState
