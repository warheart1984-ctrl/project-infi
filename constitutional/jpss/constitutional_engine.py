"""JPSS-C Constitutional Engine — governs adaptive/invariant boundary."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from constitutional.jpss.constitutional_register import (
    BoundaryLayer,
    ConstitutionalDecisionEntry,
    ConstitutionalRegister,
    load_constitutional_register,
    save_constitutional_register,
)
from constitutional.legitimacy.jpss_c_spec import ConstitutionalAction, ConstitutionalClassification
from constitutional.runtime.runtime import ConstitutionalStateRuntime

CONSTITUTIONAL_ENGINE_STATE_ID = "jpss_c_engine__latest"


class ConstitutionalGovernanceRequest(BaseModel):
    action: ConstitutionalAction
    target_layer: BoundaryLayer
    item: str
    classification: ConstitutionalClassification
    rationale: str
    steward_id: str = "steward"
    reconstruction_evidence: list[str] = Field(default_factory=list)
    consequence_simulation: str | None = None
    prior_classification: BoundaryLayer | None = None
    new_classification: BoundaryLayer | None = None


class ConstitutionalGovernanceResult(BaseModel):
    recorded: bool
    blocked: bool = False
    block_reason: str = ""
    entry: ConstitutionalDecisionEntry | None = None
    captured_at: datetime | None = None


def _requires_reconstruction(action: ConstitutionalAction) -> bool:
    return action in ("invariant_elevation", "invariant_revision", "invariant_retirement")


def _requires_consequence_simulation(action: ConstitutionalAction, classification: ConstitutionalClassification) -> bool:
    return action in ("invariant_elevation", "invariant_revision", "invariant_retirement") or (
        classification == "requires_legitimacy_review"
    )


class JPSSConstitutionalEngine:
    """Constitutional judgment: governs what belongs in adaptive vs invariant layers."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def govern(self, request: ConstitutionalGovernanceRequest) -> ConstitutionalGovernanceResult:
        now = datetime.now(UTC).replace(microsecond=0)

        if request.action == "invariant_selection":
            from constitutional.jpss.invariant_selection_engine import (
                InvariantSelectionEngine,
                InvariantSelectionRequest,
            )

            selection = InvariantSelectionEngine(self.csr).evaluate(
                InvariantSelectionRequest(
                    candidate_value=request.item,
                    signal=request.rationale,
                    steward_id=request.steward_id,
                    steward_proposals=[request.rationale] if request.rationale else [],
                )
            )
            if selection.outcome == "reject":
                return ConstitutionalGovernanceResult(
                    recorded=False,
                    blocked=True,
                    block_reason=f"Selection rejected: {selection.rationale}",
                    captured_at=now,
                )
            if selection.outcome == "keep_adaptive":
                return ConstitutionalGovernanceResult(
                    recorded=True,
                    blocked=False,
                    captured_at=now,
                )

        if request.action == "invariant_retirement":
            from constitutional.jpss.invariant_retirement_protocol import (
                InvariantRetirementProtocol,
                InvariantRetirementRequest,
            )

            if not request.reconstruction_evidence or not request.consequence_simulation:
                pass  # fall through to standard gate checks below
            else:
                retirement = InvariantRetirementProtocol(self.csr).execute(
                    InvariantRetirementRequest(
                        invariant_item=request.item,
                        steward_id=request.steward_id,
                        purpose_no_longer_applies="purpose" in request.rationale.lower(),
                        historically_contingent=True,
                        steward_consensus=True,
                        drift_triggered=True,
                        context_reconstruction="; ".join(request.reconstruction_evidence),
                        purpose_reevaluation=request.rationale,
                        identity_impact=request.consequence_simulation,
                        failure_risk_model=request.consequence_simulation,
                        deliberation_notes=request.rationale,
                        retirement_vote_approved=True,
                    )
                )
                if not retirement.retirement_approved:
                    return ConstitutionalGovernanceResult(
                        recorded=False,
                        blocked=True,
                        block_reason=retirement.continuity_verdict,
                        captured_at=now,
                    )

        if _requires_reconstruction(request.action) and not request.reconstruction_evidence:
            return ConstitutionalGovernanceResult(
                recorded=False,
                blocked=True,
                block_reason="Invariant alteration requires reconstruction evidence.",
                captured_at=now,
            )

        if _requires_consequence_simulation(request.action, request.classification) and not request.consequence_simulation:
            return ConstitutionalGovernanceResult(
                recorded=False,
                blocked=True,
                block_reason="Consequence simulation required before invariant touch.",
                captured_at=now,
            )

        if request.action == "invariant_retirement" and request.classification == "invariant_domain":
            return ConstitutionalGovernanceResult(
                recorded=False,
                blocked=True,
                block_reason="Cannot retire an item still classified as invariant without boundary consultation.",
                captured_at=now,
            )

        entry = ConstitutionalDecisionEntry(
            timestamp=now,
            steward_id=request.steward_id,
            action=request.action,
            target_layer=request.target_layer,
            item=request.item,
            classification=request.classification,
            rationale=request.rationale,
            reconstruction_evidence=list(request.reconstruction_evidence),
            consequence_simulation=request.consequence_simulation,
            prior_classification=request.prior_classification,
            new_classification=request.new_classification,
        )
        register = load_constitutional_register(self.csr)
        register.append(entry)
        save_constitutional_register(self.csr, register)
        self.csr.put_domain_doc(CONSTITUTIONAL_ENGINE_STATE_ID, "jpss_c_engine_state", entry)
        return ConstitutionalGovernanceResult(recorded=True, entry=entry, captured_at=now)


def load_latest_constitutional_decision(csr: ConstitutionalStateRuntime) -> ConstitutionalDecisionEntry | None:
    try:
        doc = csr.get_domain_doc(CONSTITUTIONAL_ENGINE_STATE_ID, ConstitutionalDecisionEntry)
        assert isinstance(doc, ConstitutionalDecisionEntry)
        return doc
    except KeyError:
        register = load_constitutional_register(csr)
        if not register.entries:
            return None
        return register.entries[-1]
