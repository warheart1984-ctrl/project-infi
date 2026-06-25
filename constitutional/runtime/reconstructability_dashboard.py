"""Reconstructability dashboard v0 — single survivability snapshot for gating and mirrors."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.runtime.constitutional_debt import (
    ConstitutionalDebtState,
    load_constitutional_debt,
)
from constitutional.runtime.fitness_risk import (
    ReconstructabilityRiskState,
    get_reconstructability_fitness_state,
    load_reconstructability_risk,
)
from constitutional.runtime.personal_constitutional_state import (
    PERSONAL_STATE_ID,
    PersonalConstitutionalState,
)
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
from constitutional.core.articles import (
    ARTICLE_H_REFERENCE,
    ARTICLE_P_REFERENCE,
    ARTICLE_S_INVARIANT,
    ARTICLE_S_REFERENCE,
    HIDDENNESS_INVARIANT,
    PURPOSE_CONTINUITY_INVARIANT,
)
from constitutional.hiddenness.hiddenness_failures import HiddennessFailureClass as HF
from constitutional.runtime.mission_fidelity_runtime import (
    MissionFidelityState,
    load_mission_fidelity_state,
)
from constitutional.runtime.purpose_failures import PurposeFailureClass as PF
from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessState
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    ContinuityBlockV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ObservationPayloadV2,
    ObservationReceiptV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    compute_lineage_hash,
    new_receipt_id,
    stable_json_hash,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

DASHBOARD_STATE_ID = "reconstructability_dashboard__global"
DASHBOARD_RUNTIME_NAME = "ReconstructabilityDashboardRuntime"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _dedupe_threats(threats: list[RF]) -> list[RF]:
    seen: set[RF] = set()
    ordered: list[RF] = []
    for threat in threats:
        if threat not in seen:
            seen.add(threat)
            ordered.append(threat)
    return ordered


def _model_snapshot(model: BaseModel | None) -> dict[str, Any]:
    if model is None:
        return {}
    return model.model_dump(mode="json")


def _dedupe_pf(threats: list[PF]) -> list[PF]:
    seen: set[PF] = set()
    ordered: list[PF] = []
    for threat in threats:
        if threat not in seen:
            seen.add(threat)
            ordered.append(threat)
    return ordered


def _dedupe_hf(threats: list[HF]) -> list[HF]:
    seen: set[HF] = set()
    ordered: list[HF] = []
    for threat in threats:
        if threat not in seen:
            seen.add(threat)
            ordered.append(threat)
    return ordered


class ReconstructabilityDashboardState(BaseModel):
    state_id: str = DASHBOARD_STATE_ID
    state_type: str = "reconstructability_dashboard"
    snapshot_at: datetime
    version: int = Field(ge=1)

    system_survivability_score: float = Field(ge=0.0, le=1.0)
    steward_independence_score: float = Field(ge=0.0, le=1.0)
    reconstructability_fitness_score: float = Field(ge=0.0, le=1.0)
    constitutional_debt_score: float = Field(ge=0.0, le=1.0)
    constitutional_risk_score: float = Field(ge=0.0, le=1.0)
    personal_capacity_continuity: float = Field(ge=0.0, le=1.0)

    active_threats: list[RF] = Field(default_factory=list)
    failed_surfaces: list[RF] = Field(default_factory=list)

    founder_dependency_index: float = Field(ge=0.0, le=1.0)
    implicit_assumptions_required: int = Field(default=0, ge=0)
    succession_readiness_score: float = Field(default=0.0, ge=0.0, le=1.0)

    governed_invariant: str = ARTICLE_S_INVARIANT
    article_reference: str = ARTICLE_S_REFERENCE

    purpose_fidelity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    invariant_interpretation_score: float = Field(default=0.0, ge=0.0, le=1.0)
    mission_legibility_score: float = Field(default=0.0, ge=0.0, le=1.0)
    purpose_continuity_index: float = Field(default=0.0, ge=0.0, le=1.0)
    purpose_threats: list[PF] = Field(default_factory=list)
    purpose_article_reference: str = ARTICLE_P_REFERENCE
    purpose_invariant: str = PURPOSE_CONTINUITY_INVARIANT

    hiddenness_index: float = Field(default=0.0, ge=0.0, le=1.0)
    hidden_threats: list[HF] = Field(default_factory=list)
    implicit_assumptions: list[str] = Field(default_factory=list)
    undocumented_invariants: list[str] = Field(default_factory=list)
    undocumented_purpose_fragments: list[str] = Field(default_factory=list)
    undocumented_authority: list[str] = Field(default_factory=list)
    undocumented_constraints: list[str] = Field(default_factory=list)
    founder_only_knowledge: list[str] = Field(default_factory=list)
    hidden_article_reference: str = ARTICLE_H_REFERENCE
    hidden_invariant: str = HIDDENNESS_INVARIANT

    fitness: dict[str, Any] = Field(default_factory=dict)
    debt: dict[str, Any] = Field(default_factory=dict)
    risk: dict[str, Any] = Field(default_factory=dict)
    personal: dict[str, Any] = Field(default_factory=dict)
    mission_fidelity: dict[str, Any] = Field(default_factory=dict)


def load_reconstructability_dashboard(
    csr: ConstitutionalStateRuntime,
) -> ReconstructabilityDashboardState:
    doc = csr.get_domain_doc(DASHBOARD_STATE_ID, ReconstructabilityDashboardState)
    assert isinstance(doc, ReconstructabilityDashboardState)
    return doc


def build_reconstructability_dashboard(
    csr: ConstitutionalStateRuntime,
    *,
    snapshot_at: datetime,
    version: int,
) -> ReconstructabilityDashboardState:
    """Aggregate fitness, debt, risk, and personal state into one survivability snapshot."""
    fitness: ReconstructabilityFitnessState | None = None
    try:
        fitness = get_reconstructability_fitness_state(csr)
    except KeyError:
        fitness = None

    debt = load_constitutional_debt(csr)
    risk = load_reconstructability_risk(csr)

    personal: PersonalConstitutionalState | None = None
    try:
        snap = csr.get_personal_snapshot()
        if isinstance(snap, PersonalConstitutionalState):
            personal = snap
    except KeyError:
        personal = None

    fitness_score = fitness.fitness_score if fitness else 0.0
    stewardship = fitness.stewardship_readiness_score if fitness else 0.0
    implicit = fitness.implicit_assumptions_required if fitness else 0
    failed_surfaces = list(fitness.failed_surfaces) if fitness else []

    debt_score = debt.debt_score
    reconstructability_risk = risk.reconstructability_risk if risk else 0.0
    capacity_continuity = personal.capacity_continuity if personal else 1.0
    unexternalized_ideas = personal.unexternalized_ideas if personal else 0
    burnout_warnings = personal.burnout_warnings if personal else 0

    system_survivability_score = _clamp01(
        0.4 * fitness_score
        + 0.3 * (1.0 - debt_score)
        + 0.2 * (1.0 - reconstructability_risk)
        + 0.1 * capacity_continuity
    )

    steward_independence_score = _clamp01(
        0.5 * stewardship
        + 0.3 * (1.0 - unexternalized_ideas / 10.0)
        + 0.2 * (1.0 - float(burnout_warnings))
    )
    founder_dependency_index = _clamp01(1.0 - steward_independence_score)

    active_threats = _dedupe_threats(list(debt.threats) + failed_surfaces)

    mission_fidelity: MissionFidelityState | None = None
    try:
        mission_fidelity = load_mission_fidelity_state(csr)
    except KeyError:
        mission_fidelity = None

    interactive_passed = False
    hidden_item_count = 0
    purpose_threats_extra: list[PF] = []
    hiddenness_index = 0.0
    hidden_threats: list[HF] = []
    implicit_assumptions_list: list[str] = []
    undocumented_invariants_list: list[str] = []
    undocumented_purpose_fragments_list: list[str] = []
    undocumented_authority_list: list[str] = []
    undocumented_constraints_list: list[str] = []
    founder_only_knowledge_list: list[str] = []
    try:
        from constitutional.runtime.mission_fidelity_interactive import load_mission_fidelity_interactive

        interactive = load_mission_fidelity_interactive(csr)
        if interactive is not None:
            interactive_passed = interactive.interactive_passed
    except ImportError:
        pass
    try:
        from constitutional.hiddenness.hiddenness_runtime import load_hiddenness_state

        hiddenness = load_hiddenness_state(csr)
        hidden_item_count = len(hiddenness.hidden_items)
        hiddenness_index = hiddenness.hiddenness_index
        hidden_threats = list(hiddenness.failed_surfaces)
        implicit_assumptions_list = list(hiddenness.implicit_assumptions)
        undocumented_invariants_list = list(hiddenness.undocumented_invariants)
        undocumented_purpose_fragments_list = list(hiddenness.undocumented_purpose_fragments)
        undocumented_authority_list = list(hiddenness.undocumented_authority)
        undocumented_constraints_list = list(hiddenness.undocumented_constraints)
        founder_only_knowledge_list = list(hiddenness.founder_only_knowledge)
        if hiddenness.pf_threats:
            purpose_threats_extra = hiddenness.pf_threats
    except KeyError:
        purpose_threats_extra = []

    purpose_fidelity_score = mission_fidelity.purpose_fidelity_score if mission_fidelity else 0.0
    invariant_interpretation_score = (
        mission_fidelity.invariant_interpretation_score if mission_fidelity else 0.0
    )
    mission_legibility_score = mission_fidelity.mission_legibility_score if mission_fidelity else 0.0
    purpose_continuity_index = mission_fidelity.purpose_continuity_index if mission_fidelity else 0.0
    purpose_threats = list(mission_fidelity.failed_surfaces) if mission_fidelity else []
    purpose_threats = _dedupe_pf(purpose_threats + purpose_threats_extra)

    from constitutional.runtime.survivability_enforcement import compute_succession_readiness_score

    succession_readiness_score = _clamp01(
        compute_succession_readiness_score(
            ReconstructabilityDashboardState(
                snapshot_at=snapshot_at,
                version=version,
                system_survivability_score=system_survivability_score,
                steward_independence_score=steward_independence_score,
                reconstructability_fitness_score=fitness_score,
                constitutional_debt_score=debt_score,
                constitutional_risk_score=reconstructability_risk,
                personal_capacity_continuity=capacity_continuity,
                active_threats=active_threats,
                failed_surfaces=failed_surfaces,
                founder_dependency_index=founder_dependency_index,
                implicit_assumptions_required=implicit,
            ),
            fitness,
        )
    )

    return ReconstructabilityDashboardState(
        snapshot_at=snapshot_at,
        version=version,
        system_survivability_score=system_survivability_score,
        steward_independence_score=steward_independence_score,
        reconstructability_fitness_score=fitness_score,
        constitutional_debt_score=debt_score,
        constitutional_risk_score=reconstructability_risk,
        personal_capacity_continuity=capacity_continuity,
        active_threats=active_threats,
        failed_surfaces=failed_surfaces,
        founder_dependency_index=founder_dependency_index,
        implicit_assumptions_required=implicit,
        succession_readiness_score=succession_readiness_score,
        purpose_fidelity_score=purpose_fidelity_score,
        invariant_interpretation_score=invariant_interpretation_score,
        mission_legibility_score=mission_legibility_score,
        purpose_continuity_index=purpose_continuity_index,
        purpose_threats=_dedupe_pf(purpose_threats),
        hiddenness_index=hiddenness_index,
        hidden_threats=_dedupe_hf(hidden_threats),
        implicit_assumptions=implicit_assumptions_list,
        undocumented_invariants=undocumented_invariants_list,
        undocumented_purpose_fragments=undocumented_purpose_fragments_list,
        undocumented_authority=undocumented_authority_list,
        undocumented_constraints=undocumented_constraints_list,
        founder_only_knowledge=founder_only_knowledge_list,
        fitness=_model_snapshot(fitness),
        debt=_model_snapshot(debt),
        risk=_model_snapshot(risk),
        personal=_model_snapshot(personal),
        mission_fidelity={
            **(_model_snapshot(mission_fidelity) if mission_fidelity else {}),
            "interactive_passed": interactive_passed,
            "hidden_item_count": hidden_item_count,
        },
    )


def build_dashboard_observation_receipt(
    state: ReconstructabilityDashboardState,
    *,
    previous_receipt_id: str | None = None,
    previous_lineage_hash: str | None = None,
) -> ObservationReceiptV2:
    payload = {
        "system_survivability_score": state.system_survivability_score,
        "steward_independence_score": state.steward_independence_score,
        "founder_dependency_index": state.founder_dependency_index,
        "reconstructability_fitness_score": state.reconstructability_fitness_score,
        "constitutional_debt_score": state.constitutional_debt_score,
        "constitutional_risk_score": state.constitutional_risk_score,
        "personal_capacity_continuity": state.personal_capacity_continuity,
        "active_threats": [t.value for t in state.active_threats],
        "failed_surfaces": [t.value for t in state.failed_surfaces],
        "implicit_assumptions_required": state.implicit_assumptions_required,
        "succession_readiness_score": state.succession_readiness_score,
        "purpose_fidelity_score": state.purpose_fidelity_score,
        "invariant_interpretation_score": state.invariant_interpretation_score,
        "mission_legibility_score": state.mission_legibility_score,
        "purpose_continuity_index": state.purpose_continuity_index,
        "purpose_threats": [t.value for t in state.purpose_threats],
        "hiddenness_index": state.hiddenness_index,
        "hidden_threats": [t.value for t in state.hidden_threats],
        "implicit_assumptions": state.implicit_assumptions,
        "undocumented_invariants": state.undocumented_invariants,
        "undocumented_purpose_fragments": state.undocumented_purpose_fragments,
        "undocumented_authority": state.undocumented_authority,
        "governed_invariant": state.governed_invariant,
        "article_reference": state.article_reference,
        "version": state.version,
    }
    payload_hash = stable_json_hash(payload)
    receipt_id = new_receipt_id("rdb")
    lineage_hash = compute_lineage_hash(
        previous_receipt_id=previous_receipt_id,
        receipt_id=receipt_id,
        payload_hash=payload_hash,
        previous_lineage_hash=previous_lineage_hash,
    )
    ts = state.snapshot_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return ObservationReceiptV2(
        receipt_id=receipt_id,
        runtime=DASHBOARD_RUNTIME_NAME,
        timestamp=ts,
        action_type="reconstructability_dashboard_snapshot",
        inputs=ReceiptInputsV2(
            request_id=state.state_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(observer_id=state.state_id),
        ),
        outputs=ReceiptOutputsV2(
            status="observed",
            result_hash=payload_hash,
            notes=(
                f"survivability={state.system_survivability_score:.2f} "
                f"steward_independence={state.steward_independence_score:.2f}"
            ),
        ),
        invariant=InvariantBlockV2(
            name=ARTICLE_S_INVARIANT,
            description=f"{ARTICLE_S_REFERENCE}: system must remain survivable across time, context, and stewardship",
            satisfied=state.system_survivability_score >= 0.6,
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
            source=DASHBOARD_RUNTIME_NAME,
            jurisdiction="governance",
            legitimacy_basis=ARTICLE_S_REFERENCE,
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["governance", "mission_preconditions", "amendment_triggers"],
            scope_out=["runtime_execution"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party="GovernanceStewards"),
        signatures=SignaturesBlockV2(runtime_signature="sig-rdb-runtime"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=previous_receipt_id,
            lineage_hash=lineage_hash,
        ),
        lifecycle=LifecycleBlockV2(
            stage="observation",
            previous_stage_receipt_id=previous_receipt_id,
            next_stage_expected="closure",
        ),
        observation=ObservationPayloadV2(
            observed_status="snapshot",
            observed_at=ts,
            observer_jurisdiction="governance",
            notes=f"Dashboard v{state.version}",
        ),
        threats=list(state.active_threats),
    )


class ReconstructabilityDashboardRuntime:
    """Aggregates fitness, debt, risk, and personal state into a survivability snapshot."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self._last_receipt_id: str | None = None
        self._last_lineage_hash: str | None = None

    def update_snapshot(self, snapshot_at: datetime | None = None) -> ReconstructabilityDashboardState:
        now = snapshot_at or datetime.now(UTC).replace(microsecond=0)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        try:
            prev = load_reconstructability_dashboard(self.csr)
            version = prev.version + 1
        except KeyError:
            version = 1

        state = build_reconstructability_dashboard(self.csr, snapshot_at=now, version=version)
        self.csr.register_or_replace_state(
            StateObject(
                state_id=DASHBOARD_STATE_ID,
                state_type="reconstructability_dashboard",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(DASHBOARD_STATE_ID, "reconstructability_dashboard", state)
        self._emit_dashboard_receipt(state)
        return state

    def get_snapshot(self) -> ReconstructabilityDashboardState:
        return load_reconstructability_dashboard(self.csr)

    def _emit_dashboard_receipt(self, state: ReconstructabilityDashboardState) -> None:
        receipt = build_dashboard_observation_receipt(
            state,
            previous_receipt_id=self._last_receipt_id,
            previous_lineage_hash=self._last_lineage_hash,
        )
        self.csr.append_observation_receipt(receipt)
        self._last_receipt_id = receipt.receipt_id
        self._last_lineage_hash = receipt.continuity.lineage_hash
