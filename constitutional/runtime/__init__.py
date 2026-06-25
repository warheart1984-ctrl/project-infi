"""Constitutional substrate — CSR, Receipt v2, transition ledger, observer verification."""

from constitutional.core import (
    DOMAIN_STATE_MAPS,
    LEGAL_TRANSITIONS,
    AmendmentContext,
    AmendmentEngine,
    StateObject,
    TransitionLedger as CoreTransitionLedger,
    validate_transition,
)
from constitutional.core.graph import map_domain_state
from constitutional.core.observer import ObserverVerificationEngine as CoreObserverEngine
from constitutional.core.observer import ObserverVerificationResult
from constitutional.runtime.amendments import (
    AmendmentReplayResult,
    AmendmentState,
    begin_amendment,
    process_amendment_receipts,
    replay_amendment,
    run_fitness_after_amendment,
)
from constitutional.runtime.constitutional_state import (
    ConstitutionalStateName,
    ReplayResult,
    StateObjectType,
    StateTransition,
    reconstruct_state,
    reconstruct_state_at,
    replay_state,
    transition_from_receipt,
)
from constitutional.runtime.observer_verification import (
    ObserverVerificationContext,
    ObserverVerificationReport,
    run_observer_verification,
)
from constitutional.runtime.receipts_v2 import (
    BaseReceiptV2,
    ConstitutionalRiskPayloadV2,
    DecisionReceiptV2,
    ReceiptContextV2,
    ReconstructabilityFitnessPayloadV2,
    ReconstructabilityFitnessReceiptV2,
    RiskReceiptV2,
    TransitionPayloadV2,
    TransitionReceiptV2,
    compute_lineage_hash,
    is_receipt_v2_complete,
    new_receipt_id,
    stable_json_hash,
    utc_now_rfc3339,
)
from constitutional.runtime.constitutional_debt import (
    ConstitutionalDebtState,
    apply_fitness_to_debt,
    compute_constitutional_debt_threats,
    compute_fitness_penalty,
    compute_personal_debt_threats,
    load_constitutional_debt,
    save_constitutional_debt,
)
from constitutional.runtime.fitness_governance import (
    FitnessGovernanceDecision,
    apply_fitness_to_governance_gate,
    evaluate_fitness_governance_gate,
    load_fitness_governance_decision,
)
from constitutional.runtime.fitness_risk import (
    ReconstructabilityRiskState,
    apply_fitness_to_risk,
    get_reconstructability_fitness_state,
    load_reconstructability_risk,
)
from constitutional.runtime.amendment_triggers import (
    AmendmentTriggerRecord,
    AmendmentTriggersState,
    apply_dashboard_to_amendment_triggers,
    maybe_trigger_reconstructability_amendment,
    open_or_escalate_amendment,
)
from constitutional.runtime.dashboard_governance import (
    GovernanceGateDecision,
    apply_and_persist_dashboard_governance,
    apply_dashboard_to_governance_gate,
    load_dashboard_governance_decision,
)
from constitutional.runtime.reconstructability_failures import (
    ALL_RECONSTRUCTABILITY_FAILURES,
    ReconstructabilityFailureClass,
)
from constitutional.runtime.reconstructability_fitness_runtime import (
    ReconstructabilityFitnessRuntime,
    ReconstructabilityFitnessState,
)
from constitutional.runtime.reconstructability_dashboard import (
    DASHBOARD_STATE_ID,
    ReconstructabilityDashboardRuntime,
    ReconstructabilityDashboardState,
    build_dashboard_observation_receipt,
    build_reconstructability_dashboard,
    load_reconstructability_dashboard,
)
from constitutional.runtime.runtime_charter import RUNTIME_CHARTER, charter_for
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.governance_gate import (
    GovernanceGateFailed,
    assert_constitutional_boot,
    require_constitutional_boot,
)
from constitutional.runtime.governance_gate import governance_gate as run_governance_gate
from constitutional.runtime.burnout_runtime import BurnoutRuntime, BurnoutState, RecoveryPlanState
from constitutional.runtime.personal_continuity_runtime import (
    PersonalContinuityRuntime,
    IdeaState,
    AssumptionState,
    CriticalContextState,
)
from constitutional.runtime.personal_constitutional_state import (
    PERSONAL_STATE_ID,
    PersonalConstitutionalState,
    PersonalConstitutionalStateRuntime,
    build_personal_observation_receipt,
    burnout_health_score,
    compute_architectural_continuity,
    compute_debt_score,
    compute_trend,
)
from constitutional.runtime.constitutional_state_model import (
    ConstitutionalStateModel,
    ConstitutionalStateObject,
    run_constitutional_state_update,
)
from constitutional.runtime.risk_runtime import (
    ConstitutionalRiskRuntime,
    ConstitutionalRiskState,
    refresh_constitutional_risk_forecasts,
)
from constitutional.runtime.global_constitutional_state import (
    GLOBAL_STATE_ID,
    ConstitutionalStateAggregator,
    GlobalConstitutionalState,
    aggregate_global_constitutional_state,
    build_constitutional_state_receipt,
    compute_constitutional_debt_score,
    compute_health_score,
    condition_from_health_score,
)
from constitutional.runtime.constitutional_state_scheduler import (
    ConstitutionalStateScheduler,
)
from constitutional.runtime.csr_bridge import register_domain_state, state_id_from_doc
from constitutional.runtime.domain_invariants import ALL_DOMAIN_INVARIANTS
from constitutional.runtime.receipt_stream import load_receipts_from_disk
from constitutional.runtime.transition_ledger import (
    ConstitutionalTransitionLedger,
    LedgerEntry,
    LedgerFailure,
    LedgerReplayResult,
)
from constitutional.runtime.survivability_enforcement import (
    ArticleS1Compliance,
    COLD_START_TEST_INTERVAL,
    FITNESS_ASSESSMENT_INTERVAL,
    FOUNDER_DEPENDENCY_REDUCTION_PHASES,
    SuccessionReadinessChecklist,
    SurvivabilityZone,
    THRESHOLD_TABLE,
    build_succession_readiness_checklist,
    classify_dashboard_metrics,
    cold_start_test_due,
    compute_succession_readiness_score,
    evaluate_article_s1_compliance,
    load_cold_start_schedule,
    record_cold_start_run,
)

