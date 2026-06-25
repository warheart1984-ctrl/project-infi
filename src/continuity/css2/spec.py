"""CSS-2 — Threshold governance + recalibration governance (v0.2 over v0.1)."""

from __future__ import annotations

from typing import Literal

CSS2_REFERENCE = "Continuity Stewardship Stack CSS-2"
CSS2_VERSION = "0.2"

# --- v0.2: Four operations (non-overlapping) ---
OPERATION_LEARNING = "learning"
OPERATION_CALIBRATION = "calibration"
OPERATION_RECALIBRATION = "recalibration"
OPERATION_CONSTITUTIONAL_RECALIBRATION = "constitutional_recalibration"

ContinuityOperation = Literal[
    "learning",
    "calibration",
    "recalibration",
    "constitutional_recalibration",
]

FOUR_OPERATIONS: tuple[str, ...] = (
    OPERATION_LEARNING,
    OPERATION_CALIBRATION,
    OPERATION_RECALIBRATION,
    OPERATION_CONSTITUTIONAL_RECALIBRATION,
)

# CSS-2 governs two layers
LAYER_THRESHOLD_GOVERNANCE = "threshold_governance"
LAYER_RECALIBRATION_GOVERNANCE = "recalibration_governance"

CSS2_LAYERS: tuple[str, ...] = (
    LAYER_THRESHOLD_GOVERNANCE,
    LAYER_RECALIBRATION_GOVERNANCE,
)

THRESHOLD_LIFECYCLE: tuple[str, ...] = (
    "creation",
    "calibration_use",
    "monitoring",
    "delta_proposal",
    "archival",
)

THRESHOLD_FAILURE_MISSING = "missing_threshold"
THRESHOLD_FAILURE_DUPLICATED = "duplicated_threshold"
THRESHOLD_FAILURE_CONTRADICTORY = "contradictory_threshold"
THRESHOLD_FAILURE_ORPHANED = "orphaned_threshold"
THRESHOLD_FAILURE_OPAQUE = "opaque_threshold"

ThresholdGovernanceFailureKind = Literal[
    "missing_threshold",
    "duplicated_threshold",
    "contradictory_threshold",
    "orphaned_threshold",
    "opaque_threshold",
]

# v0.2 JPSS-2 pipeline (threshold-native)
JPSS2_STAGE_ENVIRONMENT = "environment"
JPSS2_STAGE_PERCEPTION = "perception"
JPSS2_STAGE_SALIENCE = "salience"
JPSS2_STAGE_THRESHOLD_LOOKUP = "threshold_lookup"
JPSS2_STAGE_CALIBRATION = "calibration"
JPSS2_STAGE_DECISION = "decision"
JPSS2_STAGE_OUTCOME = "outcome"
JPSS2_STAGE_REFLECTION = "reflection"
JPSS2_STAGE_MISMATCH_DETECTION = "threshold_mismatch_detection"
JPSS2_STAGE_RECALIBRATION_PROPOSAL = "recalibration_proposal"
JPSS2_STAGE_RECALIBRATION_GOVERNANCE = "recalibration_governance"
JPSS2_STAGE_THRESHOLD_UPDATE = "threshold_update"

JPSS2_PIPELINE: tuple[str, ...] = (
    JPSS2_STAGE_ENVIRONMENT,
    JPSS2_STAGE_PERCEPTION,
    JPSS2_STAGE_SALIENCE,
    JPSS2_STAGE_THRESHOLD_LOOKUP,
    JPSS2_STAGE_CALIBRATION,
    JPSS2_STAGE_DECISION,
    JPSS2_STAGE_OUTCOME,
    JPSS2_STAGE_REFLECTION,
    JPSS2_STAGE_MISMATCH_DETECTION,
    JPSS2_STAGE_RECALIBRATION_PROPOSAL,
    JPSS2_STAGE_RECALIBRATION_GOVERNANCE,
    JPSS2_STAGE_THRESHOLD_UPDATE,
)

RECALIBRATION_BOUNDARY_RULE = (
    "Recalibration occurs only when a threshold changes. "
    "Everything else is learning, interpretation, calibration, reflection, or judgment."
)

MINIMAL_UNIT_RECALIBRATION = "Δ-threshold (ThresholdDelta)"
MINIMAL_UNIT_CONSTITUTIONAL = "Δ-recalibration-rule (RecalibrationRuleDelta)"

# --- v0.1 legacy (recalibration engine + JPSS extension) ---
JPSS1_STAGES: tuple[str, ...] = (
    "environment",
    "perception",
    "salience",
    "calibration",
    "decision",
    "outcome",
    "reflection",
    "calibration_update",
)

JPSS2_RECALIBRATION_STAGES: tuple[str, ...] = (
    "recalibration_trigger_detection",
    "recalibration_proposal",
    "recalibration_governance",
    "recalibration_event",
)

JPSS2_FULL_PIPELINE: tuple[str, ...] = (
    JPSS1_STAGES[:7] + JPSS2_RECALIBRATION_STAGES + ("calibration_update_governed",)
)

JPSS2_JUDGMENT_LAYERS = (1, 7)
JPSS2_CALIBRATION_LAYERS = (4, 12)
JPSS2_RECALIBRATION_LAYERS = (8, 11)

RECALIBRATION_AMENDMENT_ID = "CRK-1-Amendment-X"
RECALIBRATION_AMENDMENT_TITLE = "Threshold and Recalibration Governance"

RECALIBRATION_AMENDMENT_CLAUSES: tuple[str, ...] = (
    "Thresholds as first-class objects — all decision boundaries explicit.",
    "Recalibration as Δ-threshold — threshold changes are never implicit drift.",
    "Trigger requirement — persistent mismatch, repeated failure, calibration error, or mandate.",
    "Invariance constraint — no violation of core identity or non-derogable constraints.",
    "Adversarial review — Red/Blue/Black/White/Gold challenge required.",
    "Legitimacy test — process, evidence, invariant check, continuity impact assessed.",
    "Auditability — every event logged, reconstructable, attributable, reviewable.",
    "Constitutional recalibration — changes to who/when/how Δ-threshold is allowed are amendments.",
)

LEGITIMATE_TRIGGER_TYPES: tuple[str, ...] = (
    "evidence",
    "drift",
    "failure",
    "mandate",
    "other",
)

OBSERVER_TRAINING_PHASES: tuple[tuple[str, str], ...] = (
    ("phase_1_concept_free", "Concept-free observation — raw cases, no JPSS/CSS vocabulary."),
    ("phase_2_vocabulary", "Vocabulary introduction — calibration, drift, invariants, stewardship."),
    ("phase_3_f5_independence", "F5 vocabulary-independence — domain language only, measure collapse."),
    ("phase_4_meta_observation", "Meta-observation — when to revise interpretation."),
    ("phase_5_governance_drills", "Recalibration governance — Red/Blue/Black/White/Gold exercises."),
)

STEWARDSHIP_DEFINITION = (
    "Stewardship = governance of recalibration legitimacy. "
    "Stewards do not recalibrate; stewards govern when recalibration is allowed."
)
