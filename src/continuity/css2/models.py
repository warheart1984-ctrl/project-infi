"""CSS-2 core models — calibration, recalibration events, governance context."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

RecalibrationScope = Literal["local", "subsystem", "system", "constitutional"]
RecalibrationTriggerType = Literal["evidence", "drift", "failure", "mandate", "other"]
RecalibrationDecision = Literal["approved", "rejected", "deferred", "escalated"]
ContinuityEffect = Literal["improved", "degraded", "ambiguous"]
RecalibrationFailureMode = Literal[
    "CalibrationDrift",
    "RecalibrationFailure",
    "RecalibrationCapture",
    "FalseRecalibration",
    "OverRecalibration",
    "UnderRecalibration",
    "MetaDrift",
    "ThresholdCollapse",
    "AdversarialRecalibration",
    "RecalibrationInversion",
    "RecalibrationParalysis",
    "RecalibrationMyopia",
]


class InvariantRef(BaseModel):
    id: str
    description: str
    non_derogable: bool = False


class ThresholdBand(BaseModel):
    """Normal / concerning / intervention-worthy bands for one metric."""

    metric_id: str
    normal_max: float
    concerning_max: float
    intervention_max: float
    unit: str = ""


class Calibration(BaseModel):
    """Mapping from conditions → thresholds (what's normal / concerning / intervention-worthy)."""

    calibration_id: str
    scope: RecalibrationScope = "subsystem"
    thresholds: dict[str, ThresholdBand] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(microsecond=0))
    version: int = 1
    governed: bool = True


class RecalibrationTrigger(BaseModel):
    """Evidence or conditions that justify reconsidering thresholds."""

    trigger_id: str
    trigger_type: RecalibrationTriggerType
    description: str
    evidence_refs: list[str] = Field(default_factory=list)
    persistent_mismatch: bool = False
    repeated_failure: bool = False
    calibration_error: bool = False
    constitutional_mandate: bool = False

    @property
    def is_legitimate(self) -> bool:
        return (
            self.persistent_mismatch
            or self.repeated_failure
            or self.calibration_error
            or self.constitutional_mandate
            or self.trigger_type in {"evidence", "drift", "failure", "mandate"}
        )


class ThresholdChange(BaseModel):
    id: str
    metric_id: str
    before: float | str | dict[str, Any]
    after: float | str | dict[str, Any]
    rationale: str


class RecalibrationEvent(BaseModel):
    """Governed change to one or more thresholds."""

    event_id: str
    timestamp: datetime
    scope: RecalibrationScope
    trigger_type: RecalibrationTriggerType
    failure_mode_before: RecalibrationFailureMode | None = None
    proposed_changes: list[ThresholdChange] = Field(default_factory=list)
    invariants_checked: list[InvariantRef] = Field(default_factory=list)
    constraints_checked: list[str] = Field(default_factory=list)
    decision: RecalibrationDecision
    legitimacy_basis: str
    continuity_effect: ContinuityEffect | None = None
    decided_by: str = "RecalibrationGovernanceEngine"
    triggers: list[RecalibrationTrigger] = Field(default_factory=list)
    adversarial_review_passed: bool = False
    audit_trail: list[str] = Field(default_factory=list)


class RecalibrationProposalContext(BaseModel):
    state_snapshot: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    proposed_changes: list[ThresholdChange] = Field(default_factory=list)
    candidate_failure_mode: RecalibrationFailureMode | None = None
    invariants: list[InvariantRef] = Field(default_factory=list)
    triggers: list[RecalibrationTrigger] = Field(default_factory=list)
    scope: RecalibrationScope = "subsystem"
    trigger_type: RecalibrationTriggerType = "evidence"
    proposer_id: str = "operator"


class RecalibrationLedger(BaseModel):
    """Append-only ledger of governed recalibration events."""

    events: list[RecalibrationEvent] = Field(default_factory=list)
    calibrations: dict[str, Calibration] = Field(default_factory=dict)

    def append(self, event: RecalibrationEvent) -> None:
        self.events.append(event)

    def get_calibration(self, calibration_id: str) -> Calibration | None:
        return self.calibrations.get(calibration_id)


def new_recalibration_event_id(prefix: str = "recal") -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{stamp}-{uuid4().hex[:8]}"