ReceiptV2 = BaseReceiptV2
Transition = StateTransition
TransitionLedger = ConstitutionalTransitionLedger


class ObserverVerificationEngine:
    """Full receipt verification; use verify_state_core() for lightweight replay-only checks."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self._csr = csr
        self._core = CoreObserverEngine(csr)

    def verify_state(self, state_id: str) -> ObserverVerificationReport:
        state = self._csr.get_state(state_id)
        receipts = self._csr.receipts_for(state_id)
        ctx = ObserverVerificationContext(
            target_id=state_id,
            transition_receipts=receipts,
            canonical_state=state,
            ledger=self._csr.ledger,
            responsible_parties=["operator"],
        )
        return run_observer_verification(ctx)

    def verify_state_core(self, state_id: str) -> ObserverVerificationResult:
        return self._core.verify_state(state_id)


def get_personal_snapshot(csr: ConstitutionalStateRuntime) -> object:
    """Return the latest personal constitutional snapshot registered on CSR."""
    return csr.get_personal_snapshot()


__all__ = [
    "BurnoutRuntime",
    "BurnoutState",
    "CriticalContextState",
    "IdeaState",
    "PersonalContinuityRuntime",
    "RecoveryPlanState",
    "AssumptionState",
    "ALL_DOMAIN_INVARIANTS",
    "AmendmentEngine",
    "AmendmentTriggerRecord",
    "AmendmentTriggersState",
    "ArticleS1Compliance",
    "COLD_START_TEST_INTERVAL",
    "FITNESS_ASSESSMENT_INTERVAL",
    "FOUNDER_DEPENDENCY_REDUCTION_PHASES",
    "SuccessionReadinessChecklist",
    "SurvivabilityZone",
    "THRESHOLD_TABLE",
    "build_succession_readiness_checklist",
    "classify_dashboard_metrics",
    "cold_start_test_due",
    "compute_succession_readiness_score",
    "evaluate_article_s1_compliance",
    "load_cold_start_schedule",
    "record_cold_start_run",
    "apply_fitness_to_debt",
    "apply_fitness_to_governance_gate",
    "apply_fitness_to_risk",
    "compute_fitness_penalty",
    "evaluate_fitness_governance_gate",
    "FitnessGovernanceDecision",
    "get_reconstructability_fitness_state",
    "load_constitutional_debt",
    "load_fitness_governance_decision",
    "load_reconstructability_risk",
    "maybe_trigger_reconstructability_amendment",
    "open_or_escalate_amendment",
    "ReconstructabilityRiskState",
    "save_constitutional_debt",
    "AmendmentReplayResult",
    "AmendmentState",
    "assert_constitutional_boot",
    "BaseReceiptV2",
    "ConstitutionalDebtState",
    "ConstitutionalStateName",
    "ConstitutionalStateRuntime",
    "ALL_RECONSTRUCTABILITY_FAILURES",
    "ReconstructabilityFailureClass",
    "ReconstructabilityFitnessRuntime",
    "ReconstructabilityFitnessState",
    "ReconstructabilityDashboardRuntime",
    "ReconstructabilityDashboardState",
    "DASHBOARD_STATE_ID",
    "build_dashboard_observation_receipt",
    "build_reconstructability_dashboard",
    "load_reconstructability_dashboard",
    "GovernanceGateDecision",
    "apply_dashboard_to_governance_gate",
    "apply_and_persist_dashboard_governance",
    "apply_dashboard_to_amendment_triggers",
    "load_dashboard_governance_decision",
    "ReconstructabilityFitnessPayloadV2",
    "ReconstructabilityFitnessReceiptV2",
    "RUNTIME_CHARTER",
    "charter_for",
    "compute_constitutional_debt_threats",
    "compute_personal_debt_threats",
    "ConstitutionalRiskRuntime",
    "ConstitutionalRiskState",
    "ConstitutionalRiskPayloadV2",
    "RiskReceiptV2",
    "refresh_constitutional_risk_forecasts",
    "register_domain_state",
    "ConstitutionalStateModel",
    "ConstitutionalStateObject",
    "run_constitutional_state_update",
    "GLOBAL_STATE_ID",
    "ConstitutionalStateScheduler",
    "GlobalConstitutionalState",
    "aggregate_global_constitutional_state",
    "build_constitutional_state_receipt",
    "compute_constitutional_debt_score",
    "compute_health_score",
    "condition_from_health_score",
    "load_receipts_from_disk",
    "ConstitutionalTransitionLedger",
    "CoreTransitionLedger",
    "DecisionReceiptV2",
    "DOMAIN_STATE_MAPS",
    "GovernanceGateFailed",
    "LEGAL_TRANSITIONS",
    "LedgerEntry",
    "LedgerFailure",
    "LedgerReplayResult",
    "ObserverVerificationContext",
    "ObserverVerificationEngine",
    "ObserverVerificationReport",
    "ObserverVerificationResult",
    "PERSONAL_STATE_ID",
    "PersonalConstitutionalState",
    "PersonalConstitutionalStateRuntime",
    "build_personal_observation_receipt",
    "burnout_health_score",
    "compute_architectural_continuity",
    "compute_debt_score",
    "compute_trend",
    "ReceiptContextV2",
    "ReceiptV2",
    "ReplayResult",
    "StateObject",
    "StateObjectType",
    "StateTransition",
    "Transition",
    "TransitionLedger",
    "TransitionPayloadV2",
    "TransitionReceiptV2",
    "begin_amendment",
    "compute_lineage_hash",
    "get_personal_snapshot",
    "run_governance_gate",
    "require_constitutional_boot",
    "map_domain_state",
    "new_receipt_id",
    "process_amendment_receipts",
    "run_fitness_after_amendment",
    "reconstruct_state",
    "reconstruct_state_at",
    "replay_amendment",
    "replay_state",
    "run_observer_verification",
    "is_receipt_v2_complete",
    "stable_json_hash",
    "state_id_from_doc",
    "transition_from_receipt",
    "utc_now_rfc3339",
    "validate_transition",
]