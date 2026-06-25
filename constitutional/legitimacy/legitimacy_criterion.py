"""Legitimacy Criterion — authority by reconstruction demonstrations (Protocol §1)."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.legitimacy.spec import LEGITIMACY_CRITERION_DEMONSTRATIONS, MIN_LEGITIMACY_INDEX
from constitutional.runtime.runtime import ConstitutionalStateRuntime

RECONSTRUCTION_DEMO_STATE_ID = "legitimacy_reconstruction_demo__latest"


class ReconstructionDemonstration(BaseModel):
    """Public demonstration that a steward can reconstruct continuity before altering it."""

    steward_id: str
    demonstrated_at: datetime
    purpose_reconstructed: bool = False
    identity_reconstructed: bool = False
    historical_judgment_reconstructed: bool = False
    constitutional_reasoning_reconstructed: bool = False
    consequences_simulated: bool = False
    drift_detection_competence: bool = False
    evidence_refs: list[str] = Field(default_factory=list)
    proposed_change_summary: str | None = None

    def as_demonstration_map(self) -> dict[str, bool]:
        return {
            "purpose_reconstruction": self.purpose_reconstructed,
            "identity_reconstruction": self.identity_reconstructed,
            "judgment_reconstruction": self.historical_judgment_reconstructed,
            "constitutional_reasoning_reconstruction": self.constitutional_reasoning_reconstructed,
            "consequence_simulation": self.consequences_simulated,
            "drift_detection_competence": self.drift_detection_competence,
        }


class LegitimacyCriterionResult(BaseModel):
    steward_id: str
    evaluated_at: datetime
    legitimacy_index: float = Field(ge=0.0, le=1.0)
    passed: bool
    demonstrations_met: list[str] = Field(default_factory=list)
    demonstrations_missing: list[str] = Field(default_factory=list)


def evaluate_reconstruction_demonstration(demo: ReconstructionDemonstration) -> LegitimacyCriterionResult:
    demo_map = demo.as_demonstration_map()
    met = [key for key in LEGITIMACY_CRITERION_DEMONSTRATIONS if demo_map.get(key, False)]
    missing = [key for key in LEGITIMACY_CRITERION_DEMONSTRATIONS if key not in met]
    total = len(LEGITIMACY_CRITERION_DEMONSTRATIONS)
    index = len(met) / total if total else 1.0
    return LegitimacyCriterionResult(
        steward_id=demo.steward_id,
        evaluated_at=demo.demonstrated_at,
        legitimacy_index=index,
        passed=index >= MIN_LEGITIMACY_INDEX,
        demonstrations_met=met,
        demonstrations_missing=missing,
    )


def record_reconstruction_demonstration(
    csr: ConstitutionalStateRuntime,
    demo: ReconstructionDemonstration,
) -> LegitimacyCriterionResult:
    result = evaluate_reconstruction_demonstration(demo)
    csr.put_domain_doc(
        f"{RECONSTRUCTION_DEMO_STATE_ID}__{demo.steward_id}",
        "legitimacy_reconstruction_demo",
        demo,
    )
    csr.put_domain_doc(
        f"legitimacy_criterion__{demo.steward_id}",
        "legitimacy_criterion_result",
        result,
    )
    return result


def load_reconstruction_demonstration(
    csr: ConstitutionalStateRuntime,
    steward_id: str,
) -> ReconstructionDemonstration | None:
    try:
        doc = csr.get_domain_doc(
            f"{RECONSTRUCTION_DEMO_STATE_ID}__{steward_id}",
            ReconstructionDemonstration,
        )
        assert isinstance(doc, ReconstructionDemonstration)
        return doc
    except KeyError:
        return None


def load_legitimacy_criterion_result(
    csr: ConstitutionalStateRuntime,
    steward_id: str,
) -> LegitimacyCriterionResult | None:
    try:
        doc = csr.get_domain_doc(f"legitimacy_criterion__{steward_id}", LegitimacyCriterionResult)
        assert isinstance(doc, LegitimacyCriterionResult)
        return doc
    except KeyError:
        return None


def passing_reconstruction_demonstration(steward_id: str) -> ReconstructionDemonstration:
    """Reference demonstration satisfying all Protocol §1 criteria."""
    return ReconstructionDemonstration(
        steward_id=steward_id,
        demonstrated_at=datetime.now(UTC).replace(microsecond=0),
        purpose_reconstructed=True,
        identity_reconstructed=True,
        historical_judgment_reconstructed=True,
        constitutional_reasoning_reconstructed=True,
        consequences_simulated=True,
        drift_detection_competence=True,
        evidence_refs=[
            "eck2_pipeline",
            "invariant_register",
            "jpss_cycle",
            "legitimacy_drift",
            "invariant_drift",
        ],
    )
