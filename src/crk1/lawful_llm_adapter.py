"""Constitutional facade for any LLM — CRK-1 + CK-1 + CLG-1 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.crk1.calibration_lineage_graph import CalibrationLineageGraphCLG1
from src.crk1.calibration_objects import EvidenceObject, ExpectationObject
from src.crk1.continuity_graph_v2 import ContinuityGraphV2
from src.crk1.correction_engine_ce1 import CorrectionEngineCE1
from src.crk1.correction_object import CorrectionObject
from src.crk1.crr1_builder import build_crr1
from src.crk1.governance_receipt_header import GovernanceReceiptHeader


@dataclass(frozen=True)
class ModelShiftView:
    """Test-friendly view of correction magnitude."""

    magnitude: float


@dataclass
class LawfulCorrection:
    """Wrapper exposing integration-test field paths on CorrectionObject."""

    correction_object: CorrectionObject

    @property
    def model_shift(self) -> ModelShiftView:
        return ModelShiftView(magnitude=abs(float(self.correction_object.correction.model_shift)))


class LawfulLLMAdapter:
    """
    Constitutional facade for any LLM.

    Ensures all interactions pass through:
      - CRK-1 governance gate (GRR header on decisions)
      - CK-1 calibration pipeline (CE-1 F1–F5)
      - CRR-1 preservation + CLG-1 lineage ingest
    """

    def __init__(
        self,
        model: Any,
        steward_id: str = "llm_steward",
        *,
        engine: CorrectionEngineCE1 | None = None,
        clg: CalibrationLineageGraphCLG1 | None = None,
        continuity_graph: ContinuityGraphV2 | None = None,
        channel_id: str = "reality.default",
        decision_cluster_id: str | None = None,
    ) -> None:
        self.model = model
        self.steward_id = steward_id
        self.engine = engine or CorrectionEngineCE1()
        self.clg = clg or CalibrationLineageGraphCLG1()
        self.continuity_graph = continuity_graph
        self.channel_id = channel_id
        self.decision_cluster_id = decision_cluster_id
        self._correction_count = 0

    # ---------------------------------------------------------
    # 1. DECISION → GRR-1 header
    # ---------------------------------------------------------
    def ask(self, prompt: str) -> tuple[Any, GovernanceReceiptHeader]:
        """LLM produces an action/decision; CRK-1 wraps it in a governance receipt header."""
        raw = self.model(prompt)
        grr = GovernanceReceiptHeader.from_decision(
            steward_id=self.steward_id,
            decision=raw,
            invariant_context=["K0_K2", "K3_K6", "K7_K12"],
        )
        return raw, grr

    # ---------------------------------------------------------
    # 2. EXPECTATION → ExpectationObject
    # ---------------------------------------------------------
    def predict(self, prompt: str) -> ExpectationObject:
        """LLM emits an expectation with confidence."""
        pred = self.model(prompt)
        if isinstance(pred, dict):
            outcome = pred.get("outcome", pred.get("expected_outcome", 0.0))
            confidence = float(pred.get("confidence", pred.get("expected_confidence", 0.5)))
            assumptions = list(pred.get("assumptions", []))
        else:
            outcome = pred
            confidence = 0.5
            assumptions = []

        return ExpectationObject(
            expected_outcome=outcome,
            expected_confidence=confidence,
            assumptions=assumptions,
            model_ref="lawful_llm",
        )

    # ---------------------------------------------------------
    # 3. OBSERVATION → EvidenceObject
    # ---------------------------------------------------------
    def observe(self, observation: dict[str, Any]) -> EvidenceObject:
        """Reality produces evidence; LLM ingests it."""
        channel = str(observation.get("channel", self.channel_id))
        return EvidenceObject(
            evidence_ref=str(observation.get("evidence_ref", f"E-{channel}")),
            observed_outcome=observation["value"],
            evidence_strength=float(observation.get("strength", 1.0)),
            channel_id=channel,
        )

    # ---------------------------------------------------------
    # 4. CORRECTION → CorrectionObject + CRR-1 + CLG-1
    # ---------------------------------------------------------
    def correct(
        self,
        expectation: ExpectationObject,
        evidence: EvidenceObject,
        *,
        related_grr_ids: list[str] | None = None,
    ) -> tuple[LawfulCorrection, dict[str, Any]]:
        """Run contradiction → surprise → correction → CRR-1 → CLG-1."""
        if not evidence.expectation_ref:
            evidence = evidence.model_copy(update={"expectation_ref": expectation.id})

        result = self.engine.run_from_objects(
            steward_id=self.steward_id,
            expectation=expectation,
            evidence=evidence,
            related_grr_ids=related_grr_ids,
        )

        self.clg.ingest_crr(
            result.crr,
            event=result.calibration_event,
            decision_cluster_id=self.decision_cluster_id,
        )

        correction = LawfulCorrection(correction_object=result.correction_object)
        crr1 = build_crr1(result)

        if self.continuity_graph is not None:
            self.continuity_graph.record_calibration_event(crr1)

        self._apply_correction(correction)
        self._correction_count += 1

        return correction, crr1

    def run_falling_object_scenario(self) -> tuple[LawfulCorrection, dict[str, Any]]:
        """
        MVCD — Falling Object Prediction.

        Expectation: 1.0s fall time. Reality: 0.3s.
        """
        exp = self.predict("Predict fall time for 2m drop.")
        if isinstance(self.model, FallingObjectModel):
            exp = ExpectationObject(
                expected_outcome=1.0,
                expected_confidence=exp.expected_confidence,
                assumptions=exp.assumptions,
                model_ref=exp.model_ref,
            )

        evidence = self.observe({"value": 0.3, "strength": 1.0, "channel": "physics.fall"})
        return self.correct(exp, evidence)

    # ---------------------------------------------------------
    # INTERNAL
    # ---------------------------------------------------------
    def _apply_correction(self, correction: LawfulCorrection) -> None:
        """Update the LLM's lawful facade state — intentionally minimal."""
        if hasattr(self.model, "on_correction"):
            self.model.on_correction(correction.correction_object)


class FallingObjectModel:
    """Canonical first continuity model — predicts 1.0s for 2m drop."""

    def __call__(self, prompt: str) -> dict[str, Any]:
        if "fall" in prompt.lower():
            return {"outcome": 1.0, "confidence": 0.9, "assumptions": ["vacuum", "no_drag"]}
        return {"outcome": 0.5, "confidence": 0.5, "assumptions": []}

    def on_correction(self, correction: CorrectionObject) -> None:
        pass
