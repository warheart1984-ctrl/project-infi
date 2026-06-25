"""ECK-2 normative constants — unified dual-pipeline epistemic kernel."""

from __future__ import annotations

from constitutional.jpss.spec import ECK2_MIN_DRIFT_SYMMETRY_INDEX, ECK2_REFERENCE

ECK2_VERSION = "2.0"

ECK2_PURPOSE = (
    "ECK-2 unifies the judgment formation pipeline (JPSS-F) and the judgment "
    "reconstruction pipeline (ECK-R) into a single kernel that preserves both "
    "how judgment is formed and how it is reconstructed."
)

ECK2_INVARIANTS: tuple[str, ...] = (
    "bidirectional_reconstructability",
    "drift_symmetry",
    "calibration_stability",
    "salience_stability",
    "environment_anchoring",
    "failure_aware_evolution",
)

ECK2_INVARIANT_DESCRIPTIONS: dict[str, str] = {
    "bidirectional_reconstructability": (
        "Any recorded judgment must be reconstructable via ECK-R to within defined tolerance."
    ),
    "drift_symmetry": (
        "Distinguish formation drift (how stewards form judgment) from "
        "reconstruction drift (how they interpret past judgment)."
    ),
    "calibration_stability": "Threshold updates must not destabilize core invariants.",
    "salience_stability": "Salience is a first-class constitutional variable in both pipelines.",
    "environment_anchoring": "Both pipelines begin from preserved environment snapshots.",
    "failure_aware_evolution": (
        "Failure Register must inform calibration updates and reconstruction of risk priors."
    ),
}

ECK2_FORMATION_PIPELINE = (
    "environment",
    "perception",
    "salience",
    "calibration",
    "decision",
    "outcome",
    "reflection",
    "calibration_update",
)

ECK2_RECONSTRUCTION_PIPELINE = (
    "environment",
    "perception_reconstruction",
    "salience_reconstruction",
    "calibration_reconstruction",
    "prior_reconstruction",
    "judgment_reconstruction",
    "significance_reconstruction",
    "continuity_update",
)

ECK2_SHARED_OBJECTS: tuple[str, ...] = (
    "EnvironmentState",
    "PerceptionState",
    "PerceptionReconstructionState",
    "SalienceState",
    "SalienceReconstructionState",
    "CalibrationState",
    "CalibrationReconstructionState",
    "PriorState",
    "JudgmentState",
    "JudgmentReconstructionState",
    "SignificanceState",
    "ContinuityState",
)

ECK2_FORMATION_REGISTERS: tuple[str, ...] = (
    "environment",
    "perception",
    "salience",
    "calibration",
    "decision",
    "outcome",
    "reflection",
    "failure",
)

ECK2_ENGINES: tuple[str, ...] = (
    "forward_engine",
    "reverse_engine",
    "continuity_engine",
    "succession_engine",
)

ECK2_COMPLIANCE_REQUIREMENTS: tuple[str, ...] = (
    "implement_both_pipelines",
    "maintain_all_required_registers",
    "expose_drift_metrics_per_layer",
    "gate_succession_on_dual_pipeline_competence",
)

__all__ = [
    "ECK2_COMPLIANCE_REQUIREMENTS",
    "ECK2_ENGINES",
    "ECK2_FORMATION_PIPELINE",
    "ECK2_FORMATION_REGISTERS",
    "ECK2_INVARIANTS",
    "ECK2_INVARIANT_DESCRIPTIONS",
    "ECK2_MIN_DRIFT_SYMMETRY_INDEX",
    "ECK2_PURPOSE",
    "ECK2_RECONSTRUCTION_PIPELINE",
    "ECK2_REFERENCE",
    "ECK2_SHARED_OBJECTS",
    "ECK2_VERSION",
]
