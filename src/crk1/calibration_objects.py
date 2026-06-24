"""First-class calibration layer objects — Expectation through CalibrationEvent."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.crk1.errors import ConstitutionalError


class ExpectationObject(BaseModel):
    """What we predicted — bound to a decision or forecast."""

    id: str = Field(default_factory=lambda: f"EXP-{uuid.uuid4().hex[:8].upper()}")
    type: Literal["ExpectationObject"] = "ExpectationObject"
    expected_outcome: float | str
    expected_confidence: float = Field(ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)
    model_ref: str = ""
    decision_ref: str = ""
    prediction_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class EvidenceObject(BaseModel):
    """What reality produced."""

    id: str = Field(default_factory=lambda: f"EVD-{uuid.uuid4().hex[:8].upper()}")
    type: Literal["EvidenceObject"] = "EvidenceObject"
    evidence_ref: str
    observed_outcome: float | str
    channel_id: str
    evidence_strength: float = Field(ge=0.0, le=1.0, default=1.0)
    expectation_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ContradictionObject(BaseModel):
    """How wrong we were."""

    id: str = Field(default_factory=lambda: f"CTR-{uuid.uuid4().hex[:8].upper()}")
    type: Literal["ContradictionObject"] = "ContradictionObject"
    expectation_ref: str
    evidence_ref: str
    contradiction_delta: float = Field(ge=0.0)
    prediction_error_vector: list[float] = Field(default_factory=list)
    threshold_exceeded: bool = False

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @property
    def delta(self) -> float:
        return self.contradiction_delta


class SurpriseObject(BaseModel):
    """How unexpected it was — C0: requires prior expectation."""

    id: str = Field(default_factory=lambda: f"SRP-{uuid.uuid4().hex[:8].upper()}")
    type: Literal["SurpriseObject"] = "SurpriseObject"
    contradiction_ref: str
    expectation_ref: str
    surprise_intensity: float = Field(ge=0.0)
    surprise_function: str = "delta_times_confidence"
    prior_confidence: float = Field(ge=0.0, le=1.0)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @property
    def magnitude(self) -> float:
        return self.surprise_intensity

    @property
    def basis(self) -> str:
        return self.surprise_function


class CorrectionDeltaObject(BaseModel):
    """How judgment changed — distinct from CorrectionObject aggregate."""

    id: str = Field(default_factory=lambda: f"CRD-{uuid.uuid4().hex[:8].upper()}")
    type: Literal["CorrectionDeltaObject"] = "CorrectionDeltaObject"
    surprise_ref: str
    update_rule_applied: str
    assumptions_removed: list[str] = Field(default_factory=list)
    assumptions_added: list[str] = Field(default_factory=list)
    model_shift: float | dict[str, Any] = 0.0
    new_confidence: float = Field(ge=0.0, le=1.0)
    predictive_accuracy_before: float = Field(ge=0.0, le=1.0, default=0.0)
    predictive_accuracy_after: float = Field(ge=0.0, le=1.0, default=0.0)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @property
    def summary(self) -> str:
        shift = self.model_shift
        if isinstance(shift, dict):
            shift_text = str(shift.get("delta", shift))
        else:
            shift_text = str(shift)
        return f"update={self.update_rule_applied}; shift={shift_text}"


class CalibrationEvent(BaseModel):
    """Canonical calibration node — produced when a correction is preserved."""

    id: str = Field(default_factory=lambda: f"CEV-{uuid.uuid4().hex[:8].upper()}")
    type: Literal["CalibrationEvent"] = "CalibrationEvent"
    crr_id: str
    steward_id: str
    channel_id: str
    expectation_ref: str
    evidence_ref: str
    contradiction_ref: str
    surprise_ref: str
    correction_ref: str
    calibration_delta: float
    related_grr_ids: list[str] = Field(default_factory=list)
    invariant_implications: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def assert_calibration_invariants(
    *,
    expectation: ExpectationObject | None,
    contradiction: ContradictionObject | None,
    surprise: SurpriseObject | None,
    correction: CorrectionDeltaObject | None,
) -> None:
    """Enforce C0–C2 at the object layer."""
    if surprise is not None and surprise.surprise_intensity > 0:
        if expectation is None or (not expectation.model_ref and not expectation.assumptions):
            if expectation is None or expectation.expected_confidence <= 0:
                raise ConstitutionalError("C0: no surprise without expectation")
    if correction is not None:
        if contradiction is None or not contradiction.threshold_exceeded:
            if abs(correction.model_shift if isinstance(correction.model_shift, (int, float)) else 0) > 0:
                raise ConstitutionalError("C1: no correction without contradiction")
        if abs(correction.predictive_accuracy_after - correction.predictive_accuracy_before) > 0:
            if not correction.assumptions_added and not correction.assumptions_removed:
                if isinstance(correction.model_shift, (int, float)) and abs(correction.model_shift) <= 0:
                    raise ConstitutionalError("C2: no calibration without correction")
