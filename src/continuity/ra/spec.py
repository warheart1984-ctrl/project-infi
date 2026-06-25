"""RA-COS-1 / RASP-1 specification constants."""

from __future__ import annotations

RASP1_REFERENCE = "Reality-Anchored Steward Protocol RASP-1"
RA_COS1_REFERENCE = "Reality-Anchored Continuity OS RA-COS-1"
VAS1_REFERENCE = "Validation After Surpassment VAS-1"
PSDD1_REFERENCE = "Post-Surpassment Drift Detector PSDD-1"
RAG_LOOP_REFERENCE = "Reality-Anchored Governance Loop RAG-Loop"
CBCL1_REFERENCE = "Consequence-Based Continuity Ledger CBCL-1"

EPISTEMIC_INSIGHT = (
    "Continuity is not validated by founders, stewards, or the lineage — "
    "continuity is validated by consequences."
)

# RAG-Loop stages
RAG_STAGE_SURPASSMENT = "Surpassment"
RAG_STAGE_ACCEPTANCE = "Acceptance"
RAG_STAGE_VALIDATION = "Validation"
RAG_STAGE_INTEGRATION = "Integration"
RAG_STAGE_MONITORING = "Monitoring"
RAG_STAGE_CORRECTION = "Correction"

RAG_LOOP_STAGES: tuple[str, ...] = (
    RAG_STAGE_SURPASSMENT,
    RAG_STAGE_ACCEPTANCE,
    RAG_STAGE_VALIDATION,
    RAG_STAGE_INTEGRATION,
    RAG_STAGE_MONITORING,
    RAG_STAGE_CORRECTION,
)

# RASP-1 steward responsibilities
R1_REALITY_PRECEDENCE = "If lineage consensus and reality conflict, reality wins."
R2_CONSEQUENCE_TRACKING = "Stewards must track real-world consequences of accepted changes."
R3_REVERSIBILITY = "Every structural change must be revertible if reality contradicts it."
R4_RECONSTRUCTABILITY = "No change may push reconstruction cost beyond the configured threshold (K4)."
R5_DRIFT_VIGILANCE = "Stewards must monitor post-acceptance drift (PSDD-1) and act on it."

RASP_RESPONSIBILITIES: tuple[str, ...] = (
    R1_REALITY_PRECEDENCE,
    R2_CONSEQUENCE_TRACKING,
    R3_REVERSIBILITY,
    R4_RECONSTRUCTABILITY,
    R5_DRIFT_VIGILANCE,
)

INVARIANT_K4 = "K4 — Reconstructability Protection"

# Consequence-weighted invariant update
DEFAULT_LEARNING_RATE = 0.1
INVARIANT_DEPRECATION_THRESHOLD = 0.2
INVARIANT_REVIEW_THRESHOLD = 0.4

# VAS-1
VAS1_MIN_CRITERIA_PASSED = 3

VAS1_CRITERIA: tuple[tuple[str, str], ...] = (
    ("predictiveAccuracy", "Predictive Accuracy — improvement predicts real-world behavior better."),
    ("explanatoryCompression", "Explanatory Compression — explains more with fewer assumptions."),
    ("crossDomainConvergence", "Cross-Domain Convergence — independent domains rediscover the structure."),
    ("operationalOutcome", "Operational Success — applying the improvement yields better outcomes."),
    ("critiqueStability", "Stability Under Critique — withstands adversarial testing."),
)

# PSDD-1 bands (PSD = μD + νE + ξC + ρO + σL)
PSD_STABLE_MAX = 0.3
PSD_REEVALUATION_THRESHOLD = 0.6
PSD_WATCH_MAX = PSD_REEVALUATION_THRESHOLD
PSD_REJECTION_THRESHOLD = 0.8
PSD_CRITICAL_MAX = PSD_REJECTION_THRESHOLD

PSDD_SIGNALS: tuple[tuple[str, str], ...] = (
    ("predictive_divergence", "PSDD-1.1 — Predictive Divergence"),
    ("explanatory_inflation", "PSDD-1.2 — Explanatory Inflation"),
    ("convergence_failure", "PSDD-1.3 — Convergence Failure"),
    ("operational_underperformance", "PSDD-1.4 — Operational Underperformance"),
    ("load_spike", "PSDD-1.5 — Steward Load Spike"),
)

PSDD1_FORMULA = "PSD = μD + νE + ξC + ρO + σL"

# PSDD-1 component weights
PSD_WEIGHT_PREDICTIVE = 0.25
PSD_WEIGHT_EXPLANATORY = 0.20
PSD_WEIGHT_CONVERGENCE = 0.20
PSD_WEIGHT_OPERATIONAL = 0.20
PSD_WEIGHT_LOAD = 0.15

# K4 default
DEFAULT_RECONSTRUCTION_COST_THRESHOLD = 1.0
