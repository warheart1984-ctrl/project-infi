"""Recalibration governance — ThresholdDelta legitimacy (CSS-2 §2.4)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.css2.threshold import RecalibrationRule, ThresholdDelta


class TeamAdversarialReview(BaseModel):
    team: str
    passed: bool
    notes: str = ""


class RecalibrationLegitimacyResult(BaseModel):
    legitimate: bool
    threshold_delta: ThresholdDelta
    adversarial_reviews: list[TeamAdversarialReview] = Field(default_factory=list)
    invariant_violations: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


def evaluate_threshold_delta_legitimacy(
    delta: ThresholdDelta,
    *,
    rule: RecalibrationRule | None = None,
    adversarial_results: list[TeamAdversarialReview] | None = None,
    violated_invariants: list[str] | None = None,
) -> RecalibrationLegitimacyResult:
    """
    A ThresholdDelta is legitimate only if:
    - it passes adversarial review (when required), and
    - it does not violate non-derogable invariants.
    """
    active_rule = rule or RecalibrationRule(
        name="default",
        intent="Stewards govern when recalibration is allowed.",
    )
    reviews = adversarial_results or []
    violations = violated_invariants or []
    blockers: list[str] = []

    if not delta.is_recalibration:
        blockers.append("No effective threshold change — not recalibration.")

    if active_rule.requires_adversarial_review:
        required = set(active_rule.adversarial_teams)
        passed_teams = {r.team for r in reviews if r.passed}
        missing = required - passed_teams
        if missing:
            blockers.append(f"Adversarial review incomplete: missing {sorted(missing)}")
        failed = [r.team for r in reviews if not r.passed]
        if failed:
            blockers.append(f"Adversarial review failed: {failed}")

    for inv in violations:
        if inv in active_rule.non_derogable_invariants:
            blockers.append(f"Violates non-derogable invariant: {inv}")

    if active_rule.requires_evidence and not delta.rationale.strip():
        blockers.append("Recalibration requires documented rationale (evidence).")

    return RecalibrationLegitimacyResult(
        legitimate=not blockers,
        threshold_delta=delta,
        adversarial_reviews=reviews,
        invariant_violations=violations,
        blockers=blockers,
    )


def apply_approved_delta(
    delta: ThresholdDelta,
    thresholds: list,
    *,
    updated_by: str = "governance",
) -> list:
    """Replace threshold in registry after governed approval."""
    from src.continuity.css2.threshold import Threshold

    updated = delta.after.model_copy(
        update={
            "last_updated_at": delta.proposed_at,
            "last_updated_by": updated_by,
        }
    )
    out: list[Threshold] = []
    replaced = False
    for th in thresholds:
        if th.id == delta.threshold_id:
            out.append(updated)
            replaced = True
        else:
            out.append(th)
    if not replaced:
        out.append(updated)
    return out
