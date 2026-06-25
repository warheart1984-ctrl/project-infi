"""ECK-2 compliance — dual-pipeline requirements checklist."""

from __future__ import annotations

from pydantic import BaseModel, Field

from constitutional.eck2.runtime import load_eck2_pipeline
from constitutional.eck2.spec import ECK2_COMPLIANCE_REQUIREMENTS, ECK2_MIN_DRIFT_SYMMETRY_INDEX
from constitutional.jpss.drift import detect_jpss_drift
from constitutional.jpss.registers import (
    DECISION_REGISTER_DOC_ID,
    OUTCOME_REGISTER_DOC_ID,
    PERCEPTION_REGISTER_DOC_ID,
    REFLECTION_REGISTER_DOC_ID,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime


class ECK2ComplianceItem(BaseModel):
    requirement: str
    satisfied: bool = False
    detail: str = ""


class ECK2ComplianceReport(BaseModel):
    items: list[ECK2ComplianceItem] = Field(default_factory=list)
    compliant: bool = False

    @property
    def unsatisfied(self) -> list[ECK2ComplianceItem]:
        return [item for item in self.items if not item.satisfied]


def evaluate_eck2_compliance(csr: ConstitutionalStateRuntime) -> ECK2ComplianceReport:
    """Check ECK-2 compliance against normative requirements."""
    pipeline = load_eck2_pipeline(csr)
    drift = detect_jpss_drift(csr, decision_id=pipeline.formation.decision_id if pipeline else None)

    both_pipelines = pipeline is not None and pipeline.reconstruction.reconstructable
    registers_ok = bool(
        pipeline
        and pipeline.formation.decision_id
        and PERCEPTION_REGISTER_DOC_ID
        and DECISION_REGISTER_DOC_ID
        and OUTCOME_REGISTER_DOC_ID
        and REFLECTION_REGISTER_DOC_ID
    )
    drift_metrics = drift.drift_detectable and len(drift.findings) >= 8
    succession_ready = bool(
        pipeline
        and pipeline.drift_symmetry.symmetry_index >= ECK2_MIN_DRIFT_SYMMETRY_INDEX
        and both_pipelines
    )

    items = [
        ECK2ComplianceItem(
            requirement=ECK2_COMPLIANCE_REQUIREMENTS[0],
            satisfied=both_pipelines,
            detail="JPSS-F and ECK-R both executed with reconstructable result.",
        ),
        ECK2ComplianceItem(
            requirement=ECK2_COMPLIANCE_REQUIREMENTS[1],
            satisfied=registers_ok,
            detail="Formation registers populated for latest pipeline run.",
        ),
        ECK2ComplianceItem(
            requirement=ECK2_COMPLIANCE_REQUIREMENTS[2],
            satisfied=drift_metrics,
            detail=f"{len(drift.findings)} layer drift metrics exposed.",
        ),
        ECK2ComplianceItem(
            requirement=ECK2_COMPLIANCE_REQUIREMENTS[3],
            satisfied=succession_ready,
            detail=(
                f"Drift symmetry index {pipeline.drift_symmetry.symmetry_index:.2f}"
                if pipeline
                else "Dual-pipeline gate not yet satisfied."
            ),
        ),
    ]
    return ECK2ComplianceReport(items=items, compliant=all(item.satisfied for item in items))
