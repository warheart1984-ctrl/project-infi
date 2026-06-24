"""CRK-1 semantic object model tests."""

from __future__ import annotations

import pytest

from src.crk1.schema_validator import CRK1SchemaValidator
from src.crk1.semantic_layer import SemanticLayer
from src.crk1.semantic_objects import (
    InterpretationObject,
    OutcomeDescriptor,
    PredictionObject,
    ReconstructionObject,
)


def test_interpretation_object_schema(schema_validator: CRK1SchemaValidator) -> None:
    obj = InterpretationObject(
        name="dominant-frame",
        version="1.0",
        assumptions=["reality-visible"],
        weight=0.55,
        adversarial=False,
        lineage=[],
    )
    schema_validator.validate("InterpretationObject", obj.to_schema_dict())


def test_interpretation_object_rejects_non_prediction_bound() -> None:
    with pytest.raises(ValueError, match="K8"):
        InterpretationObject(
            name="bad",
            version="1.0",
            prediction_binding=False,
            weight=0.5,
            adversarial=False,
        )


def test_prediction_and_reconstruction_objects_schema(
    schema_validator: CRK1SchemaValidator,
    runtime,
) -> None:
    layer = SemanticLayer(runtime)
    layer._bootstrap()  # noqa: SLF001
    frames = layer.get_all_interpretations()
    evidence = layer.create_evidence()
    dominant = layer.get_dominant_interpretation()
    adversarial = next(f for f in frames if f.adversarial)

    prediction = layer.generate_prediction(dominant.id, evidence.id)
    pred_obj = PredictionObject.from_crk1_prediction(
        prediction,
        expected_outcome=OutcomeDescriptor(summary="consequence propagates"),
    )
    schema_validator.validate("PredictionObject", pred_obj.model_dump(mode="json"))

    view = layer.reconstruct(adversarial.id, evidence.id)
    recon = ReconstructionObject.from_reconstruction(
        interpretation_id=adversarial.id,
        evidence_id=evidence.id,
        reconstructed_view=view,
        divergence_from_dominant=0.4,
    )
    schema_validator.validate("ReconstructionObject", recon.model_dump(mode="json"))


def test_interpretation_lineage_round_trip(runtime) -> None:
    layer = SemanticLayer(runtime)
    parent = layer.create_interpretation(name="parent-frame", weight=0.4)
    child = layer.create_interpretation(name="child-frame", weight=0.3)
    child_obj = InterpretationObject.from_crk1_interpretation(child, lineage=[parent.id])
    assert parent.id in child_obj.lineage
