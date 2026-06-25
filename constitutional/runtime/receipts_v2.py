"""Receipt v2 — Six-Dimension Runtime Contract + Article XIV Remediation Lifecycle."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal, TypeAlias
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from constitutional.hiddenness.hiddenness_failures import HiddennessFailureClass
from constitutional.runtime.purpose_failures import PurposeFailureClass
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass

ThreatClass: TypeAlias = (
    ReconstructabilityFailureClass | PurposeFailureClass | HiddennessFailureClass
)

LifecycleStage: TypeAlias = Literal[
    "decision", "observation", "divergence", "remediation", "closure"
]
ReproducibilityMode: TypeAlias = Literal[
    "exact", "structural", "approximate", "non_reproducible"
]
ClaimType: TypeAlias = Literal[
    "factual", "procedural", "authority", "continuity", "reality"
]


# --- Shared blocks -------------------------------------------------------------


class EvidenceSourceV2(BaseModel):
    id: str
    type: str
    provenance: str


class ChainOfCustodyEntryV2(BaseModel):
    holder: str
    timestamp: str
    action: str


class EvidenceSufficiencyV2(BaseModel):
    continuity: bool
    truth: bool
    sovereignty: bool
    institutional: bool


class EvidenceBundleV2(BaseModel):
    bundle_id: str
    sources: list[EvidenceSourceV2] = Field(default_factory=list)
    modalities: list[str] = Field(default_factory=list)
    chain_of_custody: list[ChainOfCustodyEntryV2] = Field(default_factory=list)
    sufficiency: EvidenceSufficiencyV2


class DelegationLinkV2(BaseModel):
    from_: str = Field(alias="from")
    to: str
    scope: str
    timestamp: str

    model_config = {"populate_by_name": True}


class ConsentBlockV2(BaseModel):
    granted_by: str | None = None
    timestamp: str | None = None
    terms: str | None = None


class AuthorityBlockV2(BaseModel):
    source: str
    jurisdiction: str
    delegation_chain: list[DelegationLinkV2] = Field(default_factory=list)
    consent: ConsentBlockV2 | None = None
    legitimacy_basis: str


class ReproducibilityBlockV2(BaseModel):
    is_reproducible: bool
    mode: ReproducibilityMode
    constraints: str | None = None
    reproduction_reference_id: str | None = None


class ImpactBoundaryV2(BaseModel):
    scope_in: list[str]
    scope_out: list[str]
    notes: str | None = None


class AccountabilityChainEntryV2(BaseModel):
    role: str
    party_id: str
    responsibility_scope: str
    escalation_path: str | None = None


class AccountabilityBlockV2(BaseModel):
    primary_accountable_party: str
    accountability_chain: list[AccountabilityChainEntryV2] = Field(default_factory=list)


class ReceiptContextV2(BaseModel):
    mission_id: str | None = None
    task_id: str | None = None
    observer_id: str | None = None


class ReceiptInputsV2(BaseModel):
    request_id: str
    payload_hash: str
    context: ReceiptContextV2 = Field(default_factory=ReceiptContextV2)


class ReceiptOutputsV2(BaseModel):
    status: str
    result_hash: str
    notes: str | None = None


class InvariantBlockV2(BaseModel):
    name: str
    description: str
    satisfied: bool


class SignaturesBlockV2(BaseModel):
    runtime_signature: str
    observer_signature: str | None = None


class ContinuityBlockV2(BaseModel):
    previous_receipt_id: str | None = None
    thread_id: str | None = None
    lineage_hash: str


class LifecycleBlockV2(BaseModel):
    """Article XIV — remediation lifecycle stage and transitions."""

    stage: LifecycleStage
    previous_stage_receipt_id: str | None = None
    next_stage_expected: str | None = None


# --- Base receipt --------------------------------------------------------------


class BaseReceiptV2(BaseModel):
    receipt_id: str
    runtime: str
    timestamp: str
    action_type: str

    inputs: ReceiptInputsV2
    outputs: ReceiptOutputsV2

    invariant: InvariantBlockV2
    evidence: EvidenceBundleV2
    authority: AuthorityBlockV2
    reproducibility: ReproducibilityBlockV2
    impact_boundary: ImpactBoundaryV2
    accountability: AccountabilityBlockV2

    signatures: SignaturesBlockV2
    continuity: ContinuityBlockV2
    lifecycle: LifecycleBlockV2
    threats: list[ThreatClass] = Field(default_factory=list)


# --- Runtime-specific receipts -------------------------------------------------


class TruthClaimV2(BaseModel):
    claim_id: str
    claim_type: ClaimType
    statement: str


class TruthVerificationV2(BaseModel):
    method: str
    confidence: float
    evidence_used: list[str] = Field(default_factory=list)
    contradictions: list[str] | None = None


class TruthReceiptV2(BaseReceiptV2):
    claim: TruthClaimV2
    verification: TruthVerificationV2


class SovereigntyDelegationV2(BaseModel):
    granted_by: str
    granted_to: str
    scope: str
    jurisdiction: str
    terms: str | None = None


class SovereigntyLegitimacyV2(BaseModel):
    basis: str
    validated: bool
    conflicts: list[str] | None = None


class SovereigntyReceiptV2(BaseReceiptV2):
    delegation: SovereigntyDelegationV2
    legitimacy: SovereigntyLegitimacyV2


class ReproductionDivergenceV2(BaseModel):
    diverged: bool
    divergence_points: list[str] | None = None
    structural_match: bool
    output_match: bool


class ReproductionPayloadV2(BaseModel):
    reference_receipt_id: str
    divergence: ReproductionDivergenceV2


class ReproductionReceiptV2(BaseReceiptV2):
    reproduction: ReproductionPayloadV2


class ContinuityEventV2(BaseModel):
    event_id: str
    event_type: str
    timestamp_observed: str


class ContinuityLineageV2(BaseModel):
    chain_of_custody: list[str] = Field(default_factory=list)
    continuity_satisfied: bool


class ContinuityReceiptV2(BaseReceiptV2):
    event: ContinuityEventV2
    lineage: ContinuityLineageV2


class InstitutionalProcedureV2(BaseModel):
    procedure_id: str
    version: str
    steps_followed: list[str] = Field(default_factory=list)
    deviations: list[str] | None = None


class InstitutionalComplianceV2(BaseModel):
    compliant: bool
    violations: list[str] | None = None


class InstitutionalReceiptV2(BaseReceiptV2):
    procedure: InstitutionalProcedureV2
    compliance: InstitutionalComplianceV2


class ArbitrationConflictV2(BaseModel):
    runtimes_in_conflict: list[str]
    conflict_type: str
    evidence_presented: list[str] = Field(default_factory=list)


class ArbitrationResolutionV2(BaseModel):
    winning_runtime: str
    rationale: str
    precedence_rule: str


class ArbitrationReceiptV2(BaseReceiptV2):
    conflict: ArbitrationConflictV2
    resolution: ArbitrationResolutionV2


# --- Article XIV lifecycle receipts --------------------------------------------


class ObservationPayloadV2(BaseModel):
    """What actually occurred in reality (Reality Runtime / observer)."""

    observed_status: str
    observed_at: str
    observer_jurisdiction: str
    notes: str | None = None


class ConstitutionalStateSnapshotPayloadV2(BaseModel):
    """Macro constitutional health derived from receipts + ledger (governed aggregate)."""

    health_score: float = Field(ge=0.0, le=1.0)
    debt_score: float = Field(ge=0.0, le=1.0, default=0.0)
    constitutional_debt: int = Field(ge=0)
    unresolved_divergences: int = Field(ge=0)
    open_remediations: int = Field(ge=0)
    pending_amendments: int = Field(ge=0)
    overdue_obligations: int = Field(ge=0)
    condition: Literal["Healthy", "Degraded", "Critical"]
    version: int = Field(ge=1)
    window: str = "cumulative"


class DivergencePayloadV2(BaseModel):
    """Nature and evidence of contradiction vs expected outcome."""

    nature: str
    magnitude: str
    evidence_receipt_ids: list[str] = Field(default_factory=list)
    expected_outcome_hash: str | None = None
    observed_outcome_hash: str | None = None


class RemediationPayloadV2(BaseModel):
    required_actions: list[str]
    responsible_party: str
    restitution: str | None = None
    escalation_path: str | None = None
    constitutional_trigger: bool = False
    deadline: str | None = None


class ClosurePayloadV2(BaseModel):
    remediation_completed: bool
    restitution_delivered: bool = False
    institutional_review_performed: bool = False
    reviewing_body: str
    constitutional_amendment_id: str | None = None


class DecisionReceiptV2(BaseReceiptV2):
    @model_validator(mode="after")
    def _stage_is_decision(self) -> DecisionReceiptV2:
        if self.lifecycle.stage != "decision":
            raise ValueError("DecisionReceiptV2 requires lifecycle.stage == 'decision'")
        return self


class ObservationReceiptV2(BaseReceiptV2):
    observation: ObservationPayloadV2

    @model_validator(mode="after")
    def _stage_is_observation(self) -> ObservationReceiptV2:
        if self.lifecycle.stage != "observation":
            raise ValueError("ObservationReceiptV2 requires lifecycle.stage == 'observation'")
        return self


class ConstitutionalStateReceiptV2(ObservationReceiptV2):
    """Observation receipt for global constitutional state snapshots."""

    constitutional_state: ConstitutionalStateSnapshotPayloadV2
    action_type: str = "constitutional_state_snapshot"
    runtime: str = "ConstitutionalStateRuntime"

    @model_validator(mode="after")
    def _action_type_constitutional(self) -> ConstitutionalStateReceiptV2:
        if self.action_type != "constitutional_state_snapshot":
            object.__setattr__(self, "action_type", "constitutional_state_snapshot")
        return self


class RiskScopeV2(BaseModel):
    runtime: str
    invariant: str
    tenant: str | None = None


class RiskFactorV2(BaseModel):
    factor: str
    weight: float = Field(ge=0.0, le=1.0)
    value: float = Field(ge=0.0)


class PredictedFailureV2(BaseModel):
    type: Literal[
        "remediation_failure",
        "amendment_required",
        "governance_breakdown",
    ]
    invariant: str
    probability: float = Field(ge=0.0, le=1.0)
    horizon: str = "7d"


class RecommendedActionV2(BaseModel):
    type: Literal[
        "initiate_amendment_analysis",
        "escalate_remediation",
        "increase_observer_scrutiny",
        "acknowledge_or_dismiss",
    ]
    target: str
    urgency: Literal["low", "medium", "high", "critical"]


class ConstitutionalRiskPayloadV2(BaseModel):
    """Forecast payload — governed hint, not binding law."""

    risk_score: float = Field(ge=0.0, le=1.0)
    scope: RiskScopeV2
    risk_factors: list[RiskFactorV2] = Field(default_factory=list)
    predicted_failures: list[PredictedFailureV2] = Field(default_factory=list)
    recommended_actions: list[RecommendedActionV2] = Field(default_factory=list)
    horizon: str = "7d"
    lookback_days: int = Field(default=30, ge=1)


class RiskReceiptV2(ObservationReceiptV2):
    """Observation receipt for constitutional risk forecasts."""

    constitutional_risk: ConstitutionalRiskPayloadV2
    action_type: str = "constitutional_risk_forecast"
    runtime: str = "ConstitutionalRiskRuntime"

    @model_validator(mode="after")
    def _action_type_risk(self) -> RiskReceiptV2:
        if self.action_type != "constitutional_risk_forecast":
            object.__setattr__(self, "action_type", "constitutional_risk_forecast")
        return self


class ReconstructabilityFitnessPayloadV2(BaseModel):
    """Audit payload — periodic reconstructability fitness snapshot."""

    fitness_score: float = Field(ge=0.0, le=1.0)
    stewardship_readiness_score: float = Field(ge=0.0, le=1.0)
    version: int = Field(ge=1)
    tested_surfaces: list[str] = Field(default_factory=list)
    failed_surfaces: list[str] = Field(default_factory=list)
    implicit_assumptions_required: int = Field(default=0, ge=0)
    missing_artifacts: list[str] = Field(default_factory=list)
    missing_receipts: list[str] = Field(default_factory=list)
    missing_lineage_links: list[str] = Field(default_factory=list)


class ReconstructabilityFitnessReceiptV2(ObservationReceiptV2):
    """Observation receipt for reconstructability fitness audits."""

    reconstructability_fitness: ReconstructabilityFitnessPayloadV2
    action_type: str = "reconstructability_fitness_audit"
    runtime: str = "ReconstructabilityFitnessRuntime"

    @model_validator(mode="after")
    def _action_type_fitness(self) -> ReconstructabilityFitnessReceiptV2:
        if self.action_type != "reconstructability_fitness_audit":
            object.__setattr__(self, "action_type", "reconstructability_fitness_audit")
        return self


class MissionFidelityPayloadV2(BaseModel):
    """Audit payload — periodic mission fidelity / purpose continuity snapshot."""

    purpose_fidelity_score: float = Field(ge=0.0, le=1.0)
    invariant_interpretation_score: float = Field(ge=0.0, le=1.0)
    mission_legibility_score: float = Field(ge=0.0, le=1.0)
    purpose_continuity_index: float = Field(ge=0.0, le=1.0)
    version: int = Field(ge=1)
    tested_surfaces: list[str] = Field(default_factory=list)
    failed_surfaces: list[str] = Field(default_factory=list)
    missing_purpose_artifacts: list[str] = Field(default_factory=list)
    ambiguous_interpretations: list[str] = Field(default_factory=list)
    conflicting_justifications: list[str] = Field(default_factory=list)


class MissionFidelityReceiptV2(ObservationReceiptV2):
    """Observation receipt for mission fidelity tests (Article P)."""

    mission_fidelity: MissionFidelityPayloadV2
    action_type: str = "mission_fidelity_test"
    runtime: str = "MissionFidelityRuntime"

    @model_validator(mode="after")
    def _action_type_mission_fidelity(self) -> MissionFidelityReceiptV2:
        if self.action_type != "mission_fidelity_test":
            object.__setattr__(self, "action_type", "mission_fidelity_test")
        return self


class PurposeContinuityPayloadV2(BaseModel):
    """Purpose continuity receipt — documents meaning so it cannot be lost."""

    kind: str = "PurposeContinuity"
    invariant: str
    purpose_interpretation: str = ""
    purpose_justification: str = ""
    purpose_constraints: list[str] = Field(default_factory=list)
    non_negotiables: list[str] = Field(default_factory=list)
    drift_vectors_detected: list[str] = Field(default_factory=list)
    missing_purpose_artifacts: list[str] = Field(default_factory=list)
    tested_surfaces: list[str] = Field(default_factory=list)
    failed_surfaces: list[str] = Field(default_factory=list)
    timestamp: str


class PurposeContinuityReceiptV2(ObservationReceiptV2):
    """Receipt recording steward purpose articulation (Mission Fidelity Test v1)."""

    purpose_continuity: PurposeContinuityPayloadV2
    action_type: str = "purpose_continuity"
    runtime: str = "MissionFidelityInteractiveRuntime"

    @model_validator(mode="after")
    def _action_type_purpose_continuity(self) -> PurposeContinuityReceiptV2:
        if self.action_type != "purpose_continuity":
            object.__setattr__(self, "action_type", "purpose_continuity")
        return self


class HiddennessLineageLinksV2(BaseModel):
    related_states: list[str] = Field(default_factory=list)
    related_receipts: list[str] = Field(default_factory=list)
    amendment_candidates: list[str] = Field(default_factory=list)


class HiddennessPayloadV2(BaseModel):
    """Hiddenness audit payload — Article H surfaces knowledge not yet explicit."""

    kind: str = "Hiddenness"
    invariant: str = ""
    hiddenness_index: float = Field(ge=0.0, le=1.0)
    explicitness_score: float = Field(ge=0.0, le=1.0)
    version: int = Field(ge=1)
    failed_surfaces: list[str] = Field(default_factory=list)
    missing_items: list[str] = Field(default_factory=list)
    implicit_assumptions: list[str] = Field(default_factory=list)
    undocumented_invariants: list[str] = Field(default_factory=list)
    undocumented_purpose_fragments: list[str] = Field(default_factory=list)
    undocumented_authority: list[str] = Field(default_factory=list)
    undocumented_context: list[str] = Field(default_factory=list)
    undocumented_constraints: list[str] = Field(default_factory=list)
    founder_only_knowledge: list[str] = Field(default_factory=list)
    invariant_drift_candidates: list[str] = Field(default_factory=list)
    semantic_mismatches: list[str] = Field(default_factory=list)
    lineage_gaps: list[str] = Field(default_factory=list)
    lineage_links: HiddennessLineageLinksV2 | None = None
    hidden_items: list[dict[str, object]] = Field(default_factory=list)
    hf_threats: list[str] = Field(default_factory=list)
    pf_threats: list[str] = Field(default_factory=list)
    missing_purpose_artifacts: list[str] = Field(default_factory=list)


class HiddennessReceiptV2(ObservationReceiptV2):
    """Receipt for hiddenness runtime audits — the constitutional flashlight."""

    hiddenness: HiddennessPayloadV2
    action_type: str = "hiddenness_audit"
    runtime: str = "HiddennessRuntime"

    @model_validator(mode="after")
    def _action_type_hiddenness(self) -> HiddennessReceiptV2:
        if self.action_type != "hiddenness_audit":
            object.__setattr__(self, "action_type", "hiddenness_audit")
        return self


class DivergenceReceiptV2(BaseReceiptV2):
    divergence: DivergencePayloadV2

    @model_validator(mode="after")
    def _stage_is_divergence(self) -> DivergenceReceiptV2:
        if self.lifecycle.stage != "divergence":
            raise ValueError("DivergenceReceiptV2 requires lifecycle.stage == 'divergence'")
        return self


class RemediationReceiptV2(BaseReceiptV2):
    remediation: RemediationPayloadV2

    @model_validator(mode="after")
    def _stage_is_remediation(self) -> RemediationReceiptV2:
        if self.lifecycle.stage != "remediation":
            raise ValueError("RemediationReceiptV2 requires lifecycle.stage == 'remediation'")
        return self


class ClosureReceiptV2(BaseReceiptV2):
    closure: ClosurePayloadV2

    @model_validator(mode="after")
    def _stage_is_closure(self) -> ClosureReceiptV2:
        if self.lifecycle.stage != "closure":
            raise ValueError("ClosureReceiptV2 requires lifecycle.stage == 'closure'")
        return self


# --- Article XV transition receipts ------------------------------------------


class TransitionPayloadV2(BaseModel):
    """Legal state change justified by Receipt v2 (Constitutional State Runtime)."""

    from_state: str
    to_state: str
    legal_basis: str
    receipt_ids_used: list[str] = Field(default_factory=list)
    state_id: str | None = None
    state_type: str | None = None


class TransitionReceiptV2(BaseReceiptV2):
    """Specialization of Receipt v2 emitted for every legal constitutional transition."""

    transition: TransitionPayloadV2
    action_type: str = "state_transition"

    @model_validator(mode="after")
    def _transition_action_type(self) -> TransitionReceiptV2:
        if self.action_type != "state_transition":
            object.__setattr__(self, "action_type", "state_transition")
        return self


# --- Article XVI amendment receipts --------------------------------------------

AmendmentChangeType: TypeAlias = Literal["addition", "modification", "removal"]
AmendmentStage: TypeAlias = Literal[
    "proposed", "evaluated", "ratified", "implemented", "observed", "closed"
]


class AmendmentPayloadV2(BaseModel):
    article: str
    change_type: AmendmentChangeType
    justification: str
    trigger_receipt_id: str
    amendment_stage: AmendmentStage
    immutable_override: bool = False
    unanimous_sovereign_ratification: bool = False


class AmendmentReceiptV2(BaseReceiptV2):
    """Base specialization for all constitutional amendment stage receipts."""

    amendment: AmendmentPayloadV2
    action_type: str = "constitutional_amendment"


class AmendmentProposalReceiptV2(AmendmentReceiptV2):
    @model_validator(mode="after")
    def _stage(self) -> AmendmentProposalReceiptV2:
        if self.amendment.amendment_stage != "proposed":
            raise ValueError("AmendmentProposalReceiptV2 requires amendment_stage == 'proposed'")
        return self


class AmendmentEvaluationReceiptV2(AmendmentReceiptV2):
    @model_validator(mode="after")
    def _stage(self) -> AmendmentEvaluationReceiptV2:
        if self.amendment.amendment_stage != "evaluated":
            raise ValueError("AmendmentEvaluationReceiptV2 requires amendment_stage == 'evaluated'")
        return self


class AmendmentRatificationReceiptV2(AmendmentReceiptV2):
    @model_validator(mode="after")
    def _stage(self) -> AmendmentRatificationReceiptV2:
        if self.amendment.amendment_stage != "ratified":
            raise ValueError("AmendmentRatificationReceiptV2 requires amendment_stage == 'ratified'")
        return self


class AmendmentImplementationReceiptV2(AmendmentReceiptV2):
    @model_validator(mode="after")
    def _stage(self) -> AmendmentImplementationReceiptV2:
        if self.amendment.amendment_stage != "implemented":
            raise ValueError("AmendmentImplementationReceiptV2 requires amendment_stage == 'implemented'")
        return self


class AmendmentObservationReceiptV2(AmendmentReceiptV2):
    @model_validator(mode="after")
    def _stage(self) -> AmendmentObservationReceiptV2:
        if self.amendment.amendment_stage != "observed":
            raise ValueError("AmendmentObservationReceiptV2 requires amendment_stage == 'observed'")
        return self


class AmendmentClosureReceiptV2(AmendmentReceiptV2):
    @model_validator(mode="after")
    def _stage(self) -> AmendmentClosureReceiptV2:
        if self.amendment.amendment_stage != "closed":
            raise ValueError("AmendmentClosureReceiptV2 requires amendment_stage == 'closed'")
        return self


# --- Observer verification receipts (Article XVI handbook) --------------------


class ObserverVerificationPayloadV2(BaseModel):
    state_reconstructed: bool
    state_replayed: bool
    divergence_detected: bool
    remediation_valid: bool
    amendments_valid: bool
    target_id: str | None = None
    notes: str | None = None


class ObserverAccountabilitySummaryV2(BaseModel):
    responsible_parties: list[str] = Field(default_factory=list)


class ObserverVerificationReceiptV2(BaseReceiptV2):
    runtime: str = "observer"
    action_type: str = "observer_verification"
    verification: ObserverVerificationPayloadV2
    observer_accountability: ObserverAccountabilitySummaryV2 = Field(
        default_factory=ObserverAccountabilitySummaryV2,
    )


class ObserverDivergencePayloadV2(BaseModel):
    divergence_points: list[str] = Field(default_factory=list)
    target_receipt_ids: list[str] = Field(default_factory=list)
    rationale: str


class ObserverDivergenceReceiptV2(BaseReceiptV2):
    runtime: str = "observer"
    action_type: str = "observer_divergence"
    observer_divergence: ObserverDivergencePayloadV2


class ObserverRemediationRequestPayloadV2(BaseModel):
    requested_actions: list[str] = Field(default_factory=list)
    responsible_party: str
    trigger_receipt_id: str


class ObserverRemediationRequestReceiptV2(BaseReceiptV2):
    runtime: str = "observer"
    action_type: str = "observer_remediation_request"
    observer_remediation_request: ObserverRemediationRequestPayloadV2


class ObserverClosurePayloadV2(BaseModel):
    verification_receipt_id: str
    closed: bool = True
    notes: str | None = None


class ObserverClosureReceiptV2(BaseReceiptV2):
    runtime: str = "observer"
    action_type: str = "observer_closure"
    observer_closure: ObserverClosurePayloadV2


# --- Validation helpers --------------------------------------------------------


_REQUIRED_SUFFICIENCY_KEYS = ("continuity", "truth", "sovereignty", "institutional")

LIFECYCLE_TRANSITIONS: dict[LifecycleStage, list[LifecycleStage]] = {
    "decision": ["observation"],
    "observation": ["divergence", "closure"],
    "divergence": ["remediation"],
    "remediation": ["closure"],
    "closure": [],
}

AMENDMENT_TRANSITIONS: dict[AmendmentStage, list[AmendmentStage]] = {
    "proposed": ["evaluated"],
    "evaluated": ["ratified"],
    "ratified": ["implemented"],
    "implemented": ["observed"],
    "observed": ["closed"],
    "closed": [],
}

IMMUTABLE_CORE_ARTICLES: frozenset[str] = frozenset(
    {"XIII", "XIV", "XV", "XVI", "SEVEN_INVARIANTS"},
)


def utc_now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def compute_lineage_hash(
    *,
    previous_receipt_id: str | None,
    receipt_id: str,
    payload_hash: str,
    previous_lineage_hash: str | None = None,
) -> str:
    material = "|".join(
        [
            previous_lineage_hash or "",
            previous_receipt_id or "",
            receipt_id,
            payload_hash,
        ]
    )
    return f"sha256:{hashlib.sha256(material.encode('utf-8')).hexdigest()}"


def new_receipt_id(prefix: str = "rcv2") -> str:
    return f"{prefix}:{uuid4()}"


def is_receipt_v2_complete(receipt: BaseReceiptV2) -> bool:
    """Return True when all constitutionally required fields are present and non-empty."""
    if not receipt.receipt_id or not receipt.runtime or not receipt.timestamp:
        return False
    if not receipt.action_type:
        return False
    if not receipt.inputs.request_id or not receipt.inputs.payload_hash:
        return False
    if not receipt.outputs.status or not receipt.outputs.result_hash:
        return False
    if not receipt.invariant.name:
        return False
    if not receipt.evidence.bundle_id:
        return False
    suff = receipt.evidence.sufficiency
    if not all(getattr(suff, key) is not None for key in _REQUIRED_SUFFICIENCY_KEYS):
        return False
    if not receipt.authority.source or not receipt.authority.legitimacy_basis:
        return False
    if receipt.reproducibility.mode is None:
        return False
    if not receipt.impact_boundary.scope_in or not receipt.impact_boundary.scope_out:
        return False
    if not receipt.accountability.primary_accountable_party:
        return False
    if not receipt.continuity.lineage_hash:
        return False
    if not receipt.signatures.runtime_signature:
        return False
    return True


def expected_next_lifecycle_stages(stage: LifecycleStage) -> list[LifecycleStage]:
    return list(LIFECYCLE_TRANSITIONS[stage])


def validate_lifecycle_transition(
    prior: BaseReceiptV2,
    nxt: BaseReceiptV2,
) -> tuple[bool, str]:
    """Rule-check Article XIV stage transitions between two receipts."""
    allowed = LIFECYCLE_TRANSITIONS.get(prior.lifecycle.stage, [])
    if nxt.lifecycle.stage not in allowed:
        return (
            False,
            f"invalid transition {prior.lifecycle.stage} -> {nxt.lifecycle.stage}; "
            f"allowed: {allowed}",
        )
    if nxt.lifecycle.previous_stage_receipt_id != prior.receipt_id:
        return False, "next receipt must reference prior receipt_id in previous_stage_receipt_id"
    if prior.lifecycle.stage == "closure":
        return False, "closure is terminal; no further lifecycle receipts permitted"
    return True, "ok"


def observation_follows_decision(
    decision: DecisionReceiptV2,
    observation: ObservationReceiptV2,
) -> tuple[bool, str]:
    ok, reason = validate_lifecycle_transition(decision, observation)
    if not ok:
        return ok, reason
    if observation.lifecycle.next_stage_expected not in {"divergence_or_closure", "divergence", "closure"}:
        return False, "observation next_stage_expected must anticipate divergence or closure"
    return True, "ok"


def closure_or_divergence_from_observation(
    observation: ObservationReceiptV2,
    *,
    reality_matches_expected: bool,
) -> LifecycleStage:
    """Rule 2 — Observation → Divergence or Closure."""
    return "closure" if reality_matches_expected else "divergence"


def validate_amendment_transition(
    from_stage: AmendmentStage,
    to_stage: AmendmentStage,
) -> None:
    allowed = AMENDMENT_TRANSITIONS.get(from_stage, [])
    if to_stage not in allowed:
        raise ValueError(f"Illegal amendment transition: {from_stage} → {to_stage}")


def validate_immutable_amendment(payload: AmendmentPayloadV2) -> None:
    """Article XVI §5 — immutable core requires explicit override path."""
    article_key = payload.article.upper().replace("ARTICLE ", "").strip()
    if article_key not in IMMUTABLE_CORE_ARTICLES:
        return
    if payload.change_type == "addition":
        return
    if payload.immutable_override and payload.unanimous_sovereign_ratification:
        return
    raise ValueError(
        f"Article {payload.article} is immutable; modification/removal requires "
        "immutable_override and unanimous_sovereign_ratification"
    )


def is_amendment_trigger_receipt(receipt: BaseReceiptV2) -> bool:
    """Return True when receipt may lawfully trigger constitutional amendment."""
    if isinstance(receipt, RemediationReceiptV2):
        return receipt.remediation.constitutional_trigger
    if isinstance(receipt, ArbitrationReceiptV2):
        return True
    if isinstance(receipt, ContinuityReceiptV2):
        return not receipt.lineage.continuity_satisfied
    if isinstance(receipt, SovereigntyReceiptV2):
        return not receipt.legitimacy.validated
    if isinstance(receipt, TruthReceiptV2):
        return not receipt.invariant.satisfied
    if isinstance(receipt, InstitutionalReceiptV2):
        return not receipt.compliance.compliant
    if receipt.action_type == "observer_petition":
        return True
    if receipt.action_type == "foundational_invariant_violation":
        return True
    return False
