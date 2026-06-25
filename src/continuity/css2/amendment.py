"""CRK-1 Amendment X — Recalibration Governance clause."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.css2.models import (
    InvariantRef,
    RecalibrationEvent,
    RecalibrationProposalContext,
    RecalibrationTrigger,
)
from src.continuity.css2.spec import (
    RECALIBRATION_AMENDMENT_CLAUSES,
    RECALIBRATION_AMENDMENT_ID,
    RECALIBRATION_AMENDMENT_TITLE,
)


class AmendmentComplianceResult(BaseModel):
    amendment_id: str = RECALIBRATION_AMENDMENT_ID
    title: str = RECALIBRATION_AMENDMENT_TITLE
    compliant: bool
    clause_results: dict[str, bool] = Field(default_factory=dict)
    violations: list[str] = Field(default_factory=list)


def check_recalibration_amendment(
    event: RecalibrationEvent,
    *,
    triggers: list[RecalibrationTrigger] | None = None,
) -> AmendmentComplianceResult:
    """Verify a recalibration event against Amendment X clauses."""
    trigger_list = triggers or event.triggers
    results: dict[str, bool] = {}
    violations: list[str] = []

    results["governed_act"] = event.decision != "approved" or event.adversarial_review_passed or bool(event.audit_trail)
    if not results["governed_act"]:
        violations.append("Approved recalibration without governed audit trail.")

    results["trigger_requirement"] = bool(trigger_list) and any(trigger.is_legitimate for trigger in trigger_list)
    if not results["trigger_requirement"]:
        violations.append("No legitimate recalibration trigger documented.")

    non_derogable = [inv for inv in event.invariants_checked if inv.non_derogable]
    touched = _touches_non_derogable(event, non_derogable)
    results["invariance_constraint"] = not touched or event.decision == "rejected"
    if touched and event.decision == "approved":
        violations.append("Approved recalibration touches non-derogable invariant.")

    results["adversarial_review"] = event.adversarial_review_passed or event.decision in {"rejected", "deferred"}
    if event.decision == "approved" and not event.adversarial_review_passed:
        violations.append("Approval without adversarial review (Red/Black/Blue).")

    results["legitimacy_test"] = bool(event.legitimacy_basis) and bool(event.invariants_checked)
    if not results["legitimacy_test"]:
        violations.append("Missing legitimacy basis or invariant checks.")

    results["auditability"] = bool(event.event_id) and bool(event.timestamp) and bool(event.decided_by)
    if not results["auditability"]:
        violations.append("Event not fully auditable (id/timestamp/actor missing).")

    results["meta_recalibration"] = "meta" not in event.legitimacy_basis.lower() or event.decision != "approved"
    if not results["meta_recalibration"]:
        violations.append("Meta-recalibration criteria changed without constitutional review.")

    compliant = not violations
    return AmendmentComplianceResult(
        compliant=compliant,
        clause_results=results,
        violations=violations,
    )


def check_proposal_amendment(ctx: RecalibrationProposalContext) -> AmendmentComplianceResult:
    """Pre-flight check before governance evaluation."""
    dummy = RecalibrationEvent(
        event_id="preflight",
        timestamp=__import__("datetime").datetime.now(__import__("datetime").UTC).replace(microsecond=0),
        scope=ctx.scope,
        trigger_type=ctx.trigger_type,
        failure_mode_before=ctx.candidate_failure_mode,
        proposed_changes=ctx.proposed_changes,
        invariants_checked=ctx.invariants,
        constraints_checked=[inv.id for inv in ctx.invariants],
        decision="deferred",
        legitimacy_basis="preflight",
        triggers=ctx.triggers,
    )
    return check_recalibration_amendment(dummy, triggers=ctx.triggers)


def _touches_non_derogable(
    event: RecalibrationEvent,
    non_derogable: list[InvariantRef],
) -> bool:
    for inv in non_derogable:
        for change in event.proposed_changes:
            if inv.id.lower() in change.rationale.lower():
                return True
            if inv.id.lower() in change.metric_id.lower():
                return True
    return False
