"""ECK-2 dual-pipeline models — formation + reconstruction."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from constitutional.eck1.models import (
    ContinuityState,
    EnvironmentState,
    PriorState,
    SignificanceState,
)
from constitutional.jpss.invariant_drift import InvariantDriftState
from constitutional.jpss.invariant_drift_dashboard import InvariantDriftDashboardState
from constitutional.jpss.models import JPSSCycleResult, JPSSDriftReport
from constitutional.jpss.stewardship_balancing_test import StewardshipBalancingResult
from constitutional.jpss.jpss_ii_models import JPSSIITransferabilityReport


class PerceptionReconstructionState(BaseModel):
    """ECK-R perception layer — reconstructed from perception register."""

    available_signals: list[str] = Field(default_factory=list)
    missing_signals: list[str] = Field(default_factory=list)
    intake_channels: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    steward_id: str = "steward"
    captured_at: datetime | None = None
    reconstructable: bool = False


class SalienceReconstructionState(BaseModel):
    """ECK-R salience layer — reconstructed from salience ledger."""

    primary_signals: list[str] = Field(default_factory=list)
    secondary_signals: list[str] = Field(default_factory=list)
    ignored_signals: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    steward_id: str = "steward"
    captured_at: datetime | None = None
    reconstructable: bool = False


class CalibrationReconstructionState(BaseModel):
    """ECK-R calibration layer — reconstructed from calibration register."""

    evidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    required_invariants: list[str] = Field(default_factory=list)
    decision_id: str | None = None
    steward_id: str = "steward"
    captured_at: datetime | None = None
    reconstructable: bool = False


class JudgmentReconstructionState(BaseModel):
    """ECK-R judgment layer — reconstructed from decision register."""

    decision_id: str
    outcome: str
    rationale: str
    applied_invariants: list[str] = Field(default_factory=list)
    steward_id: str = "steward"
    captured_at: datetime | None = None
    reconstructable: bool = False


class ContinuityUpdateState(BaseModel):
    """ECK-R terminal continuity verdict."""

    decision_id: str
    symmetry_index: float = Field(default=0.0, ge=0.0, le=1.0)
    reconstructable: bool = False
    remediation_hints: list[str] = Field(default_factory=list)
    captured_at: datetime | None = None


class ECK2ReconstructionResult(BaseModel):
    """Backward causal loop (ECK-R) for a single decision."""

    decision_id: str
    environment: EnvironmentState | None = None
    perception: PerceptionReconstructionState | None = None
    salience: SalienceReconstructionState | None = None
    calibration: CalibrationReconstructionState | None = None
    priors: PriorState | None = None
    judgment: JudgmentReconstructionState | None = None
    significance: SignificanceState | None = None
    continuity: ContinuityUpdateState | None = None
    perception_available_signals: list[str] = Field(default_factory=list)
    reconstructable: bool = False
    missing_layers: list[str] = Field(default_factory=list)
    captured_at: datetime | None = None


class DriftSymmetryFinding(BaseModel):
    layer: str
    formation_present: bool = False
    reconstruction_present: bool = False
    symmetric: bool = False
    description: str = ""


class DriftSymmetryReport(BaseModel):
    decision_id: str
    symmetry_index: float = Field(ge=0.0, le=1.0)
    findings: list[DriftSymmetryFinding] = Field(default_factory=list)
    formation_drift: JPSSDriftReport | None = None
    reconstruction_gaps: list[str] = Field(default_factory=list)
    captured_at: datetime | None = None

    @property
    def symmetric(self) -> bool:
        return self.symmetry_index >= 0.80 and not self.reconstruction_gaps


class ECK2PipelineResult(BaseModel):
    """Unified forward + reverse epistemic kernel output."""

    formation: JPSSCycleResult
    reconstruction: ECK2ReconstructionResult
    drift_symmetry: DriftSymmetryReport
    invariant_drift: InvariantDriftState | None = None
    invariant_drift_dashboard: InvariantDriftDashboardState | None = None
    stewardship_balancing: StewardshipBalancingResult | None = None
    transferability: JPSSIITransferabilityReport | None = None
    eck1_continuity: ContinuityState | None = None
    captured_at: datetime | None = None
