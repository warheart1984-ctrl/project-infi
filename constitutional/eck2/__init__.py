"""ECK-2 — Unified Epistemic Kernel (formation + reconstruction)."""

from constitutional.eck2.compliance import ECK2ComplianceReport, evaluate_eck2_compliance
from constitutional.eck2.continuity_engine import ECK2ContinuityEngine
from constitutional.eck2.formation_engine import ECK2FormationEngine
from constitutional.eck2.kernel import ECK2Kernel, eck2_from_csr
from constitutional.eck2.models import (
    CalibrationReconstructionState,
    ContinuityUpdateState,
    DriftSymmetryFinding,
    DriftSymmetryReport,
    ECK2PipelineResult,
    ECK2ReconstructionResult,
    JudgmentReconstructionState,
    PerceptionReconstructionState,
    SalienceReconstructionState,
)
from constitutional.eck2.reconstruction_engine import ECK2ReconstructionEngine
from constitutional.eck2.runtime import ECK2Runtime, ECK2_PIPELINE_STATE_ID, load_eck2_pipeline
from constitutional.eck2.spec import (
    ECK2_COMPLIANCE_REQUIREMENTS,
    ECK2_FORMATION_PIPELINE,
    ECK2_FORMATION_REGISTERS,
    ECK2_INVARIANTS,
    ECK2_INVARIANT_DESCRIPTIONS,
    ECK2_MIN_DRIFT_SYMMETRY_INDEX,
    ECK2_PURPOSE,
    ECK2_RECONSTRUCTION_PIPELINE,
    ECK2_REFERENCE,
    ECK2_SHARED_OBJECTS,
    ECK2_VERSION,
)
from constitutional.eck2.governance import succession_eck2_dual_pipeline_ready
from constitutional.eck2.succession_engine import check_eck2_succession_gate, run_eck2_succession_evaluation

__all__ = [
    "ECK2_FORMATION_PIPELINE",
    "ECK2_INVARIANTS",
    "ECK2_MIN_DRIFT_SYMMETRY_INDEX",
    "ECK2_PIPELINE_STATE_ID",
    "ECK2_RECONSTRUCTION_PIPELINE",
    "ECK2_REFERENCE",
    "ECK2_VERSION",
    "DriftSymmetryFinding",
    "DriftSymmetryReport",
    "ECK2ContinuityEngine",
    "ECK2FormationEngine",
    "ECK2Kernel",
    "ECK2PipelineResult",
    "ECK2ReconstructionResult",
    "ECK2ReconstructionEngine",
    "ECK2Runtime",
    "check_eck2_succession_gate",
    "eck2_from_csr",
    "load_eck2_pipeline",
    "run_eck2_succession_evaluation",
    "succession_eck2_dual_pipeline_ready",
]
