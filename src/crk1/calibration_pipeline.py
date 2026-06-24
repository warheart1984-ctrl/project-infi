"""Calibration event pipeline — MVCD and Continuity Proof-of-Life Test (C-PoLT)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from src.crk1.continuity_failure_equation import CFEInputs, evaluate_continuity_failure
from src.crk1.correction_object import (
    CalibrationCorrectionReceipt,
    CalibrationSection,
    ContradictionSection,
    CorrectionObject,
    CorrectionSection,
    EvidenceSection,
    ExpectationSection,
    IntegritySection,
    LinkageSection,
    SurpriseSection,
    _sha256_payload,
)
from src.crk1.errors import ConstitutionalError
from src.crk1.stewardship_calibration_test import SCTInputs, run_stewardship_calibration_test

from src.crk1.calibration_objects import (
    ContradictionObject,
    CorrectionDeltaObject,
    EvidenceObject,
    ExpectationObject,
    SurpriseObject,
)

TestResult = Literal["PASS", "FAIL"]


@dataclass
class CalibrationResult:
    """
    Unified calibration pipeline output for CRR-1 builder and CLG-1 ingestion.

    Fields align with the calibration pipeline steps:
      expectation → evidence → contradiction → surprise → correction → calibration_delta
    """

    expectation: ExpectationObject
    evidence: EvidenceObject
    contradiction: ContradictionObject
    surprise: SurpriseObject
    correction: CorrectionDeltaObject
    calibration_delta: float
    future_implications: list[str] = field(default_factory=list)
    steward_id: str = "unknown"
    decision_id: str | None = None
    crr_id: str | None = None


def calibration_result_from_ce1(result: Any) -> CalibrationResult:
    """Map CE-1 pipeline result to CalibrationResult."""
    from src.crk1.correction_engine_ce1 import CE1PipelineResult

    if not isinstance(result, CE1PipelineResult):
        raise TypeError("expected CE1PipelineResult")

    shift = result.correction_delta.model_shift
    calibration_delta = float(shift) if isinstance(shift, (int, float)) else 0.0

    return CalibrationResult(
        expectation=result.expectation,
        evidence=result.evidence,
        contradiction=result.contradiction,
        surprise=result.surprise,
        correction=result.correction_delta,
        calibration_delta=calibration_delta,
        future_implications=[f"channel:{result.evidence.channel_id}"],
        steward_id=result.crr.created_by,
        decision_id=result.expectation.decision_ref or None,
        crr_id=result.crr.id,
    )


@dataclass
class CalibrationLineageGraph:
    """CLG-1 — links calibration events for reconstruction."""

    crr_ids: list[str] = field(default_factory=list)
    correction_ids: list[str] = field(default_factory=list)

    def link(self, crr: CalibrationCorrectionReceipt) -> None:
        self.crr_ids.append(crr.id)
        self.correction_ids.append(crr.correction.id)


@dataclass
class CalibrationPipelineResult:
    correction: CorrectionObject
    crr: CalibrationCorrectionReceipt
    sct_report: dict[str, Any]
    cfe_report: dict[str, Any]
    clg: CalibrationLineageGraph

    def to_dict(self) -> dict[str, Any]:
        return {
            "correction": self.correction.to_dict(),
            "crr": self.crr.to_dict(),
            "sct": self.sct_report,
            "cfe": self.cfe_report,
            "clg": {
                "crr_ids": list(self.clg.crr_ids),
                "correction_ids": list(self.clg.correction_ids),
            },
        }


def _numeric(value: float | str) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def surprise_magnitude(delta: float, confidence: float) -> float:
    """R4 / Step 4 — S = g(Δ, confidence)."""
    return max(0.0, delta * confidence)


def run_calibration_pipeline(
    *,
    steward_id: str,
    channel_id: str,
    expected_outcome: float | str,
    observed_outcome: float | str,
    expected_confidence: float,
    assumptions: list[str] | None = None,
    model_ref: str = "mvcd-default",
    contradiction_threshold: float = 0.01,
    update_rule: str = "bayesian_update",
    epoch: int = 1,
    lineage_refs: list[str] | None = None,
    clg: CalibrationLineageGraph | None = None,
) -> CalibrationPipelineResult:
    """
    Steps 1–7: Expectation → Evidence → Contradiction → Surprise → Correction →
    Calibration → Preservation (CRR-1 + CLG-1).
    """
    # Step 1 — Expectation
    expectation = ExpectationSection(
        expected_outcome=expected_outcome,
        expected_confidence=expected_confidence,
        assumptions=list(assumptions or []),
        model_ref=model_ref,
    )

    # Step 2 — Evidence
    evidence_payload = {
        "evidence_ref": f"E-{channel_id}",
        "observed_outcome": observed_outcome,
        "channel_id": channel_id,
    }
    evidence = EvidenceSection(
        evidence_ref=str(evidence_payload["evidence_ref"]),
        observed_outcome=observed_outcome,
        channel_id=channel_id,
        evidence_strength=1.0,
    )

    # Step 3 — Contradiction
    exp_num = _numeric(expected_outcome)
    obs_num = _numeric(observed_outcome)
    delta = abs(exp_num - obs_num)
    threshold_exceeded = delta > contradiction_threshold
    contradiction = ContradictionSection(
        contradiction_delta=delta,
        prediction_error_vector=[obs_num - exp_num],
        threshold_exceeded=threshold_exceeded,
    )

    if not threshold_exceeded:
        raise ConstitutionalError("MVCD R3: no contradiction — pipeline cannot produce correction")

    # Step 4 — Surprise
    surprise_intensity = surprise_magnitude(delta, expected_confidence)
    surprise = SurpriseSection(
        surprise_intensity=surprise_intensity,
        surprise_function="delta_times_confidence",
        prior_confidence=expected_confidence,
    )

    # Step 5 — Correction
    new_confidence = max(0.0, min(1.0, expected_confidence - delta * 0.1))
    model_shift = obs_num - exp_num
    correction_section = CorrectionSection(
        update_rule_applied=update_rule,
        assumptions_removed=[a for a in (assumptions or []) if "optimistic" in a.lower()],
        assumptions_added=[f"observed_via_{channel_id}"],
        model_shift=model_shift,
        new_confidence=new_confidence,
    )

    # Step 6 — Calibration
    calibration_delta = model_shift
    calibration = CalibrationSection(
        calibration_delta=calibration_delta,
        bias_reduction=abs(model_shift) * 0.5,
        predictive_accuracy_change=0.01 if threshold_exceeded else 0.0,
    )

    # Integrity + linkage
    integrity = IntegritySection(
        steward_id=steward_id,
        evidence_hash=_sha256_payload(evidence_payload),
        signature=f"steward:{steward_id}",
    )
    linkage = LinkageSection(lineage_refs=list(lineage_refs or []))

    correction = CorrectionObject(
        expectation=expectation,
        evidence=evidence,
        contradiction=contradiction,
        surprise=surprise,
        correction=correction_section,
        calibration=calibration,
        integrity=integrity,
        linkage=linkage,
    )

    # Step 7 — Preservation (CRR-1)
    crr = CalibrationCorrectionReceipt.from_correction(
        correction,
        created_by=steward_id,
        epoch=epoch,
    )

    graph = clg or CalibrationLineageGraph()
    graph.link(crr)

    sct = run_stewardship_calibration_test(
        SCTInputs(
            evidence=obs_num,
            calibration_prior=exp_num,
            calibration_post=obs_num,
            contradiction_magnitude=delta,
            surprise_response=surprise_intensity,
        ),
        evidence_trace_id=evidence.evidence_ref,
    )

    cfe = evaluate_continuity_failure(
        CFEInputs(
            ce=1.0,
            contradiction_magnitude=delta,
            surprise_response=surprise_intensity,
            calibration_delta=calibration_delta,
        )
    )

    return CalibrationPipelineResult(
        correction=correction,
        crr=crr,
        sct_report=sct.to_dict(),
        cfe_report=cfe.to_dict(),
        clg=graph,
    )


@dataclass
class CPoLTReport:
    """Continuity Proof-of-Life Test — seven-test suite."""

    tests: dict[str, TestResult]
    overall: TestResult

    def to_dict(self) -> dict[str, Any]:
        return {"tests": dict(self.tests), "overall": self.overall}


def run_continuity_proof_of_life(
    *,
    steward_id: str = "S-MVCD-001",
    channel_id: str = "reality-channel-1",
) -> tuple[CalibrationPipelineResult, CPoLTReport]:
    """
    C-PoLT — minimal viable continuity demonstration end-to-end.

    Expectation 1.0, observed 0.3 → contradiction → surprise → correction → CRR-1.
    """
    result = run_calibration_pipeline(
        steward_id=steward_id,
        channel_id=channel_id,
        expected_outcome=1.0,
        observed_outcome=0.3,
        expected_confidence=0.9,
        assumptions=["optimistic_baseline"],
        model_ref="mvcd-v0.1",
        contradiction_threshold=0.01,
    )

    tests: dict[str, TestResult] = {}

    # Test 1 — Expectation
    tests["expectation"] = (
        "PASS" if result.correction.expectation.expected_confidence > 0 else "FAIL"
    )

    # Test 2 — Reality contact
    tests["reality_contact"] = (
        "PASS" if result.correction.evidence.channel_id and result.correction.integrity.evidence_hash else "FAIL"
    )

    # Test 3 — Contradiction
    tests["contradiction"] = (
        "PASS" if result.correction.contradiction.threshold_exceeded else "FAIL"
    )

    # Test 4 — Surprise
    tests["surprise"] = (
        "PASS" if result.correction.surprise.surprise_intensity > 0 else "FAIL"
    )

    # Test 5 — Correction
    tests["correction"] = (
        "PASS" if abs(result.correction.correction.model_shift) > 0 else "FAIL"
    )

    # Test 6 — Calibration preservation
    tests["calibration_preservation"] = (
        "PASS" if result.crr.id and result.crr.id.startswith("CRR-1") else "FAIL"
    )

    # Test 7 — Reconstruction
    replay = result.crr.reconstruct()
    tests["reconstruction"] = (
        "PASS"
        if replay.get("calibration_delta") == result.correction.calibration.calibration_delta
        and replay.get("expectation")
        else "FAIL"
    )

    overall: TestResult = "PASS" if all(value == "PASS" for value in tests.values()) else "FAIL"
    return result, CPoLTReport(tests=tests, overall=overall)
