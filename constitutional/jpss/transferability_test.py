"""JPSS Transferability Test — five-component steward survivability validation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from constitutional.jpss.competency import assess_steward_competency
from constitutional.jpss.constitutional_drift import detect_constitutional_drift
from constitutional.jpss.constitutional_register import load_constitutional_register
from constitutional.jpss.invariant_drift import detect_invariant_drift, load_invariant_drift_state
from constitutional.jpss.jpss_ii_models import JPSSIITransferabilityReport
from constitutional.jpss.transferability import evaluate_jpss_transferability, load_transferability_report
from constitutional.legitimacy.jpss_c_exam import load_jpss_c_exam_result
from constitutional.legitimacy.jpss_c_spec import (
    JPSS_C_TRANSFERABILITY_PASSING_CONDITION,
    JPSS_C_TRANSFERABILITY_TEST_COMPONENTS,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

TRANSFERABILITY_TEST_STATE_ID = "jpss_c_transferability_test__latest"


class TransferabilityComponentResult(BaseModel):
    component: str
    passed: bool = False
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: str = ""


class JPSTransferabilityTestReport(BaseModel):
    """Five-component test: JPSS survives contact with a steward who never met founders."""

    passing_condition: str = JPSS_C_TRANSFERABILITY_PASSING_CONDITION
    components: list[TransferabilityComponentResult] = Field(default_factory=list)
    composite_score: float = Field(default=0.0, ge=0.0, le=1.0)
    passed: bool = False
    base_report: JPSSIITransferabilityReport | None = None
    captured_at: datetime | None = None


def run_jpss_transferability_test(csr: ConstitutionalStateRuntime) -> JPSTransferabilityTestReport:
    from constitutional.eck2.runtime import load_eck2_pipeline

    base = load_transferability_report(csr) or evaluate_jpss_transferability(csr)
    pipeline = load_eck2_pipeline(csr)
    competency = assess_steward_competency(csr)
    jpss_c = load_jpss_c_exam_result(csr)
    constitutional = load_constitutional_register(csr)
    invariant_drift = load_invariant_drift_state(csr) or detect_invariant_drift(csr)
    constitutional_drift = detect_constitutional_drift(csr)

    components: list[TransferabilityComponentResult] = []

    reconstruction_ok = pipeline is not None and pipeline.reconstruction.reconstructable
    components.append(
        TransferabilityComponentResult(
            component="reconstruction_test",
            passed=reconstruction_ok,
            score=1.0 if reconstruction_ok else 0.0,
            evidence="ECK-R reconstructs formation from registers." if reconstruction_ok else "Reconstruction gaps present.",
        )
    )

    application_ok = competency.dual_pipeline_demonstrated and competency.passed
    components.append(
        TransferabilityComponentResult(
            component="application_test",
            passed=application_ok,
            score=competency.overall_score if application_ok else 0.0,
            evidence="Steward applied dual-pipeline JPSS competently." if application_ok else "Application competency insufficient.",
        )
    )

    critique_ok = jpss_c is not None and jpss_c.passed
    components.append(
        TransferabilityComponentResult(
            component="critique_test",
            passed=critique_ok,
            score=1.0 if critique_ok else 0.0,
            evidence="JPSS-C exam demonstrates drift and boundary critique." if critique_ok else "Critique capability not demonstrated.",
        )
    )

    extension_ok = len(constitutional.entries) > 0 and not invariant_drift.drift_detected
    components.append(
        TransferabilityComponentResult(
            component="extension_test",
            passed=extension_ok,
            score=1.0 if extension_ok else 0.0,
            evidence="Constitutional extensions recorded without identity collapse."
            if extension_ok
            else "Extension blocked or caused drift.",
        )
    )

    stewardship_ok = base.stewardship_validity.passed and not constitutional_drift.drift_detected
    components.append(
        TransferabilityComponentResult(
            component="stewardship_test",
            passed=stewardship_ok,
            score=base.stewardship_validity.score if stewardship_ok else base.stewardship_validity.score * 0.5,
            evidence="Purpose and core values preserved under new steward."
            if stewardship_ok
            else "Stewardship or constitutional drift failing.",
        )
    )

    assert len(components) == len(JPSS_C_TRANSFERABILITY_TEST_COMPONENTS)

    composite = round(sum(c.score for c in components) / len(components), 4)
    passed = all(c.passed for c in components) and base.transferable

    report = JPSTransferabilityTestReport(
        components=components,
        composite_score=composite,
        passed=passed,
        base_report=base,
        captured_at=base.captured_at,
    )
    csr.put_domain_doc(TRANSFERABILITY_TEST_STATE_ID, "jpss_c_transferability_test", report)
    return report


def load_jpss_transferability_test(csr: ConstitutionalStateRuntime) -> JPSTransferabilityTestReport | None:
    try:
        doc = csr.get_domain_doc(TRANSFERABILITY_TEST_STATE_ID, JPSTransferabilityTestReport)
        assert isinstance(doc, JPSTransferabilityTestReport)
        return doc
    except KeyError:
        return None
