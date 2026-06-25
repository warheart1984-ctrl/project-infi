"""Stewardship Legitimacy Exam — public reconstructable competence certification."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.eck2.runtime import load_eck2_pipeline
from constitutional.eck2.spec import ECK2_MIN_DRIFT_SYMMETRY_INDEX
from constitutional.jpss.jpss_i_spec import ECK2_MIN_INVARIANT_DRIFT_INDEX
from constitutional.jpss.stewardship_balancing_test import load_stewardship_balancing_result
from constitutional.legitimacy.jpss_c_exam import JPSSCExamResult, load_jpss_c_exam_result
from constitutional.legitimacy.legitimacy_criterion import (
    LegitimacyCriterionResult,
    load_legitimacy_criterion_result,
)
from constitutional.legitimacy.legitimacy_protocol import (
    COMPETENCE_REQUIREMENTS,
    PLURALITY_REQUIREMENTS,
    RECEIPTS_REQUIREMENTS,
    StewardshipLegitimacyProtocolStatus,
    evaluate_protocol_pillars,
)
from constitutional.legitimacy.spec import MIN_LEGITIMACY_INDEX
from constitutional.runtime.runtime import ConstitutionalStateRuntime

LEGITIMACY_EXAM_STATE_ID = "legitimacy_exam__latest"


class LegitimacyExamResult(BaseModel):
    steward_id: str
    evaluated_at: datetime
    passed: bool
    legitimacy_index: float = Field(ge=0.0, le=1.0)
    jpss_formation_ready: bool = False
    jpss_i_balancing_passed: bool = False
    jpss_c_passed: bool = False
    reconstruction_criterion_passed: bool = False
    eck2_pipeline_ready: bool = False
    protocol: StewardshipLegitimacyProtocolStatus | None = None
    blockers: list[str] = Field(default_factory=list)


class StewardshipLegitimacyExam:
    """Public, reconstructable stewardship exam integrating JPSS, JPSS-I, JPSS-C."""

    def evaluate(self, csr: ConstitutionalStateRuntime, steward_id: str) -> LegitimacyExamResult:
        now = datetime.now(UTC).replace(microsecond=0)
        blockers: list[str] = []

        pipeline = load_eck2_pipeline(csr)
        jpss_formation_ready = pipeline is not None
        if not jpss_formation_ready:
            blockers.append("JPSS formation cycle not preserved.")

        eck2_ready = False
        if pipeline is not None:
            eck2_ready = (
                pipeline.reconstruction.reconstructable
                and pipeline.drift_symmetry.symmetry_index >= ECK2_MIN_DRIFT_SYMMETRY_INDEX
                and (pipeline.invariant_drift is None or pipeline.invariant_drift.drift_index >= ECK2_MIN_INVARIANT_DRIFT_INDEX)
            )
            if not eck2_ready:
                blockers.append("ECK-2 dual pipeline not reconstructable or drift thresholds not met.")

        balancing = load_stewardship_balancing_result(csr)
        jpss_i_passed = balancing is not None and balancing.passed
        if not jpss_i_passed:
            blockers.append("JPSS-I stewardship balancing test not passed.")

        jpss_c = load_jpss_c_exam_result(csr)
        jpss_c_passed = jpss_c is not None and jpss_c.passed
        if not jpss_c_passed:
            blockers.append("JPSS-C constitutional judgment exam not passed.")

        criterion = load_legitimacy_criterion_result(csr, steward_id)
        reconstruction_passed = criterion is not None and criterion.passed
        if not reconstruction_passed:
            blockers.append("Legitimacy reconstruction criterion not satisfied.")

        drift_competence = criterion is not None and "drift_detection_competence" in criterion.demonstrations_met
        if not drift_competence:
            blockers.append("Drift detection competence not demonstrated (Protocol §1.6).")

        from constitutional.legitimacy.legitimacy_process import load_legitimacy_process_result

        process = load_legitimacy_process_result(csr, steward_id)
        process_passed = process is not None and process.passed
        if not process_passed:
            blockers.append("Legitimacy Protocol v1.0 five-phase process not completed.")

        competence_met: list[str] = []
        if jpss_formation_ready:
            competence_met.append("jpss_judgment_exam")
        if jpss_i_passed:
            competence_met.append("jpss_i_adaptive_invariant_exam")
        if jpss_c_passed:
            competence_met.append("jpss_c_constitutional_exam")
        if reconstruction_passed:
            competence_met.extend(
                [
                    "constitutional_reasoning_reconstruction",
                    "consequence_modeling",
                ]
            )
        if drift_competence:
            competence_met.append("drift_detection_competence")
        if process_passed:
            competence_met.append("legitimacy_process_v1")

        receipts_met: list[str] = []
        if pipeline is not None:
            receipts_met.append("decisions_recorded")
            if pipeline.reconstruction.reconstructable:
                receipts_met.append("reasoning_reconstructable")
                receipts_met.append("survivable_by_future_stewards")
            receipts_met.append("reasoning_criticizable")

        from constitutional.legitimacy.legitimacy_register import load_legitimacy_register

        register = load_legitimacy_register(csr)
        plurality_met: list[str] = []
        active_count = len(register.active_stewards())
        if active_count >= 1:
            plurality_met.append("distributed_certified_stewards")
        if active_count >= register.minimum_plurality:
            plurality_met.extend(
                [
                    "overlapping_reconstruction_competence",
                    "no_unilateral_invariant_alteration",
                ]
            )
        if any(entry.certified_by for entry in register.entries):
            plurality_met.append("prior_cohort_certification")

        protocol = evaluate_protocol_pillars(
            competence_met=competence_met,
            receipts_met=receipts_met,
            plurality_met=plurality_met,
        )

        checks = [
            jpss_formation_ready,
            jpss_i_passed,
            jpss_c_passed,
            reconstruction_passed,
            drift_competence,
            process_passed,
            eck2_ready,
        ]
        legitimacy_index = sum(1 for check in checks if check) / len(checks)
        passed = legitimacy_index >= MIN_LEGITIMACY_INDEX and protocol.competence.satisfied

        return LegitimacyExamResult(
            steward_id=steward_id,
            evaluated_at=now,
            passed=passed,
            legitimacy_index=legitimacy_index,
            jpss_formation_ready=jpss_formation_ready,
            jpss_i_balancing_passed=jpss_i_passed,
            jpss_c_passed=jpss_c_passed,
            reconstruction_criterion_passed=reconstruction_passed,
            eck2_pipeline_ready=eck2_ready,
            protocol=protocol,
            blockers=blockers,
        )


def run_legitimacy_exam(csr: ConstitutionalStateRuntime, steward_id: str) -> LegitimacyExamResult:
    result = StewardshipLegitimacyExam().evaluate(csr, steward_id)
    csr.put_domain_doc(LEGITIMACY_EXAM_STATE_ID, "legitimacy_exam_result", result)
    return result


def load_legitimacy_exam_result(csr: ConstitutionalStateRuntime) -> LegitimacyExamResult | None:
    try:
        doc = csr.get_domain_doc(LEGITIMACY_EXAM_STATE_ID, LegitimacyExamResult)
        assert isinstance(doc, LegitimacyExamResult)
        return doc
    except KeyError:
        return None
