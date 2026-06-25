"""Hiddenness Runtime v1 — Article H constitutional flashlight."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_H_REFERENCE,
    HIDDENNESS_INVARIANT,
    HIDDENNESS_RECEIPT_INVARIANT,
)
from constitutional.core.models import StateObject
from constitutional.hiddenness.hiddenness_failures import (
    HF_SURFACE_COUNT,
    HiddennessFailureClass as HF,
    hf_surface_code,
)
from constitutional.runtime.mission_fidelity_interactive import (
    MISSION_FIDELITY_INTERACTIVE_STATE_ID,
    load_mission_fidelity_interactive,
)
from constitutional.runtime.mission_fidelity_runtime import (
    MISSION_STATEMENT_STATE_ID,
    load_mission_fidelity_state,
    load_mission_statement,
)
from constitutional.runtime.personal_continuity_runtime import (
    AssumptionState,
    CriticalContextState,
    IdeaState,
)
from constitutional.runtime.purpose_failures import PurposeFailureClass as PF
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    BaseReceiptV2,
    ContinuityBlockV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    HiddennessPayloadV2,
    HiddennessReceiptV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ObservationPayloadV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    compute_lineage_hash,
    stable_json_hash,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.runtime_charter import RUNTIME_CHARTER

HIDDENNESS_STATE_ID = "hiddenness__global"
HIDDENNESS_RUNTIME_NAME = "HiddennessRuntime"
MIN_RATIONALE_LENGTH = 10


class HiddennessCategory(str, Enum):
    IMPLICIT_ASSUMPTION = "implicit_assumption"
    MISSING_INVARIANT = "missing_invariant"
    MISSING_RATIONALE = "missing_rationale"
    MISSING_PURPOSE_RECEIPT = "missing_purpose_receipt"
    MISSING_AUTHORITY_LINK = "missing_authority_link"
    MISSING_OPERATIONAL_KNOWLEDGE = "missing_operational_knowledge"
    MISSING_CULTURAL_CONTEXT = "missing_cultural_context"
    MISSING_CONSTRAINT = "missing_constraint"
    MISSING_DEFINITION = "missing_definition"
    MISSING_BOUNDARY = "missing_boundary"
    MISSING_MEANING = "missing_meaning"


CATEGORY_TO_HF: dict[HiddennessCategory, HF] = {
    HiddennessCategory.IMPLICIT_ASSUMPTION: HF.HIDDEN_ASSUMPTION,
    HiddennessCategory.MISSING_INVARIANT: HF.HIDDEN_INVARIANT,
    HiddennessCategory.MISSING_RATIONALE: HF.HIDDEN_RATIONALE,
    HiddennessCategory.MISSING_PURPOSE_RECEIPT: HF.HIDDEN_PURPOSE_FRAGMENT,
    HiddennessCategory.MISSING_AUTHORITY_LINK: HF.HIDDEN_AUTHORITY,
    HiddennessCategory.MISSING_OPERATIONAL_KNOWLEDGE: HF.HIDDEN_STEWARD_KNOWLEDGE,
    HiddennessCategory.MISSING_CULTURAL_CONTEXT: HF.HIDDEN_CONTEXT,
    HiddennessCategory.MISSING_CONSTRAINT: HF.HIDDEN_CONSTRAINT,
    HiddennessCategory.MISSING_DEFINITION: HF.HIDDEN_DEPENDENCY,
    HiddennessCategory.MISSING_BOUNDARY: HF.HIDDEN_CONSTRAINT,
    HiddennessCategory.MISSING_MEANING: HF.HIDDEN_MEANING,
}

CATEGORY_TO_PF: dict[HiddennessCategory, PF] = {
    HiddennessCategory.IMPLICIT_ASSUMPTION: PF.PURPOSE_DRIFT,
    HiddennessCategory.MISSING_INVARIANT: PF.INVARIANT_DILUTION,
    HiddennessCategory.MISSING_RATIONALE: PF.INVARIANT_DILUTION,
    HiddennessCategory.MISSING_PURPOSE_RECEIPT: PF.MISSION_AMNESIA,
    HiddennessCategory.MISSING_AUTHORITY_LINK: PF.PURPOSE_FRAGMENTATION,
    HiddennessCategory.MISSING_OPERATIONAL_KNOWLEDGE: PF.CULTURAL_DISCONTINUITY,
    HiddennessCategory.MISSING_CULTURAL_CONTEXT: PF.CULTURAL_DISCONTINUITY,
    HiddennessCategory.MISSING_CONSTRAINT: PF.PURPOSE_AMBIGUITY,
    HiddennessCategory.MISSING_DEFINITION: PF.PURPOSE_AMBIGUITY,
    HiddennessCategory.MISSING_BOUNDARY: PF.PURPOSE_FRAGMENTATION,
    HiddennessCategory.MISSING_MEANING: PF.PURPOSE_AMBIGUITY,
}


class HiddennessItem(BaseModel):
    category: HiddennessCategory
    description: str
    source: str
    hf_threat: HF
    pf_threat: PF
    amendment_required: bool = True


class HiddennessState(BaseModel):
    state_id: str = HIDDENNESS_STATE_ID
    state_type: str = "hiddenness"
    snapshot_at: datetime
    version: int = Field(ge=1)

    hiddenness_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: List[HF] = Field(default_factory=list)
    missing_items: List[str] = Field(default_factory=list)
    implicit_assumptions: List[str] = Field(default_factory=list)
    undocumented_invariants: List[str] = Field(default_factory=list)
    undocumented_purpose_fragments: List[str] = Field(default_factory=list)
    undocumented_authority: List[str] = Field(default_factory=list)
    undocumented_context: List[str] = Field(default_factory=list)
    undocumented_constraints: List[str] = Field(default_factory=list)
    founder_only_knowledge: List[str] = Field(default_factory=list)

    hidden_items: List[HiddennessItem] = Field(default_factory=list)
    pf_threats: List[PF] = Field(default_factory=list)
    missing_purpose_artifacts: List[str] = Field(default_factory=list)

    @property
    def explicitness_score(self) -> float:
        """Backward-compatible alias for hiddenness_index."""
        return self.hiddenness_index


def load_hiddenness_state(csr: ConstitutionalStateRuntime) -> HiddennessState:
    doc = csr.get_domain_doc(HIDDENNESS_STATE_ID, HiddennessState)
    assert isinstance(doc, HiddennessState)
    return doc


def build_hiddenness_receipt(
    state: HiddennessState,
    *,
    previous_receipt_id: str | None = None,
    previous_lineage_hash: str | None = None,
) -> HiddennessReceiptV2:
    payload = HiddennessPayloadV2(
        kind="Hiddenness",
        invariant=HIDDENNESS_RECEIPT_INVARIANT,
        hiddenness_index=state.hiddenness_index,
        explicitness_score=state.hiddenness_index,
        version=state.version,
        failed_surfaces=[hf_surface_code(hf) for hf in state.failed_surfaces],
        missing_items=list(state.missing_items),
        implicit_assumptions=list(state.implicit_assumptions),
        undocumented_invariants=list(state.undocumented_invariants),
        undocumented_purpose_fragments=list(state.undocumented_purpose_fragments),
        undocumented_authority=list(state.undocumented_authority),
        undocumented_context=list(state.undocumented_context),
        undocumented_constraints=list(state.undocumented_constraints),
        founder_only_knowledge=list(state.founder_only_knowledge),
        hidden_items=[
            {
                "category": item.category.value,
                "description": item.description,
                "source": item.source,
                "hf_threat": hf_surface_code(item.hf_threat),
                "pf_threat": item.pf_threat.value,
                "amendment_required": item.amendment_required,
            }
            for item in state.hidden_items
        ],
        hf_threats=[hf_surface_code(hf) for hf in state.failed_surfaces],
        pf_threats=[pf.value for pf in state.pf_threats],
        missing_purpose_artifacts=list(state.missing_purpose_artifacts),
    )
    payload_hash = stable_json_hash(payload.model_dump())
    ts_slug = state.snapshot_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    receipt_id = f"hiddenness-{ts_slug}-v{state.version}"
    lineage_hash = compute_lineage_hash(
        previous_receipt_id=previous_receipt_id,
        receipt_id=receipt_id,
        payload_hash=payload_hash,
        previous_lineage_hash=previous_lineage_hash,
    )
    ts = state.snapshot_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return HiddennessReceiptV2(
        receipt_id=receipt_id,
        runtime=HIDDENNESS_RUNTIME_NAME,
        timestamp=ts,
        action_type="hiddenness_audit",
        inputs=ReceiptInputsV2(
            request_id=state.state_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(observer_id=state.state_id),
        ),
        outputs=ReceiptOutputsV2(
            status="audit",
            result_hash=payload_hash,
            notes=(
                f"hiddenness_index={state.hiddenness_index:.2f} "
                f"hf_failed={len(state.failed_surfaces)}"
            ),
        ),
        invariant=InvariantBlockV2(
            name=HIDDENNESS_RECEIPT_INVARIANT,
            description="Nothing required for continuity, legitimacy, or meaning may remain hidden",
            satisfied=state.hiddenness_index >= 0.7 and len(state.failed_surfaces) == 0,
        ),
        evidence=EvidenceBundleV2(
            bundle_id="constitutional_ledger",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        authority=AuthorityBlockV2(
            source=HIDDENNESS_RUNTIME_NAME,
            jurisdiction="hiddenness",
            legitimacy_basis=ARTICLE_H_REFERENCE,
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["governance", "mission_preconditions", "amendment_triggers"],
            scope_out=["execution", "state_mutation"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party="GovernanceStewards"),
        signatures=SignaturesBlockV2(runtime_signature="sig-hid-runtime"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=previous_receipt_id,
            lineage_hash=lineage_hash,
        ),
        lifecycle=LifecycleBlockV2(
            stage="observation",
            previous_stage_receipt_id=previous_receipt_id,
            next_stage_expected=None,
        ),
        observation=ObservationPayloadV2(
            observed_status="audit",
            observed_at=ts,
            observer_jurisdiction="hiddenness",
            notes=f"hf_threats={len(state.failed_surfaces)}",
        ),
        threats=list(state.failed_surfaces),
        hiddenness=payload,
    )


class HiddennessRuntime:
    """v1: continuously detect, expose, and remediate hidden knowledge (Article H)."""

    resists = list(HF)

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self._last_receipt_id: str | None = None
        self._last_lineage_hash: str | None = None

    def run_scan(self, snapshot_at: datetime | None = None) -> HiddennessState:
        return self.run_audit(snapshot_at=snapshot_at)

    def run_audit(self, snapshot_at: datetime | None = None, *, trigger_amendments: bool = True) -> HiddennessState:
        now = snapshot_at or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        hidden: List[HiddennessItem] = []
        missing_items: List[str] = []
        assumptions: List[str] = []
        invariants: List[str] = []
        purpose_fragments: List[str] = []
        authority: List[str] = []
        context: List[str] = []
        constraints: List[str] = []
        founder_only: List[str] = []

        hidden.extend(self._check_mission_artifacts(missing_items, invariants, purpose_fragments, context))
        hidden.extend(self._check_interactive_gaps(missing_items, purpose_fragments, founder_only))
        hidden.extend(
            self._check_personal_continuity(
                missing_items, assumptions, context, purpose_fragments, founder_only
            )
        )
        hidden.extend(
            self._check_receipt_gaps(missing_items, authority, purpose_fragments, constraints)
        )
        hidden.extend(self._check_runtime_charter_gaps(missing_items))

        failed_surfaces = self._collect_failed_surfaces(hidden)
        pf_threats = list(dict.fromkeys(item.pf_threat for item in hidden))
        hiddenness_index = max(0.0, 1.0 - len(failed_surfaces) / float(HF_SURFACE_COUNT))

        try:
            prev = load_hiddenness_state(self.csr)
            version = prev.version + 1
        except KeyError:
            version = 1

        state = HiddennessState(
            snapshot_at=now,
            version=version,
            hiddenness_index=hiddenness_index,
            failed_surfaces=failed_surfaces,
            missing_items=missing_items,
            implicit_assumptions=assumptions,
            undocumented_invariants=invariants,
            undocumented_purpose_fragments=purpose_fragments,
            undocumented_authority=authority,
            undocumented_context=context,
            undocumented_constraints=constraints,
            founder_only_knowledge=founder_only,
            hidden_items=hidden,
            pf_threats=pf_threats,
            missing_purpose_artifacts=missing_items,
        )

        self.csr.register_or_replace_state(
            StateObject(
                state_id=HIDDENNESS_STATE_ID,
                state_type="hiddenness",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(HIDDENNESS_STATE_ID, "hiddenness", state)
        self._emit_receipt(state)
        if trigger_amendments:
            self._maybe_trigger_amendments(state)
        return state

    def _collect_failed_surfaces(self, hidden: List[HiddennessItem]) -> List[HF]:
        seen: set[HF] = set()
        ordered: List[HF] = []
        for item in hidden:
            if item.hf_threat not in seen:
                seen.add(item.hf_threat)
                ordered.append(item.hf_threat)
        return ordered

    def _emit_receipt(self, state: HiddennessState) -> None:
        receipt = build_hiddenness_receipt(
            state,
            previous_receipt_id=self._last_receipt_id,
            previous_lineage_hash=self._last_lineage_hash,
        )
        self.csr.append_observation_receipt(receipt)
        self._last_receipt_id = receipt.receipt_id
        self._last_lineage_hash = receipt.continuity.lineage_hash

    def _maybe_trigger_amendments(self, state: HiddennessState) -> None:
        from constitutional.hiddenness.hiddenness_amendment import (
            maybe_trigger_hiddenness_amendment,
        )

        maybe_trigger_hiddenness_amendment(
            self.csr,
            state,
            opened_at=state.snapshot_at,
        )

        if not state.hidden_items:
            return
        from constitutional.purpose.purpose_continuity_amendment import (
            maybe_trigger_purpose_continuity_amendment,
        )

        try:
            mf_state = load_mission_fidelity_state(self.csr)
        except KeyError:
            return
        merged = mf_state.model_copy(
            update={
                "failed_surfaces": list(
                    dict.fromkeys(mf_state.failed_surfaces + state.pf_threats)
                ),
                "missing_purpose_artifacts": list(
                    dict.fromkeys(mf_state.missing_purpose_artifacts + state.missing_items)
                ),
            }
        )
        maybe_trigger_purpose_continuity_amendment(
            self.csr,
            merged,
            opened_at=state.snapshot_at,
        )

    def _add(
        self,
        hidden: List[HiddennessItem],
        category: HiddennessCategory,
        description: str,
        source: str,
        missing: List[str],
        *,
        assumptions: List[str] | None = None,
        invariants: List[str] | None = None,
        purpose_fragments: List[str] | None = None,
        authority: List[str] | None = None,
        context: List[str] | None = None,
        constraints: List[str] | None = None,
        founder_only: List[str] | None = None,
    ) -> None:
        artifact = f"{category.value}:{source}"
        missing.append(artifact)
        if assumptions is not None:
            assumptions.append(description)
        if invariants is not None:
            invariants.append(description)
        if purpose_fragments is not None:
            purpose_fragments.append(description)
        if authority is not None:
            authority.append(description)
        if context is not None:
            context.append(description)
        if constraints is not None:
            constraints.append(description)
        if founder_only is not None:
            founder_only.append(description)
        hidden.append(
            HiddennessItem(
                category=category,
                description=description,
                source=source,
                hf_threat=CATEGORY_TO_HF[category],
                pf_threat=CATEGORY_TO_PF[category],
            )
        )

    def _check_mission_artifacts(
        self,
        missing: List[str],
        invariants: List[str],
        purpose_fragments: List[str],
        context: List[str],
    ) -> List[HiddennessItem]:
        hidden: List[HiddennessItem] = []
        mission = load_mission_statement(self.csr)
        if mission is None:
            self._add(
                hidden,
                HiddennessCategory.MISSING_PURPOSE_RECEIPT,
                "No mission statement externalized",
                MISSION_STATEMENT_STATE_ID,
                missing,
                purpose_fragments=purpose_fragments,
            )
            return hidden

        if len(mission.invariant_rationale.strip()) < MIN_RATIONALE_LENGTH:
            self._add(
                hidden,
                HiddennessCategory.MISSING_RATIONALE,
                "Mission lacks invariant rationale",
                MISSION_STATEMENT_STATE_ID,
                missing,
            )

        if len(mission.founding_context.strip()) < MIN_RATIONALE_LENGTH:
            self._add(
                hidden,
                HiddennessCategory.MISSING_CULTURAL_CONTEXT,
                "Mission lacks founding cultural context",
                MISSION_STATEMENT_STATE_ID,
                missing,
                context=context,
            )

        from constitutional.core.articles import PURPOSE_CONTINUITY_INVARIANT

        registry = self.csr.invariant_registry
        if PURPOSE_CONTINUITY_INVARIANT not in registry:
            self._add(
                hidden,
                HiddennessCategory.MISSING_INVARIANT,
                "Purpose continuity invariant not registered",
                "invariant_registry",
                missing,
                invariants=invariants,
            )

        return hidden

    def _check_interactive_gaps(
        self,
        missing: List[str],
        purpose_fragments: List[str],
        founder_only: List[str],
    ) -> List[HiddennessItem]:
        hidden: List[HiddennessItem] = []
        interactive = load_mission_fidelity_interactive(self.csr)
        if interactive is None:
            self._add(
                hidden,
                HiddennessCategory.MISSING_PURPOSE_RECEIPT,
                "Mission Fidelity interactive test never submitted",
                MISSION_FIDELITY_INTERACTIVE_STATE_ID,
                missing,
                purpose_fragments=purpose_fragments,
            )
            return hidden

        unanswered = interactive.unanswered_question_ids()
        if unanswered:
            self._add(
                hidden,
                HiddennessCategory.MISSING_MEANING,
                f"Incomplete purpose interpretation ({len(unanswered)} unanswered)",
                MISSION_FIDELITY_INTERACTIVE_STATE_ID,
                missing,
                purpose_fragments=purpose_fragments,
            )
            for question_id in unanswered:
                self._add(
                    hidden,
                    HiddennessCategory.MISSING_OPERATIONAL_KNOWLEDGE,
                    f"Steward has not answered: {question_id}",
                    question_id,
                    missing,
                    purpose_fragments=purpose_fragments,
                    founder_only=founder_only,
                )

        return hidden

    def _check_personal_continuity(
        self,
        missing: List[str],
        assumptions: List[str],
        context: List[str],
        purpose_fragments: List[str],
        founder_only: List[str],
    ) -> List[HiddennessItem]:
        hidden: List[HiddennessItem] = []

        for assumption in self.csr.states_of_type("assumption"):
            if not isinstance(assumption, AssumptionState):
                continue
            if assumption.status == "implicit":
                self._add(
                    hidden,
                    HiddennessCategory.IMPLICIT_ASSUMPTION,
                    f"Implicit assumption: {assumption.statement[:80]}",
                    assumption.state_id,
                    missing,
                    assumptions=assumptions,
                )

        for ctx in self.csr.states_of_type("critical_context"):
            if not isinstance(ctx, CriticalContextState):
                continue
            if not ctx.externalized and ctx.reconstruction_difficulty != "low":
                self._add(
                    hidden,
                    HiddennessCategory.MISSING_CULTURAL_CONTEXT,
                    f"Critical context not externalized: {ctx.description[:80]}",
                    ctx.state_id,
                    missing,
                    context=context,
                )

        for idea in self.csr.states_of_type("idea"):
            if not isinstance(idea, IdeaState):
                continue
            if idea.foundational and not idea.evidence_links:
                self._add(
                    hidden,
                    HiddennessCategory.MISSING_OPERATIONAL_KNOWLEDGE,
                    f"Foundational idea lacks evidence links: {idea.title}",
                    idea.state_id,
                    missing,
                    purpose_fragments=purpose_fragments,
                    founder_only=founder_only,
                )

        return hidden

    def _check_receipt_gaps(
        self,
        missing: List[str],
        authority: List[str],
        purpose_fragments: List[str],
        constraints: List[str],
    ) -> List[HiddennessItem]:
        hidden: List[HiddennessItem] = []
        has_purpose_receipt = False
        for receipt in self._all_receipts():
            action = getattr(receipt, "action_type", "")
            if action in {"purpose_continuity", "mission_fidelity_test"}:
                has_purpose_receipt = True
            auth = receipt.authority
            if not auth.source or not auth.legitimacy_basis:
                self._add(
                    hidden,
                    HiddennessCategory.MISSING_AUTHORITY_LINK,
                    f"Receipt {receipt.receipt_id} lacks authority linkage",
                    receipt.receipt_id,
                    missing,
                    authority=authority,
                )
            boundary = receipt.impact_boundary
            if not boundary.scope_in and not boundary.scope_out:
                self._add(
                    hidden,
                    HiddennessCategory.MISSING_BOUNDARY,
                    f"Receipt {receipt.receipt_id} lacks impact boundaries",
                    receipt.receipt_id,
                    missing,
                    constraints=constraints,
                )

        if not has_purpose_receipt:
            self._add(
                hidden,
                HiddennessCategory.MISSING_PURPOSE_RECEIPT,
                "No purpose continuity or mission fidelity receipt on ledger",
                "receipt_ledger",
                missing,
                purpose_fragments=purpose_fragments,
            )

        return hidden

    def _check_runtime_charter_gaps(self, missing: List[str]) -> List[HiddennessItem]:
        hidden: List[HiddennessItem] = []
        receipt_runtimes = {
            receipt.runtime for receipt in self._all_receipts() if receipt.runtime
        }
        charter_runtimes = set(RUNTIME_CHARTER) | {HIDDENNESS_RUNTIME_NAME, "MissionFidelityRuntime"}
        undocumented = receipt_runtimes - charter_runtimes
        for name in sorted(undocumented):
            self._add(
                hidden,
                HiddennessCategory.MISSING_DEFINITION,
                f"Runtime {name} emits receipts but is not in charter",
                name,
                missing,
            )
        return hidden

    def _all_receipts(self) -> list[BaseReceiptV2]:
        return self.csr.get_all_receipts()
