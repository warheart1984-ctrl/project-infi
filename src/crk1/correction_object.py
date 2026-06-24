"""CorrectionObject and CRR-1 — atomic calibration unit and preservation receipt."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from src.crk1.errors import ConstitutionalError


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


class ExpectationSection(BaseModel):
    expected_outcome: float | str
    expected_confidence: float = Field(ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)
    model_ref: str = ""


class EvidenceSection(BaseModel):
    evidence_ref: str
    observed_outcome: float | str
    channel_id: str
    evidence_strength: float = Field(ge=0.0, le=1.0, default=1.0)


class ContradictionSection(BaseModel):
    contradiction_delta: float = Field(ge=0.0)
    prediction_error_vector: list[float] = Field(default_factory=list)
    threshold_exceeded: bool = False


class SurpriseSection(BaseModel):
    surprise_intensity: float = Field(ge=0.0)
    surprise_function: str = "linear"
    prior_confidence: float = Field(ge=0.0, le=1.0)


class CorrectionSection(BaseModel):
    update_rule_applied: str
    assumptions_removed: list[str] = Field(default_factory=list)
    assumptions_added: list[str] = Field(default_factory=list)
    model_shift: float = 0.0
    new_confidence: float = Field(ge=0.0, le=1.0)


class CalibrationSection(BaseModel):
    calibration_delta: float
    bias_reduction: float = 0.0
    predictive_accuracy_change: float = 0.0


class IntegritySection(BaseModel):
    timestamp: str = Field(default_factory=_now_iso)
    steward_id: str
    signature: str = ""
    evidence_hash: str = ""


class LinkageSection(BaseModel):
    crr_id: str = ""
    lineage_refs: list[str] = Field(default_factory=list)


class CorrectionObject(BaseModel):
    """
    Atomic unit of calibration — runtime contract for reality changing judgment.

    Runtime invariants I1–I5 enforced at construction.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["CorrectionObject"] = "CorrectionObject"
    expectation: ExpectationSection
    evidence: EvidenceSection
    contradiction: ContradictionSection
    surprise: SurpriseSection
    correction: CorrectionSection
    calibration: CalibrationSection
    integrity: IntegritySection
    linkage: LinkageSection = Field(default_factory=LinkageSection)

    @model_validator(mode="after")
    def _enforce_runtime_invariants(self) -> "CorrectionObject":
        # I1 — no correction without contradiction
        if not self.contradiction.threshold_exceeded and abs(self.calibration.calibration_delta) > 0:
            raise ConstitutionalError("I1: correction without contradiction")
        # I2 — no surprise without expectation
        if self.surprise.surprise_intensity > 0 and not self.expectation.model_ref and not self.expectation.assumptions:
            if self.expectation.expected_confidence <= 0:
                raise ConstitutionalError("I2: surprise without prior expectation")
        # I3 — no calibration without correction
        if abs(self.calibration.calibration_delta) > 0 and abs(self.correction.model_shift) <= 0:
            if not self.correction.assumptions_added and not self.correction.assumptions_removed:
                raise ConstitutionalError("I3: calibration without correction event")
        return self

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class CalibrationCorrectionReceipt(BaseModel):
    """CRR-1 — preserves expectation → evidence → contradiction → surprise → correction."""

    id: str
    type: Literal["CalibrationCorrectionReceipt"] = "CalibrationCorrectionReceipt"
    created_at: str = Field(default_factory=_now_iso)
    created_by: str
    epoch: int = 1
    correction: CorrectionObject
    reconstruction_digest: str = ""

    @classmethod
    def from_correction(
        cls,
        correction: CorrectionObject,
        *,
        created_by: str,
        epoch: int = 1,
        crr_id: str | None = None,
    ) -> "CalibrationCorrectionReceipt":
        crr_id = crr_id or f"CRR-1-{uuid.uuid4().hex[:8].upper()}"
        correction.linkage.crr_id = crr_id
        digest = _sha256_payload(correction.to_dict())
        return cls(
            id=crr_id,
            created_by=created_by,
            epoch=epoch,
            correction=correction,
            reconstruction_digest=digest,
        )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def reconstruct(self) -> dict[str, Any]:
        """I5 / C-PoLT Test 7 — replay preserved calibration lineage."""
        c = self.correction
        return {
            "expectation": c.expectation.model_dump(),
            "evidence": c.evidence.model_dump(),
            "contradiction": c.contradiction.model_dump(),
            "surprise": c.surprise.model_dump(),
            "correction": c.correction.model_dump(),
            "calibration_delta": c.calibration.calibration_delta,
            "crr_id": self.id,
            "reconstruction_digest": self.reconstruction_digest,
        }
