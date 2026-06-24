"""CRK-1 semantic object model — Interpretation, Prediction, Reconstruction."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

from src.crk1.semantic_layer import CRK1Interpretation, CRK1Prediction

if TYPE_CHECKING:
    from src.crk1.semantic_layer import CRK1Reconstruction


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class OutcomeDescriptor(BaseModel):
    """Falsifiable expected outcome for a prediction-bound interpretation."""

    summary: str
    measurable: bool = True
    replay_required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class InterpretationObject(BaseModel):
    """
    Single interpretive frame (K7–K11).

    Must be plural, prediction-bound, non-dominant, reconstructable, drift-tracked.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str
    assumptions: list[str] = Field(default_factory=list)
    prediction_binding: bool = True
    weight: float = Field(ge=0.0, le=1.0)
    adversarial: bool = False
    lineage: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=_now_iso)

    @field_validator("prediction_binding")
    @classmethod
    def _k8_must_bind(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("K8: interpretation must be prediction-bound")
        return value

    def to_schema_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_crk1_interpretation(
        cls,
        frame: CRK1Interpretation,
        *,
        lineage: list[str] | None = None,
    ) -> InterpretationObject:
        return cls(
            id=frame.id,
            name=frame.name,
            version=frame.version,
            assumptions=list(frame.assumptions),
            prediction_binding=frame.prediction_binding,
            weight=frame.weight,
            adversarial=frame.adversarial,
            lineage=list(lineage or frame.lineage),
            created_at=frame.created_at,
        )


class PredictionObject(BaseModel):
    """Binds an interpretation to a falsifiable claim (K8)."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    interpretation_id: str
    evidence_id: str
    claim: str
    expected_outcome: OutcomeDescriptor
    created_at: str = Field(default_factory=_now_iso)

    @classmethod
    def from_crk1_prediction(
        cls,
        prediction: CRK1Prediction,
        *,
        expected_outcome: OutcomeDescriptor | None = None,
    ) -> PredictionObject:
        return cls(
            id=prediction.id,
            interpretation_id=prediction.frame_id,
            evidence_id=prediction.evidence_id,
            claim=prediction.claim,
            expected_outcome=expected_outcome
            or OutcomeDescriptor(summary=prediction.claim, measurable=True),
            created_at=prediction.created_at,
        )


class ReconstructionObject(BaseModel):
    """Adversarial reinterpretation of evidence (K10)."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    interpretation_id: str
    evidence_id: str
    reconstructed_view: str
    divergence_from_dominant: float = Field(ge=0.0, le=1.0)
    created_at: str = Field(default_factory=_now_iso)

    @classmethod
    def from_crk1_reconstruction(cls, rec: CRK1Reconstruction) -> ReconstructionObject:
        return cls(
            id=rec.id,
            interpretation_id=rec.interpretation_id,
            evidence_id=rec.evidence_id,
            reconstructed_view=rec.reconstructed_view,
            divergence_from_dominant=rec.divergence_from_dominant,
        )

    @classmethod
    def from_reconstruction(
        cls,
        *,
        interpretation_id: str,
        evidence_id: str,
        reconstructed_view: str,
        divergence_from_dominant: float,
    ) -> ReconstructionObject:
        return cls(
            interpretation_id=interpretation_id,
            evidence_id=evidence_id,
            reconstructed_view=reconstructed_view,
            divergence_from_dominant=divergence_from_dominant,
        )
