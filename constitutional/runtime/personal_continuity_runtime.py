# constitutional_substrate/personal_continuity_runtime.py
"""Personal continuity runtime — ideas, assumptions, critical contexts on CSR."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar, Literal

from constitutional.runtime.domain_receipt_emitter import build_domain_observation_receipt
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass
from constitutional.runtime.receipts_v2 import ObservationReceiptV2
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.core.models import StateObject
from pydantic import BaseModel, Field

RUNTIME_NAME = "PersonalContinuityRuntime"
GLOBAL_STATE_ID = "personal_continuity__global"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------- StateObjects ----------


class IdeaState(BaseModel):
    state_id: str
    state_type: str = "idea"
    title: str
    status: Literal["seed", "in_flight", "frozen", "retired"]
    foundational: bool = False
    lineage: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    linked_systems: list[str] = Field(default_factory=list)
    evidence_links: list[str] = Field(default_factory=list)
    last_updated_at: datetime


class AssumptionState(BaseModel):
    state_id: str
    state_type: str = "assumption"
    statement: str
    confidence: float
    status: Literal["implicit", "active", "challenged", "retired"]
    supporting_evidence: list[str] = Field(default_factory=list)
    last_updated_at: datetime


class CriticalContextState(BaseModel):
    state_id: str
    state_type: str = "critical_context"
    description: str
    dependencies: list[str] = Field(default_factory=list)
    reconstruction_difficulty: Literal["low", "medium", "high"]
    externalized: bool = False
    last_updated_at: datetime


# ---------- Runtime ----------


class PersonalContinuityRuntime:
    """Preserves architectural state: foundational ideas, assumptions, critical contexts."""

    resists: ClassVar[list[ReconstructabilityFailureClass]] = [
        ReconstructabilityFailureClass.STEWARD_DISCONTINUITY,
        ReconstructabilityFailureClass.EVIDENCE_LOSS,
        ReconstructabilityFailureClass.LINEAGE_BREAK,
    ]

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self._ensure_global_state()

    def _ensure_global_state(self) -> None:
        try:
            self.csr.get_state(GLOBAL_STATE_ID)
        except KeyError:
            self.csr.register_state(
                StateObject(
                    state_id=GLOBAL_STATE_ID,
                    state_type="personal_continuity",
                    current_state="Proposed",
                    invariants=["PC-1", "PC-2", "PC-3", "PC-4"],
                    evidence_requirements=["continuity_evidence"],
                    authority_model=["founder", "runtime_law_spine"],
                    reproducibility_requirements=["exact"],
                    impact_boundaries=["personal_continuity"],
                    accountability_chain=["founder"],
                )
            )

    def _register_idea_state_object(self, idea_id: str) -> None:
        state = StateObject(
            state_id=idea_id,
            state_type="idea",
            current_state="Proposed",
            invariants=["PC-1", "PC-2"],
            evidence_requirements=["idea_evidence_links"],
            authority_model=["founder"],
            reproducibility_requirements=["exact"],
            impact_boundaries=["personal_continuity"],
            accountability_chain=["founder"],
        )
        try:
            self.csr.get_state(idea_id)
            self.csr.register_or_replace_state(state)
        except KeyError:
            self.csr.register_state(state)

    # --- idea lifecycle ---

    def create_idea(self, title: str, foundational: bool = False) -> IdeaState:
        now = _utc_now()
        idea = IdeaState(
            state_id=f"idea__{int(now.timestamp() * 1000)}",
            title=title,
            status="seed",
            foundational=foundational,
            last_updated_at=now,
        )
        self._register_idea_state_object(idea.state_id)
        self.csr.put_domain_doc(idea.state_id, "idea", idea)
        self._emit_idea_receipt(idea, kind="Creation")
        return idea

    def update_idea_status(
        self,
        idea_id: str,
        status: Literal["seed", "in_flight", "frozen", "retired"],
    ) -> IdeaState:
        idea = self.csr.get_domain_doc(idea_id, IdeaState)
        idea = idea.model_copy(update={"status": status, "last_updated_at": _utc_now()})
        self.csr.put_domain_doc(idea_id, "idea", idea)
        kind = _status_to_receipt_kind(status)
        self._emit_idea_receipt(idea, kind=kind)
        return idea

    # --- risk: founder-only knowledge ---

    def assess_continuity_risk(self) -> ObservationReceiptV2:
        ideas = self.csr.states_of_type("idea")
        contexts = self.csr.states_of_type("critical_context")

        missing_foundational = [
            idea for idea in ideas if idea.foundational and not idea.evidence_links
        ]
        unexternalized_contexts = [
            ctx
            for ctx in contexts
            if not ctx.externalized and ctx.reconstruction_difficulty != "low"
        ]

        risk_score = min(
            1.0,
            0.5 * len(missing_foundational) + 0.5 * len(unexternalized_contexts),
        )

        payload = {
            "missing_foundational_ideas": [i.state_id for i in missing_foundational],
            "unexternalized_contexts": [c.state_id for c in unexternalized_contexts],
            "risk_score": risk_score,
        }

        prior = self.csr.domain_receipts_for(GLOBAL_STATE_ID)
        prev = prior[-1] if prior else None
        risk_threats = [
            ReconstructabilityFailureClass.EVIDENCE_LOSS,
            ReconstructabilityFailureClass.LINEAGE_BREAK,
            ReconstructabilityFailureClass.STEWARD_DISCONTINUITY,
        ]
        receipt = build_domain_observation_receipt(
            runtime=RUNTIME_NAME,
            state_object_id=GLOBAL_STATE_ID,
            action_type="continuity_risk_assessment",
            kind="Observation",
            invariant_name="FOUNDER_CONTEXT_MUST_NOT_BE_SINGLE_POINT_OF_FAILURE",
            invariant_description="PC risk: foundational ideas and critical contexts must be externalized",
            payload=payload,
            impact_scope_in=["governance_only", "personal_continuity"],
            thread_id=GLOBAL_STATE_ID,
            previous_receipt_id=prev.receipt_id if prev else None,
            previous_lineage_hash=prev.continuity.lineage_hash if prev else None,
            observed_status=f"risk_score={risk_score:.2f}",
            threats=risk_threats,
        )
        self.csr.append_observation_receipt(receipt)
        return receipt

    # --- internal ---

    def _emit_idea_receipt(self, idea: IdeaState, kind: str) -> None:
        prior = self.csr.domain_receipts_for(idea.state_id)
        prev = prior[-1] if prior else None
        payload = {
            "title": idea.title,
            "status": idea.status,
            "foundational": idea.foundational,
        }
        receipt = build_domain_observation_receipt(
            runtime=RUNTIME_NAME,
            state_object_id=idea.state_id,
            action_type=f"idea_{kind.lower()}",
            kind=kind,
            invariant_name="FOUNDATIONAL_IDEAS_MUST_BE_TRACKED_AND_EXTERNALIZED",
            invariant_description="PC-1: foundational ideas require evidence links when in flight",
            payload=payload,
            impact_scope_in=["governance_only", "personal_continuity"],
            evidence_ids=idea.evidence_links,
            thread_id=idea.state_id,
            previous_receipt_id=prev.receipt_id if prev else None,
            previous_lineage_hash=prev.continuity.lineage_hash if prev else None,
            observed_status=idea.status,
            threats=list(self.resists),
        )
        self.csr.append_observation_receipt(receipt)


def _status_to_receipt_kind(
    status: Literal["seed", "in_flight", "frozen", "retired"],
) -> str:
    if status == "frozen":
        return "Freeze"
    if status == "retired":
        return "Retire"
    return "Refinement"
