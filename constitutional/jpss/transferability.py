"""JPSS-II Transferability — dual validity axes and evidence hierarchy."""

from __future__ import annotations

from datetime import UTC, datetime

from constitutional.jpss.jpss_ii_models import (
    EvidenceTierScore,
    JPSSIITransferabilityReport,
    ValidityAxisScore,
)
from constitutional.jpss.competency import assess_steward_competency
from constitutional.jpss.constitutional_register import load_constitutional_register
from constitutional.jpss.invariant_drift import detect_invariant_drift, load_invariant_drift_state
from constitutional.jpss.jpss_ii_spec import (
    JPSS_II_EVIDENCE_HIERARCHY,
    JPSS_II_MIN_TRANSFERABILITY_INDEX,
    JPSS_II_TRANSFERABILITY_LAW,
    JPSS_II_VALIDITY_AXES,
    JPSS_RECURSIVE_CONDITION,
)
from constitutional.jpss.runtime import load_jpss_cycle
from constitutional.jpss.spec import JPSS_CANONICAL_CYCLE, JPSS_INVARIANTS
from constitutional.legitimacy.jpss_c_exam import load_jpss_c_exam_result
from constitutional.legitimacy.jpss_c_spec import JPSS_C_GOVERNANCE_CHAIN
from constitutional.runtime.runtime import ConstitutionalStateRuntime

TRANSFERABILITY_STATE_ID = "jpss_ii_transferability__latest"


def _evaluate_epistemic_validity() -> ValidityAxisScore:
    """Theory correctness: spec completeness and internal coherence."""
    checks = [
        len(JPSS_CANONICAL_CYCLE) == 8,
        len(JPSS_INVARIANTS) >= 5,
        len(JPSS_C_GOVERNANCE_CHAIN) == 5,
        bool(JPSS_II_TRANSFERABILITY_LAW),
    ]
    from constitutional.legitimacy.jpss_c_spec import JPSS_C_CANONICAL_CYCLE

    checks.append(len(JPSS_C_CANONICAL_CYCLE) == 8)
    score = sum(1 for ok in checks if ok) / len(checks)
    return ValidityAxisScore(
        axis="epistemic_validity",
        score=round(score, 4),
        passed=score >= JPSS_II_MIN_TRANSFERABILITY_INDEX,
        evidence=[
            "JPSS canonical cycle defined",
            "JPSS invariants defined",
            "JPSS-C governance chain defined",
            "Transferability law articulated",
        ],
    )


def evaluate_jpss_transferability(csr: ConstitutionalStateRuntime) -> JPSSIITransferabilityReport:
    """Evaluate whether JPSS satisfies its own stewardship requirements."""
    from constitutional.eck2.compliance import evaluate_eck2_compliance
    from constitutional.eck2.runtime import load_eck2_pipeline

    now = datetime.now(UTC).replace(microsecond=0)
    epistemic = _evaluate_epistemic_validity()

    cycle = load_jpss_cycle(csr)
    pipeline = load_eck2_pipeline(csr)
    competency = assess_steward_competency(csr)
    jpss_c = load_jpss_c_exam_result(csr)
    constitutional_register = load_constitutional_register(csr)
    compliance = evaluate_eck2_compliance(csr)
    invariant_drift = load_invariant_drift_state(csr) or detect_invariant_drift(csr)

    stewardship_checks = [
        cycle is not None,
        pipeline is not None and pipeline.reconstruction.reconstructable,
        competency.dual_pipeline_demonstrated,
        jpss_c is not None and jpss_c.passed,
        len(constitutional_register.entries) > 0 or jpss_c is not None,
        not invariant_drift.drift_detected,
    ]
    stewardship_score = sum(1 for ok in stewardship_checks if ok) / len(stewardship_checks)
    stewardship = ValidityAxisScore(
        axis="stewardship_validity",
        score=round(stewardship_score, 4),
        passed=stewardship_score >= JPSS_II_MIN_TRANSFERABILITY_INDEX,
        evidence=[name for name, ok in zip(
            [
                "jpss_cycle_preserved",
                "eck2_reconstructable",
                "dual_pipeline_competency",
                "jpss_c_exam_passed",
                "constitutional_decisions_recorded",
                "identity_preserved_no_invariant_drift",
            ],
            stewardship_checks,
        ) if ok],
    )

    evidence_tiers: list[EvidenceTierScore] = [
        EvidenceTierScore(tier="theory", satisfied=True, detail="Normative specs and constants present."),
        EvidenceTierScore(
            tier="case_studies",
            satisfied=cycle is not None,
            detail="JPSS formation cycle recorded." if cycle else "No preserved judgment cycle.",
        ),
        EvidenceTierScore(
            tier="cross_domain_validation",
            satisfied=bool(
                cycle
                and pipeline
                and (jpss_c is not None or len(constitutional_register.entries) > 0)
            ),
            detail="Adaptive, invariant, and constitutional layers all evidenced.",
        ),
        EvidenceTierScore(
            tier="independent_steward",
            satisfied=competency.passed and (jpss_c.passed if jpss_c else False),
            detail="Steward competency and JPSS-C exam passed.",
        ),
        EvidenceTierScore(
            tier="independent_application",
            satisfied=bool(pipeline and compliance.compliant),
            detail="Dual-pipeline ECK-2 compliance satisfied.",
        ),
        EvidenceTierScore(
            tier="independent_improvement",
            satisfied=bool(
                len(constitutional_register.entries) > 0
                and not invariant_drift.drift_detected
            ),
            detail="Constitutional boundary decisions recorded without identity collapse.",
        ),
    ]

    tier_score = sum(1 for tier in evidence_tiers if tier.satisfied) / len(evidence_tiers)
    transferability_index = round((epistemic.score + stewardship.score + tier_score) / 3, 4)

    continuity_marks = {
        "correct": epistemic.passed,
        "reconstructable": pipeline is not None and pipeline.reconstruction.reconstructable,
        "transferable": stewardship.passed,
        "evolvable": len(constitutional_register.entries) > 0,
        "identity_preserving": not invariant_drift.drift_detected,
    }

    report = JPSSIITransferabilityReport(
        epistemic_validity=epistemic,
        stewardship_validity=stewardship,
        evidence_tiers=evidence_tiers,
        transferability_index=transferability_index,
        transferable=transferability_index >= JPSS_II_MIN_TRANSFERABILITY_INDEX
        and epistemic.passed
        and stewardship.passed,
        continuity_marks=continuity_marks,
        captured_at=now,
    )
    csr.put_domain_doc(TRANSFERABILITY_STATE_ID, "jpss_ii_transferability", report)
    if pipeline is not None:
        from constitutional.eck2.runtime import ECK2_PIPELINE_STATE_ID

        updated = pipeline.model_copy(update={"transferability": report})
        csr.put_domain_doc(ECK2_PIPELINE_STATE_ID, "eck2_pipeline", updated)
    return report


def load_transferability_report(csr: ConstitutionalStateRuntime) -> JPSSIITransferabilityReport | None:
    try:
        doc = csr.get_domain_doc(TRANSFERABILITY_STATE_ID, JPSSIITransferabilityReport)
        assert isinstance(doc, JPSSIITransferabilityReport)
        return doc
    except KeyError:
        return None
