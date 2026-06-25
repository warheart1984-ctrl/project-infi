"""JPSS-1 canonical judgment-cycle objects."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from constitutional.eck1.models import (
    CalibrationState,
    EnvironmentState,
    JudgmentState,
    SalienceState,
)
from constitutional.jpss.spec import JPSSDriftClass, JPSSStage


class PerceptionState(BaseModel):
    """Informational intake — what is available to be noticed."""

    available_signals: list[str] = Field(default_factory=list)
    missing_signals: list[str] = Field(default_factory=list)
    intake_channels: list[str] = Field(default_factory=list)
    noise_filtered: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    steward_id: str = "steward"
    captured_at: datetime | None = None


class OutcomeState(BaseModel):
    """Real-world result of a decision."""

    decision_id: str
    observed_result: str
    expected_result: str | None = None
    success: bool | None = None
    steward_id: str = "steward"
    captured_at: datetime | None = None


class ReflectionState(BaseModel):
    """Evaluation of outcome relative to expectations."""

    decision_id: str
    expectation_delta: str = ""
    lessons: list[str] = Field(default_factory=list)
    surprise_signals: list[str] = Field(default_factory=list)
    steward_id: str = "steward"
    captured_at: datetime | None = None


class CalibrationUpdateState(BaseModel):
    """Adjustment of thresholds and evidence weights after reflection."""

    decision_id: str
    prior_evidence_threshold: float = Field(ge=0.0, le=1.0)
    new_evidence_threshold: float = Field(ge=0.0, le=1.0)
    prior_risk_tolerance: float = Field(ge=0.0, le=1.0)
    new_risk_tolerance: float = Field(ge=0.0, le=1.0)
    adjustment_rationale: str = ""
    steward_id: str = "steward"
    captured_at: datetime | None = None


class JPSSCycleResult(BaseModel):
    """Complete forward judgment cycle (JPSS-F)."""

    decision_id: str
    environment: EnvironmentState
    perception: PerceptionState
    salience: SalienceState
    calibration: CalibrationState
    decision: JudgmentState
    outcome: OutcomeState
    reflection: ReflectionState
    calibration_update: CalibrationUpdateState
    stages_completed: list[JPSSStage] = Field(default_factory=list)
    captured_at: datetime | None = None


class JPSSDriftFinding(BaseModel):
    drift_class: JPSSDriftClass
    detected: bool = False
    description: str = ""
    correctable: bool = True


class JPSSDriftReport(BaseModel):
    decision_id: str | None = None
    findings: list[JPSSDriftFinding] = Field(default_factory=list)
    drift_detectable: bool = True
    drift_correctable: bool = True
    captured_at: datetime | None = None

    @property
    def active_drifts(self) -> list[JPSSDriftFinding]:
        return [finding for finding in self.findings if finding.detected]
