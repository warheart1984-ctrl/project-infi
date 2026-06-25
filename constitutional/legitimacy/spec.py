"""Stewardship Legitimacy Protocol v1.0 — canonical normative specification."""

from __future__ import annotations

from typing import Literal

LEGITIMACY_VERSION = "1.0"
LEGITIMACY_REFERENCE = "Stewardship Legitimacy Protocol v1.0"

STEWARDSHIP_LEGITIMACY_DEFINITION = (
    "Stewardship Legitimacy = the system's rule for who may alter the conditions of continuity."
)

LEGITIMACY_PURPOSE = (
    "Define who is authorized to govern the invariant layer of a continuity system. "
    "Replace founder, positional, majority, and cultural authority with authority by "
    "demonstrated, reconstructable stewardship competence."
)

# Full four-layer judgment stack
JudgmentLayer = Literal["adaptive", "invariant", "constitutional", "legitimacy"]

JUDGMENT_STACK_LAYERS: tuple[JudgmentLayer, ...] = (
    "adaptive",
    "invariant",
    "constitutional",
    "legitimacy",
)

JUDGMENT_LAYER_DESCRIPTIONS: dict[JudgmentLayer, str] = {
    "adaptive": "What should change.",
    "invariant": "What must remain true.",
    "constitutional": "How the boundary between them is governed.",
    "legitimacy": "Who is authorized to govern that boundary.",
}

CONSTITUTIONAL_JUDGMENT_DEFINITION = "How invariant classifications are made."
CONSTITUTIONAL_LEGITIMACY_DEFINITION = "Who is authorized to make them."

# §1 Legitimacy Criteria (minimum bar)
LEGITIMACY_CRITERIA: tuple[tuple[str, str], ...] = (
    ("purpose_reconstruction", "Original intent, constraints, failure conditions, purpose evolution."),
    ("identity_reconstruction", "Identity markers, sacred constraints, core values, commitments."),
    ("judgment_reconstruction", "Historical decisions, JPSS cycles, salience, calibration, failure updates."),
    (
        "constitutional_reasoning_reconstruction",
        "Invariant elevation/retirement, boundary drawing, identity preservation.",
    ),
    (
        "consequence_simulation",
        "Downstream effects, identity-preserving vs breaking changes, failure and drift risks.",
    ),
    (
        "drift_detection_competence",
        "Adaptive, invariant, boundary, constitutional, and legitimacy drift detection.",
    ),
)

LEGITIMACY_CRITERION_DEMONSTRATIONS: tuple[str, ...] = tuple(key for key, _ in LEGITIMACY_CRITERIA)

LEGITIMACY_CRITERION_RULE = (
    "No one is legitimate to change continuity who cannot first reconstruct continuity."
)

# §2 Legitimacy Process — five phases
LegitimacyProcessPhase = Literal[
    "demonstration",
    "interrogation",
    "red_team",
    "receipts",
    "ratification",
]

LEGITIMACY_PROCESS_PHASES: tuple[LegitimacyProcessPhase, ...] = (
    "demonstration",
    "interrogation",
    "red_team",
    "receipts",
    "ratification",
)

LEGITIMACY_PROCESS_DESCRIPTIONS: dict[LegitimacyProcessPhase, str] = {
    "demonstration": "Public reconstruction and consequence modeling with receipts.",
    "interrogation": "Existing stewards challenge reconstructions, boundaries, and simulations.",
    "red_team": "Independent stewards stress-test reasoning for capture and blind spots.",
    "receipts": "Reconstruction, constitutional, drift, consequence, and legitimacy logs recorded.",
    "ratification": "Plural approval only if reconstructions accurate and no capture detected.",
}

# §3 Legitimacy Receipt types
LEGITIMACY_RECEIPT_TYPES: tuple[str, ...] = (
    "reconstruction_receipts",
    "boundary_receipts",
    "drift_receipts",
    "consequence_receipts",
    "legitimacy_receipts",
)

# §4 Legitimacy drift model (v1.0)
LEGITIMACY_DRIFT_CLASSES: tuple[str, ...] = (
    "over_concentration_drift",
    "under_concentration_drift",
    "competence_drift",
    "cultural_capture_drift",
    "founder_capture_drift",
    "steward_capture_drift",
    "boundary_drift",
)

# Legitimacy judgment — meta-layer subject to JPSS
LEGITIMACY_JUDGMENT_SURFACES: tuple[str, ...] = (
    "legitimacy_environment",
    "legitimacy_salience",
    "legitimacy_calibration",
    "legitimacy_drift",
)

LEGITIMACY_JUDGMENT_DESCRIPTIONS: dict[str, str] = {
    "legitimacy_environment": "Incentives, risks, and pressures shaping who gets certified.",
    "legitimacy_salience": "Signals of competence noticed or ignored.",
    "legitimacy_calibration": "How strict the bar is for granting authority.",
    "legitimacy_drift": "How the standard for qualified steward erodes or ossifies.",
}

# §5 Capture vectors explicitly rejected
LEGITIMACY_CAPTURE_VECTORS: tuple[str, ...] = (
    "founders_blessing",
    "current_steward_preference",
    "majority_vote",
    "most_competent_person_wins_unaudited",
    "positional_title",
    "cultural_authority",
)

# §6 Legitimacy stability requirements
LEGITIMACY_STABILITY_REQUIREMENTS: tuple[str, ...] = (
    "legitimacy_is_earned_not_inherited",
    "legitimacy_is_reconstructable",
    "legitimacy_is_criticizable",
    "legitimacy_is_extendable",
    "legitimacy_is_revocable",
    "legitimacy_is_drift_detectable",
    "legitimacy_is_plural_not_singular",
    "legitimacy_is_grounded_in_stewardship_competence",
)

STEWARDSHIP_LEGITIMACY_PROBLEM = (
    "Can a continuity system reliably determine who is qualified to alter continuity?"
)

MIN_LEGITIMACY_INDEX = 0.80
MIN_PLURALITY_FOR_INVARIANT_ALTERATION = 2
MAX_PLURALITY_BEFORE_UNDER_CONCENTRATION = 12

__all__ = [
    "CONSTITUTIONAL_JUDGMENT_DEFINITION",
    "CONSTITUTIONAL_LEGITIMACY_DEFINITION",
    "JUDGMENT_LAYER_DESCRIPTIONS",
    "JUDGMENT_STACK_LAYERS",
    "JudgmentLayer",
    "LEGITIMACY_CAPTURE_VECTORS",
    "LEGITIMACY_CRITERIA",
    "LEGITIMACY_CRITERION_DEMONSTRATIONS",
    "LEGITIMACY_CRITERION_RULE",
    "LEGITIMACY_DRIFT_CLASSES",
    "LEGITIMACY_JUDGMENT_DESCRIPTIONS",
    "LEGITIMACY_JUDGMENT_SURFACES",
    "LEGITIMACY_PROCESS_DESCRIPTIONS",
    "LEGITIMACY_PROCESS_PHASES",
    "LEGITIMACY_PURPOSE",
    "LEGITIMACY_RECEIPT_TYPES",
    "LEGITIMACY_REFERENCE",
    "LEGITIMACY_STABILITY_REQUIREMENTS",
    "LEGITIMACY_VERSION",
    "LegitimacyProcessPhase",
    "MAX_PLURALITY_BEFORE_UNDER_CONCENTRATION",
    "MIN_LEGITIMACY_INDEX",
    "MIN_PLURALITY_FOR_INVARIANT_ALTERATION",
    "STEWARDSHIP_LEGITIMACY_DEFINITION",
    "STEWARDSHIP_LEGITIMACY_PROBLEM",
]
