"""CRK-1 Amendment X — Threshold and Recalibration Governance."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.css2.governance import AdversarialReviewResult
from src.continuity.css2.recalibration_governance import (
    RecalibrationLegitimacyResult,
    TeamAdversarialReview,
    evaluate_threshold_delta_legitimacy,
)
from src.continuity.css2.threshold import RecalibrationRule, Threshold, ThresholdDelta
from src.continuity.css2.threshold_governance import (
    ThresholdGovernanceReport,
    audit_threshold_registry,
)

AMENDMENT_REFERENCE = "CRK-1 Amendment X — Threshold and Recalibration Governance"
AMENDMENT_ID = "CRK-1-AMENDMENT-X"

STEWARDSHIP_DEFINITION = (
    "Stewardship = governance of recalibration legitimacy. "
    "Stewards do not recalibrate; stewards govern when recalibration is allowed."
)


class CRK1ThresholdAmendmentReport(BaseModel):
    amendment: str = AMENDMENT_REFERENCE
    stewardship: str = STEWARDSHIP_DEFINITION
    threshold_audit: ThresholdGovernanceReport
    recalibration_legitimacy: RecalibrationLegitimacyResult | None = None
    compliant: bool = True
    notes: list[str] = Field(default_factory=list)


def assess_crk1_threshold_amendment(
    thresholds: list[Threshold],
    *,
    required_metrics: list[tuple[str, str]] | None = None,
    pending_delta: ThresholdDelta | None = None,
    rule: RecalibrationRule | None = None,
    adversarial_results: list[AdversarialReviewResult] | None = None,
) -> CRK1ThresholdAmendmentReport:
    """
    Amendment X compliance:
    - thresholds are explicit, with provenance
    - recalibration is Δ-threshold with legitimacy checks
    - constitutional changes are rule deltas (caller supplies separately)
    """
    audit = audit_threshold_registry(thresholds, required_metrics=required_metrics)
    notes: list[str] = []
    legitimacy: RecalibrationLegitimacyResult | None = None

    if audit.failures:
        notes.append("Threshold registry has governance failures.")

    for th in thresholds:
        if not th.created_by or not th.last_updated_by:
            notes.append(f"Threshold {th.id} missing provenance fields.")

    if pending_delta is not None:
        legitimacy = evaluate_threshold_delta_legitimacy(
            pending_delta,
            rule=rule,
            adversarial_results=adversarial_results,
        )
        if not legitimacy.legitimate:
            notes.extend(legitimacy.blockers)

    compliant = audit.ok and (legitimacy is None or legitimacy.legitimate)

    return CRK1ThresholdAmendmentReport(
        threshold_audit=audit,
        recalibration_legitimacy=legitimacy,
        compliant=compliant,
        notes=notes,
    )
