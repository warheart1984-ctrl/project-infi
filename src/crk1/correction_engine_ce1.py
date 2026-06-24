"""CE-1 — Correction Engine implementing Calibration Layer functions F1–F5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.crk1.calibration_objects import (
    CalibrationEvent,
    ContradictionObject,
    CorrectionDeltaObject,
    EvidenceObject,
    ExpectationObject,
    SurpriseObject,
    assert_calibration_invariants,
)
from src.crk1.correction_object import (
    CalibrationCorrectionReceipt,
    CalibrationSection,
    CorrectionObject,
    CorrectionSection,
    ContradictionSection,
    EvidenceSection,
    ExpectationSection,
    IntegritySection,
    LinkageSection,
    SurpriseSection,
    _sha256_payload,
)
from src.crk1.errors import ConstitutionalError


def _numeric(value: float | str) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@dataclass
class CE1PipelineResult:
    """Output of a full CE-1 calibration cycle."""

    expectation: ExpectationObject
    evidence: EvidenceObject
    contradiction: ContradictionObject
    surprise: SurpriseObject
    correction_delta: CorrectionDeltaObject
    correction_object: CorrectionObject
    crr: CalibrationCorrectionReceipt
    calibration_event: CalibrationEvent

    def to_dict(self) -> dict[str, Any]:
        return {
            "expectation": self.expectation.to_dict(),
            "evidence": self.evidence.to_dict(),
            "contradiction": self.contradiction.to_dict(),
            "surprise": self.surprise.to_dict(),
            "correction_delta": self.correction_delta.to_dict(),
            "correction_object": self.correction_object.to_dict(),
            "crr": self.crr.to_dict(),
            "calibration_event": self.calibration_event.to_dict(),
        }


class CorrectionEngineCE1:
    """
    Constitutional Correction Engine — F1 through F5.

    F1 Detect Contradiction
    F2 Quantify Surprise
    F3 Apply Correction
    F4 Compute Calibration Delta
    F5 Preserve Calibration (CRR-1 + CalibrationEvent)
    """

    def __init__(
        self,
        *,
        contradiction_threshold: float = 0.01,
        surprise_function: str = "delta_times_confidence",
        default_update_rule: str = "bayesian_update",
    ) -> None:
        self.contradiction_threshold = contradiction_threshold
        self.surprise_function = surprise_function
        self.default_update_rule = default_update_rule

    # F1
    def detect_contradiction(
        self,
        expectation: ExpectationObject,
        evidence: EvidenceObject,
    ) -> ContradictionObject:
        exp_num = _numeric(expectation.expected_outcome)
        obs_num = _numeric(evidence.observed_outcome)
        delta = abs(exp_num - obs_num)
        return ContradictionObject(
            expectation_ref=expectation.id,
            evidence_ref=evidence.id,
            contradiction_delta=delta,
            prediction_error_vector=[obs_num - exp_num],
            threshold_exceeded=delta > self.contradiction_threshold,
        )

    # F2
    def quantify_surprise(
        self,
        contradiction: ContradictionObject,
        expectation: ExpectationObject,
    ) -> SurpriseObject:
        if not contradiction.threshold_exceeded:
            return SurpriseObject(
                contradiction_ref=contradiction.id,
                expectation_ref=expectation.id,
                surprise_intensity=0.0,
                surprise_function=self.surprise_function,
                prior_confidence=expectation.expected_confidence,
            )
        intensity = max(0.0, contradiction.contradiction_delta * expectation.expected_confidence)
        return SurpriseObject(
            contradiction_ref=contradiction.id,
            expectation_ref=expectation.id,
            surprise_intensity=intensity,
            surprise_function=self.surprise_function,
            prior_confidence=expectation.expected_confidence,
        )

    # F3
    def apply_correction(
        self,
        expectation: ExpectationObject,
        evidence: EvidenceObject,
        contradiction: ContradictionObject,
        surprise: SurpriseObject,
        *,
        update_rule: str | None = None,
    ) -> CorrectionDeltaObject:
        if not contradiction.threshold_exceeded:
            raise ConstitutionalError("F3: cannot apply correction without contradiction")
        exp_num = _numeric(expectation.expected_outcome)
        obs_num = _numeric(evidence.observed_outcome)
        model_shift = obs_num - exp_num
        new_confidence = max(0.0, min(1.0, expectation.expected_confidence - contradiction.contradiction_delta * 0.1))
        accuracy_before = expectation.expected_confidence
        accuracy_after = min(1.0, accuracy_before + 0.01)
        return CorrectionDeltaObject(
            surprise_ref=surprise.id,
            update_rule_applied=update_rule or self.default_update_rule,
            assumptions_removed=[a for a in expectation.assumptions if "optimistic" in a.lower()],
            assumptions_added=[f"observed_via_{evidence.channel_id}"],
            model_shift=model_shift,
            new_confidence=new_confidence,
            predictive_accuracy_before=accuracy_before,
            predictive_accuracy_after=accuracy_after,
        )

    # F4
    def compute_calibration_delta(
        self,
        correction: CorrectionDeltaObject,
    ) -> float:
        shift = correction.model_shift
        if isinstance(shift, dict):
            return float(shift.get("delta", 0.0))
        return float(shift)

    # F5
    def preserve_calibration(
        self,
        *,
        steward_id: str,
        expectation: ExpectationObject,
        evidence: EvidenceObject,
        contradiction: ContradictionObject,
        surprise: SurpriseObject,
        correction_delta: CorrectionDeltaObject,
        epoch: int = 1,
        related_grr_ids: list[str] | None = None,
        invariant_implications: list[str] | None = None,
        lineage_refs: list[str] | None = None,
    ) -> tuple[CorrectionObject, CalibrationCorrectionReceipt, CalibrationEvent]:
        calibration_delta = self.compute_calibration_delta(correction_delta)
        evidence_payload = evidence.to_dict()

        correction_object = CorrectionObject(
            expectation=ExpectationSection(
                expected_outcome=expectation.expected_outcome,
                expected_confidence=expectation.expected_confidence,
                assumptions=list(expectation.assumptions),
                model_ref=expectation.model_ref,
            ),
            evidence=EvidenceSection(
                evidence_ref=evidence.evidence_ref,
                observed_outcome=evidence.observed_outcome,
                channel_id=evidence.channel_id,
                evidence_strength=evidence.evidence_strength,
            ),
            contradiction=ContradictionSection(
                contradiction_delta=contradiction.contradiction_delta,
                prediction_error_vector=list(contradiction.prediction_error_vector),
                threshold_exceeded=contradiction.threshold_exceeded,
            ),
            surprise=SurpriseSection(
                surprise_intensity=surprise.surprise_intensity,
                surprise_function=surprise.surprise_function,
                prior_confidence=surprise.prior_confidence,
            ),
            correction=CorrectionSection(
                update_rule_applied=correction_delta.update_rule_applied,
                assumptions_removed=list(correction_delta.assumptions_removed),
                assumptions_added=list(correction_delta.assumptions_added),
                model_shift=float(correction_delta.model_shift)
                if isinstance(correction_delta.model_shift, (int, float))
                else 0.0,
                new_confidence=correction_delta.new_confidence,
            ),
            calibration=CalibrationSection(
                calibration_delta=calibration_delta,
                bias_reduction=abs(calibration_delta) * 0.5,
                predictive_accuracy_change=correction_delta.predictive_accuracy_after
                - correction_delta.predictive_accuracy_before,
            ),
            integrity=IntegritySection(
                steward_id=steward_id,
                evidence_hash=_sha256_payload(evidence_payload),
                signature=f"steward:{steward_id}",
            ),
            linkage=LinkageSection(lineage_refs=list(lineage_refs or [])),
        )

        crr = CalibrationCorrectionReceipt.from_correction(
            correction_object,
            created_by=steward_id,
            epoch=epoch,
        )

        event = CalibrationEvent(
            crr_id=crr.id,
            steward_id=steward_id,
            channel_id=evidence.channel_id,
            expectation_ref=expectation.id,
            evidence_ref=evidence.id,
            contradiction_ref=contradiction.id,
            surprise_ref=surprise.id,
            correction_ref=correction_delta.id,
            calibration_delta=calibration_delta,
            related_grr_ids=list(related_grr_ids or []),
            invariant_implications=list(invariant_implications or []),
        )

        return correction_object, crr, event

    def run(
        self,
        *,
        steward_id: str,
        channel_id: str,
        expected_outcome: float | str,
        observed_outcome: float | str,
        expected_confidence: float,
        assumptions: list[str] | None = None,
        model_ref: str = "ce1-default",
        decision_ref: str = "",
        related_grr_ids: list[str] | None = None,
        invariant_implications: list[str] | None = None,
        epoch: int = 1,
    ) -> CE1PipelineResult:
        """Full F1–F5 pipeline from raw inputs."""
        expectation = ExpectationObject(
            expected_outcome=expected_outcome,
            expected_confidence=expected_confidence,
            assumptions=list(assumptions or []),
            model_ref=model_ref,
            decision_ref=decision_ref,
        )
        evidence = EvidenceObject(
            evidence_ref=f"E-{channel_id}",
            observed_outcome=observed_outcome,
            channel_id=channel_id,
            expectation_ref=expectation.id,
        )

        contradiction = self.detect_contradiction(expectation, evidence)
        if not contradiction.threshold_exceeded:
            raise ConstitutionalError("CE-1: no contradiction — cannot complete calibration cycle")

        surprise = self.quantify_surprise(contradiction, expectation)
        correction_delta = self.apply_correction(expectation, evidence, contradiction, surprise)
        assert_calibration_invariants(
            expectation=expectation,
            contradiction=contradiction,
            surprise=surprise,
            correction=correction_delta,
        )

        correction_object, crr, event = self.preserve_calibration(
            steward_id=steward_id,
            expectation=expectation,
            evidence=evidence,
            contradiction=contradiction,
            surprise=surprise,
            correction_delta=correction_delta,
            epoch=epoch,
            related_grr_ids=related_grr_ids,
            invariant_implications=invariant_implications,
        )

        return CE1PipelineResult(
            expectation=expectation,
            evidence=evidence,
            contradiction=contradiction,
            surprise=surprise,
            correction_delta=correction_delta,
            correction_object=correction_object,
            crr=crr,
            calibration_event=event,
        )

    def run_from_objects(
        self,
        *,
        steward_id: str,
        expectation: ExpectationObject,
        evidence: EvidenceObject,
        related_grr_ids: list[str] | None = None,
        invariant_implications: list[str] | None = None,
        epoch: int = 1,
    ) -> CE1PipelineResult:
        """Full F1–F5 pipeline from ExpectationObject + EvidenceObject."""
        if not evidence.expectation_ref:
            evidence = evidence.model_copy(update={"expectation_ref": expectation.id})

        contradiction = self.detect_contradiction(expectation, evidence)
        if not contradiction.threshold_exceeded:
            raise ConstitutionalError("CE-1: no contradiction — cannot complete calibration cycle")

        surprise = self.quantify_surprise(contradiction, expectation)
        correction_delta = self.apply_correction(expectation, evidence, contradiction, surprise)
        assert_calibration_invariants(
            expectation=expectation,
            contradiction=contradiction,
            surprise=surprise,
            correction=correction_delta,
        )

        correction_object, crr, event = self.preserve_calibration(
            steward_id=steward_id,
            expectation=expectation,
            evidence=evidence,
            contradiction=contradiction,
            surprise=surprise,
            correction_delta=correction_delta,
            epoch=epoch,
            related_grr_ids=related_grr_ids,
            invariant_implications=invariant_implications,
        )

        return CE1PipelineResult(
            expectation=expectation,
            evidence=evidence,
            contradiction=contradiction,
            surprise=surprise,
            correction_delta=correction_delta,
            correction_object=correction_object,
            crr=crr,
            calibration_event=event,
        )
