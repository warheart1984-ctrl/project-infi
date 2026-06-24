"""Build CRR-1 wire receipts from CalibrationResult and pipeline outputs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from src.crk1.calibration_pipeline import CalibrationResult, calibration_result_from_ce1
from src.crk1.correction_engine_ce1 import CE1PipelineResult
from src.crk1.correction_object import CalibrationCorrectionReceipt
from src.crk1.schema_validator import CRK1SchemaValidator


def _coerce_calibration_result(result: Any) -> CalibrationResult:
    if isinstance(result, CalibrationResult):
        return result
    if isinstance(result, CE1PipelineResult):
        return calibration_result_from_ce1(result)
    if isinstance(result, CalibrationCorrectionReceipt):
        correction = result.correction
        from src.crk1.calibration_objects import (
            ContradictionObject,
            CorrectionDeltaObject,
            EvidenceObject,
            ExpectationObject,
            SurpriseObject,
        )

        expectation = ExpectationObject(
            expected_outcome=correction.expectation.expected_outcome,
            expected_confidence=correction.expectation.expected_confidence,
            assumptions=list(correction.expectation.assumptions),
            model_ref=correction.expectation.model_ref,
        )
        evidence = EvidenceObject(
            evidence_ref=correction.evidence.evidence_ref,
            observed_outcome=correction.evidence.observed_outcome,
            channel_id=correction.evidence.channel_id,
            evidence_strength=correction.evidence.evidence_strength,
        )
        contradiction = ContradictionObject(
            expectation_ref=expectation.id,
            evidence_ref=evidence.id,
            contradiction_delta=correction.contradiction.contradiction_delta,
            prediction_error_vector=list(correction.contradiction.prediction_error_vector),
            threshold_exceeded=correction.contradiction.threshold_exceeded,
        )
        surprise = SurpriseObject(
            contradiction_ref=contradiction.id,
            expectation_ref=expectation.id,
            surprise_intensity=correction.surprise.surprise_intensity,
            surprise_function=correction.surprise.surprise_function,
            prior_confidence=correction.surprise.prior_confidence,
        )
        correction_delta = CorrectionDeltaObject(
            surprise_ref=surprise.id,
            update_rule_applied=correction.correction.update_rule_applied,
            assumptions_removed=list(correction.correction.assumptions_removed),
            assumptions_added=list(correction.correction.assumptions_added),
            model_shift=correction.correction.model_shift,
            new_confidence=correction.correction.new_confidence,
        )
        return CalibrationResult(
            expectation=expectation,
            evidence=evidence,
            contradiction=contradiction,
            surprise=surprise,
            correction=correction_delta,
            calibration_delta=correction.calibration.calibration_delta,
            future_implications=list(correction.linkage.lineage_refs),
            steward_id=result.created_by,
            crr_id=result.id,
        )
    raise TypeError(f"unsupported calibration result type: {type(result)!r}")


def build_crr1(
    result: CalibrationResult | CE1PipelineResult | CalibrationCorrectionReceipt,
    *,
    validate: bool = True,
    schema_validator: CRK1SchemaValidator | None = None,
) -> dict[str, Any]:
    """
    Build a Calibration Reconstruction Receipt (CRR-1) from a CalibrationResult.

    Accepts CalibrationResult, CE1PipelineResult, or CalibrationCorrectionReceipt.
    """
    cal = _coerce_calibration_result(result)
    exp = cal.expectation
    ev = cal.evidence
    contradiction = cal.contradiction
    surprise = cal.surprise
    corr = cal.correction

    crr_id = cal.crr_id or f"CRR-1-{uuid.uuid4().hex[:8].upper()}"

    crr1: dict[str, Any] = {
        "schema_version": "1.0",
        "receipt_type": "CRR-1",
        "timestamp_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "steward_id": cal.steward_id,
        "crr_id": crr_id,
        "expected_outcome": exp.expected_outcome,
        "expected_confidence": exp.expected_confidence,
        "observed_outcome": ev.observed_outcome,
        "evidence_strength": ev.evidence_strength,
        "contradiction_delta": contradiction.delta,
        "surprise_magnitude": surprise.magnitude,
        "surprise_basis": surprise.basis,
        "correction_summary": corr.summary,
        "calibration_change": cal.calibration_delta,
        "calibration_delta": cal.calibration_delta,
        "future_implications": list(cal.future_implications),
        "assumptions": list(exp.assumptions),
        "reality_channel": ev.channel_id,
        "links": {
            "expectation_id": exp.id,
            "evidence_id": ev.id,
            "decision_id": cal.decision_id,
            "crr_id": crr_id,
        },
    }

    if validate:
        validator = schema_validator or CRK1SchemaValidator()
        validator.validate("calibration_reconstruction_receipt", crr1)

    return crr1
