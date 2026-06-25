"""Invariant Retirement Protocol — safe de-sacralization of obsolete invariants."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.jpss.constitutional_ledgers import (
    RetirementReviewEntry,
    load_retirement_review_ledger,
    save_retirement_review_ledger,
)
from constitutional.jpss.invariant_register import InvariantEntry, InvariantRegister, load_invariant_register, save_invariant_register
from constitutional.legitimacy.jpss_c_spec import JPSS_C_RETIREMENT_CRITERIA, JPSS_C_RETIREMENT_STEPS
from constitutional.runtime.runtime import ConstitutionalStateRuntime


class InvariantRetirementRequest(BaseModel):
    invariant_item: str
    invariant_field: str = "core_values"
    steward_id: str = "steward"
    purpose_no_longer_applies: bool = False
    contradicts_higher_order: bool = False
    blocks_necessary_adaptation: bool = False
    causes_identity_distortion: bool = False
    historically_contingent: bool = False
    fails_future_steward_test: bool = False
    steward_consensus: bool = False
    drift_triggered: bool = False
    context_reconstruction: str = ""
    purpose_reevaluation: str = ""
    identity_impact: str = ""
    failure_risk_model: str = ""
    deliberation_notes: str = ""
    retirement_vote_approved: bool = False


class RetirementStepResult(BaseModel):
    step: str
    completed: bool
    detail: str = ""


class InvariantRetirementResult(BaseModel):
    invariant_item: str
    retirement_approved: bool = False
    steps: list[RetirementStepResult] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    criteria_met: list[str] = Field(default_factory=list)
    continuity_verdict: str = ""
    register_updated: bool = False
    captured_at: datetime | None = None


def _collect_triggers(request: InvariantRetirementRequest) -> list[str]:
    mapping = {
        "repeated_conflict_with_purpose": request.purpose_no_longer_applies,
        "repeated_conflict_with_identity": request.causes_identity_distortion,
        "repeated_conflict_with_adaptive_survival": request.blocks_necessary_adaptation,
        "historical_justification_no_longer_applies": request.historically_contingent,
        "steward_consensus": request.steward_consensus,
        "drift_detection": request.drift_triggered,
    }
    return [key for key, active in mapping.items() if active]


def _collect_criteria(request: InvariantRetirementRequest) -> list[str]:
    flags = {
        "purpose_no_longer_applies": request.purpose_no_longer_applies,
        "contradicts_higher_order_invariants": request.contradicts_higher_order,
        "blocks_necessary_adaptation": request.blocks_necessary_adaptation,
        "causes_identity_distortion": request.causes_identity_distortion,
        "historically_contingent_not_essential": request.historically_contingent,
        "fails_future_steward_test": request.fails_future_steward_test,
    }
    return [name for name in JPSS_C_RETIREMENT_CRITERIA if flags.get(name, False)]


def _remove_from_register(register: InvariantRegister, field: str, item: str) -> bool:
    latest = register.latest()
    if latest is None:
        return False

    target_list = getattr(latest, field, None)
    if not isinstance(target_list, list):
        return False

    normalized = item.lower()
    filtered = [value for value in target_list if value.lower() != normalized]
    if len(filtered) == len(target_list):
        return False

    setattr(latest, field, filtered)
    return True


class InvariantRetirementProtocol:
    """Eight-step protocol for safe invariant de-sacralization."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def execute(self, request: InvariantRetirementRequest) -> InvariantRetirementResult:
        now = datetime.now(UTC).replace(microsecond=0)
        triggers = _collect_triggers(request)
        criteria_met = _collect_criteria(request)

        steps: list[RetirementStepResult] = []

        steps.append(
            RetirementStepResult(
                step="context_reconstruction",
                completed=bool(request.context_reconstruction),
                detail=request.context_reconstruction or "Context reconstruction required.",
            )
        )
        steps.append(
            RetirementStepResult(
                step="purpose_reevaluation",
                completed=bool(request.purpose_reevaluation),
                detail=request.purpose_reevaluation or "Purpose re-evaluation required.",
            )
        )
        steps.append(
            RetirementStepResult(
                step="identity_impact_analysis",
                completed=bool(request.identity_impact),
                detail=request.identity_impact or "Identity impact analysis required.",
            )
        )
        steps.append(
            RetirementStepResult(
                step="failure_risk_modeling",
                completed=bool(request.failure_risk_model),
                detail=request.failure_risk_model or "Failure risk modeling required.",
            )
        )
        steps.append(
            RetirementStepResult(
                step="steward_deliberation",
                completed=bool(request.deliberation_notes or request.steward_consensus),
                detail=request.deliberation_notes or "Steward deliberation required.",
            )
        )
        steps.append(
            RetirementStepResult(
                step="retirement_vote",
                completed=request.retirement_vote_approved and request.steward_consensus,
                detail="Retirement vote approved." if request.retirement_vote_approved else "Retirement vote pending.",
            )
        )

        all_prior_complete = all(step.completed for step in steps)
        criteria_sufficient = len(criteria_met) >= 2 or (len(criteria_met) >= 1 and request.drift_triggered)
        retirement_approved = (
            all_prior_complete
            and criteria_sufficient
            and request.retirement_vote_approved
            and not request.contradicts_higher_order
        )

        register_updated = False
        if retirement_approved:
            register = load_invariant_register(self.csr)
            register_updated = _remove_from_register(register, request.invariant_field, request.invariant_item)
            if register_updated:
                save_invariant_register(self.csr, register)

        steps.append(
            RetirementStepResult(
                step="register_update",
                completed=register_updated if retirement_approved else not retirement_approved,
                detail="Invariant register updated." if register_updated else "No register change.",
            )
        )

        continuity_verdict = (
            "Continuity preserved; invariant safely retired."
            if retirement_approved and register_updated
            else "Retirement blocked — identity collapse risk or incomplete protocol."
        )
        steps.append(
            RetirementStepResult(
                step="continuity_review",
                completed=retirement_approved,
                detail=continuity_verdict,
            )
        )

        ledger = load_retirement_review_ledger(self.csr)
        ledger.append(
            RetirementReviewEntry(
                timestamp=now,
                steward_id=request.steward_id,
                invariant_item=request.invariant_item,
                triggers=triggers,
                steps_completed=[s.step for s in steps if s.completed],
                retirement_approved=retirement_approved,
                continuity_verdict=continuity_verdict,
                rationale=request.deliberation_notes,
            )
        )
        save_retirement_review_ledger(self.csr, ledger)

        return InvariantRetirementResult(
            invariant_item=request.invariant_item,
            retirement_approved=retirement_approved,
            steps=steps,
            triggers=triggers,
            criteria_met=criteria_met,
            continuity_verdict=continuity_verdict,
            register_updated=register_updated,
            captured_at=now,
        )
