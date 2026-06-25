"""CSS-2 — Threshold governance + recalibration governance (v0.2 over v0.1)."""

# v0.2 — explicit Threshold / Δ-threshold layer
from src.continuity.css2.edge_cases import (
    EdgeCaseFinding,
    detect_false_recalibration,
    detect_hidden_recalibration,
    detect_recalibration_by_exception,
    detect_recalibration_by_silence,
    detect_threshold_camouflage,
)
from src.continuity.css2.jpss2_pipeline import (
    CalibrationResult,
    JPSS2PipelineResult,
    MismatchSignal,
    run_jpss2_slice,
)
from src.continuity.css2.operations import (
    OperationClassification,
    apply_threshold,
    classify_operation,
    test_a_learn_without_recalibrate,
    test_b_recalibrate_without_learn,
)
from src.continuity.css2.crk_invariants import check_crk_threshold_delta
from src.continuity.css2.recalibration_governance import (
    RecalibrationLegitimacyResult,
    TeamAdversarialReview,
    apply_approved_delta,
    evaluate_threshold_delta_legitimacy,
)
from src.continuity.css2.registry import default_recalibration_rule, seed_css1_thresholds
from src.continuity.css2.spec import (
    CSS2_LAYERS,
    CSS2_REFERENCE,
    CSS2_VERSION,
    FOUR_OPERATIONS,
    JPSS2_FULL_PIPELINE,
    JPSS2_PIPELINE,
    MINIMAL_UNIT_CONSTITUTIONAL,
    MINIMAL_UNIT_RECALIBRATION,
    RECALIBRATION_AMENDMENT_CLAUSES,
    RECALIBRATION_AMENDMENT_ID,
    RECALIBRATION_BOUNDARY_RULE,
    STEWARDSHIP_DEFINITION,
    JPSS2_RECALIBRATION_STAGES,
    LEGITIMATE_TRIGGER_TYPES,
    OBSERVER_TRAINING_PHASES,
)
from src.continuity.css2.threshold import (
    RecalibrationRule,
    RecalibrationRuleDelta,
    SystemState,
    Threshold,
    ThresholdDelta,
)
from src.continuity.css2.threshold_governance import (
    ThresholdGovernanceFailure,
    ThresholdGovernanceReport,
    audit_threshold_registry,
    find_relevant_thresholds,
)

# v0.1 — recalibration engine + amendment (unchanged)
from src.continuity.css2.amendment import (
    AmendmentComplianceResult,
    check_proposal_amendment,
    check_recalibration_amendment,
)
from src.continuity.css2.governance import (
    AdversarialReviewResult,
    RecalibrationGovernanceEngine,
    SimpleRecalibrationGovernance,
    default_recalibration_invariants,
)
from src.continuity.css2.jpss2 import JPSS2Pipeline, JPSS2PipelineResult as JPSS2EventPipelineResult, JPSS2StageResult
from src.continuity.css2.models import (
    Calibration,
    InvariantRef,
    RecalibrationEvent,
    RecalibrationLedger,
    RecalibrationProposalContext,
    RecalibrationTrigger,
    ThresholdBand,
    ThresholdChange,
    new_recalibration_event_id,
)
from src.continuity.css2.observer_training import (
    ObserverTrainingProtocol,
    ObserverTrainingSession,
    PhaseScore,
    TrainingCase,
)

__all__ = [
    # spec
    "CSS2_REFERENCE",
    "CSS2_VERSION",
    "CSS2_LAYERS",
    "FOUR_OPERATIONS",
    "JPSS2_PIPELINE",
    "JPSS2_FULL_PIPELINE",
    "RECALIBRATION_BOUNDARY_RULE",
    "MINIMAL_UNIT_RECALIBRATION",
    "MINIMAL_UNIT_CONSTITUTIONAL",
    "STEWARDSHIP_DEFINITION",
    "RECALIBRATION_AMENDMENT_ID",
    "RECALIBRATION_AMENDMENT_CLAUSES",
    # v0.2 threshold layer
    "Threshold",
    "ThresholdDelta",
    "RecalibrationRule",
    "RecalibrationRuleDelta",
    "SystemState",
    "OperationClassification",
    "classify_operation",
    "apply_threshold",
    "test_a_learn_without_recalibrate",
    "test_b_recalibrate_without_learn",
    "ThresholdGovernanceFailure",
    "ThresholdGovernanceReport",
    "audit_threshold_registry",
    "find_relevant_thresholds",
    "TeamAdversarialReview",
    "RecalibrationLegitimacyResult",
    "evaluate_threshold_delta_legitimacy",
    "apply_approved_delta",
    "check_crk_threshold_delta",
    "seed_css1_thresholds",
    "default_recalibration_rule",
    "CalibrationResult",
    "MismatchSignal",
    "JPSS2PipelineResult",
    "run_jpss2_slice",
    "EdgeCaseFinding",
    "detect_hidden_recalibration",
    "detect_false_recalibration",
    "detect_threshold_camouflage",
    "detect_recalibration_by_exception",
    "detect_recalibration_by_silence",
    # v0.1 engine
    "Calibration",
    "ThresholdBand",
    "ThresholdChange",
    "RecalibrationTrigger",
    "RecalibrationEvent",
    "RecalibrationProposalContext",
    "RecalibrationLedger",
    "InvariantRef",
    "new_recalibration_event_id",
    "RecalibrationGovernanceEngine",
    "SimpleRecalibrationGovernance",
    "AdversarialReviewResult",
    "default_recalibration_invariants",
    "AmendmentComplianceResult",
    "check_recalibration_amendment",
    "check_proposal_amendment",
    "JPSS2Pipeline",
    "JPSS2EventPipelineResult",
    "JPSS2StageResult",
    "ObserverTrainingProtocol",
    "ObserverTrainingSession",
    "PhaseScore",
    "TrainingCase",
    "OBSERVER_TRAINING_PHASES",
    "JPSS2_RECALIBRATION_STAGES",
    "LEGITIMATE_TRIGGER_TYPES",
]
