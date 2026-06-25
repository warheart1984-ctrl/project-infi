"""JPSS-C — Constitutional Judgment layer (formal specification)."""

from __future__ import annotations

from typing import Literal

JPSS_C_VERSION = "1.1"
JPSS_C_REFERENCE = "JPSS-C — Constitutional Judgment Preservation Science"

JPSS_C_ABSTRACT = (
    "JPSS-C defines the constitutional judgment layer: the process by which a system determines "
    "what becomes invariant, what remains adaptive, when invariants evolve, when invariants retire, "
    "how identity changes without collapsing, and how identity persists without ossifying."
)

# §1 Canonical constitutional cycle (meta-judgment loop)
JPSS_C_CANONICAL_CYCLE: tuple[str, ...] = (
    "signal",
    "candidate_value",
    "elevation_review",
    "invariant_classification",
    "steward_ratification",
    "invariant_register_update",
    "drift_monitoring",
    "retirement_review",
)

# §2 Canonical constitutional questions
JPSS_C_CANONICAL_QUESTIONS: tuple[str, ...] = (
    "Should this become invariant?",
    "Should this remain adaptive?",
    "Should this invariant be revised?",
    "Should this invariant be retired?",
    "Does this change preserve identity?",
    "Does this change distort identity?",
)

# §3 Constitutional elevation test
JPSS_C_ELEVATION_CRITERIA: tuple[str, ...] = (
    "protects_purpose",
    "prevents_catastrophic_drift",
    "defines_identity",
    "constrains_unacceptable_actions",
    "stabilizes_long_term_coherence",
    "required_for_reconstructability",
)

# §4 Constitutional de-sacralization test
JPSS_C_RETIREMENT_CRITERIA: tuple[str, ...] = (
    "purpose_no_longer_applies",
    "contradicts_higher_order_invariants",
    "blocks_necessary_adaptation",
    "causes_identity_distortion",
    "historically_contingent_not_essential",
    "fails_future_steward_test",
)

# §5 Canonical registers
JPSS_C_REGISTER_NAMES: tuple[str, ...] = (
    "invariant_candidate_ledger",
    "elevation_review_ledger",
    "retirement_review_ledger",
    "boundary_decisions_ledger",
)

# §6 Canonical drift modes
ConstitutionalDriftMode = Literal[
    "over_sacralization",
    "under_sacralization",
    "boundary_drift",
    "constitutional_drift",
]

JPSS_C_DRIFT_MODES: tuple[ConstitutionalDriftMode, ...] = (
    "over_sacralization",
    "under_sacralization",
    "boundary_drift",
    "constitutional_drift",
)

JPSS_C_DRIFT_MODE_DESCRIPTIONS: dict[ConstitutionalDriftMode, str] = {
    "over_sacralization": "Too many invariants → ossification.",
    "under_sacralization": "Too few invariants → identity collapse.",
    "boundary_drift": "Misclassification of adaptive vs invariant.",
    "constitutional_drift": "The constitutional process itself becomes unstable.",
}

# Governance chain (invariant lifecycle)
JPSS_C_GOVERNANCE_CHAIN: tuple[str, ...] = (
    "invariant_selection",
    "invariant_elevation",
    "invariant_revision",
    "invariant_retirement",
    "boundary_governance",
)

# Gate protocol for boundary crossings (exam + legitimacy)
JPSS_C_BOUNDARY_CHAIN: tuple[str, ...] = (
    "classify_change_domain",
    "apply_invariant_consultation",
    "require_reconstruction_evidence",
    "require_consequence_simulation",
    "record_constitutional_reasoning",
)

JPSS_C_INVARIANTS: tuple[str, ...] = (
    "invariant_alteration_requires_reconstruction",
    "adaptive_change_must_not_bypass_invariant_gate",
    "constitutional_reasoning_must_be_recorded",
    "consequence_simulation_required_before_invariant_change",
    "legitimacy_required_before_invariant_touch",
)

# II — Invariant Selection Engine
JPSS_C_SELECTION_INPUTS: tuple[str, ...] = (
    "candidate_value",
    "purpose_clauses",
    "historical_failures",
    "identity_markers",
    "risk_models",
    "steward_proposals",
)

SelectionDimension = Literal[
    "purpose_alignment",
    "identity_protection",
    "failure_prevention",
    "cross_era_stability",
    "reconstructability",
    "sacred_constraint_fit",
    "misclassification_cost",
]

JPSS_C_SELECTION_DIMENSIONS: tuple[SelectionDimension, ...] = (
    "purpose_alignment",
    "identity_protection",
    "failure_prevention",
    "cross_era_stability",
    "reconstructability",
    "sacred_constraint_fit",
    "misclassification_cost",
)

SelectionOutcome = Literal[
    "elevate_to_invariant",
    "keep_adaptive",
    "escalate_to_constitutional_review",
    "reject",
]

JPSS_C_SELECTION_OUTCOMES: tuple[SelectionOutcome, ...] = (
    "elevate_to_invariant",
    "keep_adaptive",
    "escalate_to_constitutional_review",
    "reject",
)

# III — Invariant Retirement Protocol
JPSS_C_RETIREMENT_TRIGGERS: tuple[str, ...] = (
    "repeated_conflict_with_purpose",
    "repeated_conflict_with_identity",
    "repeated_conflict_with_adaptive_survival",
    "historical_justification_no_longer_applies",
    "steward_consensus",
    "drift_detection",
)

JPSS_C_RETIREMENT_STEPS: tuple[str, ...] = (
    "context_reconstruction",
    "purpose_reevaluation",
    "identity_impact_analysis",
    "failure_risk_modeling",
    "steward_deliberation",
    "retirement_vote",
    "register_update",
    "continuity_review",
)

# IV — Constitutional Drift Detector
ConstitutionalDriftType = Literal[
    "boundary_drift",
    "over_sacralization",
    "under_sacralization",
    "identity_distortion",
    "purpose_erosion",
    "commitment_inflation",
]

JPSS_C_DRIFT_TYPES: tuple[ConstitutionalDriftType, ...] = (
    "boundary_drift",
    "over_sacralization",
    "under_sacralization",
    "identity_distortion",
    "purpose_erosion",
    "commitment_inflation",
)

JPSS_C_DRIFT_SIGNALS: tuple[str, ...] = (
    "too_many_invariants",
    "too_few_invariants",
    "invariants_contradicting_each_other",
    "invariants_contradicting_purpose",
    "invariants_blocking_survival",
    "invariants_becoming_symbolic_only",
)

JPSS_C_DRIFT_INDEX_COMPONENTS: tuple[str, ...] = (
    "boundary_stability",
    "invariant_turnover_rate",
    "identity_coherence",
    "purpose_alignment",
    "sacred_constraint_integrity",
)

JPSS_C_MIN_DRIFT_INDEX = 0.80

# V — JPSS Transferability Test
JPSS_C_TRANSFERABILITY_TEST_COMPONENTS: tuple[str, ...] = (
    "reconstruction_test",
    "application_test",
    "critique_test",
    "extension_test",
    "stewardship_test",
)

JPSS_C_TRANSFERABILITY_PASSING_CONDITION = (
    "JPSS survives contact with a steward who never met its founders."
)

ConstitutionalAction = Literal[
    "invariant_selection",
    "invariant_elevation",
    "invariant_revision",
    "invariant_retirement",
    "boundary_governance",
]

JPSS_C_ACTIONS: tuple[ConstitutionalAction, ...] = (
    "invariant_selection",
    "invariant_elevation",
    "invariant_revision",
    "invariant_retirement",
    "boundary_governance",
)

ConstitutionalClassification = Literal[
    "adaptive_domain",
    "invariant_domain",
    "boundary_consultation",
    "requires_legitimacy_review",
]

JPSS_C_CLASSIFICATIONS: tuple[ConstitutionalClassification, ...] = (
    "adaptive_domain",
    "invariant_domain",
    "boundary_consultation",
    "requires_legitimacy_review",
)

# VI — Dar-z next questions (theory continuity map)
JPSS_C_DAR_Z_QA: tuple[tuple[str, str], ...] = (
    (
        "How do we prevent over-sacralization?",
        "Monitor invariant inflation and enforce retirement protocols.",
    ),
    (
        "How do we prevent under-sacralization?",
        "Ensure purpose, identity, and sacred constraints remain anchored.",
    ),
    (
        "How do we detect boundary drift early?",
        "Through the constitutional drift detector's boundary stability index.",
    ),
    (
        "How do we train stewards to classify invariants?",
        "Through the constitutional judgment curriculum.",
    ),
    (
        "How do we ensure invariants don't contradict each other?",
        "Invariant coherence checks.",
    ),
    (
        "How do we ensure invariants don't contradict purpose?",
        "Purpose-alignment audits.",
    ),
    (
        "How do we ensure invariants don't block survival?",
        "Adaptive-pressure stress tests.",
    ),
    (
        "How do we ensure identity evolves safely?",
        "Identity evolution protocols.",
    ),
    (
        "How do we ensure identity doesn't collapse?",
        "Identity drift detectors.",
    ),
    (
        "How do we ensure identity doesn't ossify?",
        "Invariant retirement mechanisms.",
    ),
    (
        "How do we reconstruct constitutional judgment historically?",
        "Through the boundary decisions ledger.",
    ),
    (
        "How do we model constitutional drift mathematically?",
        "Through invariant turnover rates and boundary entropy.",
    ),
    (
        "How do we encode sacred constraints formally?",
        "As non-negotiable invariants with zero-tolerance drift.",
    ),
    (
        "How do we test whether a value is truly core?",
        "Through cross-era stability and purpose alignment.",
    ),
    (
        "How do we test whether a commitment is obsolete?",
        "Through failure-risk modeling and purpose re-evaluation.",
    ),
    (
        "How do we test whether identity markers are still valid?",
        "Through identity coherence analysis.",
    ),
    (
        "How do we prevent political capture of invariants?",
        "Through multi-steward constitutional review.",
    ),
    (
        "How do we prevent cultural capture of invariants?",
        "Through cross-domain invariant validation.",
    ),
    (
        "How do we ensure JPSS itself doesn't ossify?",
        "Through the JPSS transferability test.",
    ),
    (
        "How do we ensure JPSS itself doesn't drift?",
        "Through the JPSS constitutional drift detector.",
    ),
)

__all__ = [
    "ConstitutionalAction",
    "ConstitutionalClassification",
    "ConstitutionalDriftMode",
    "ConstitutionalDriftType",
    "JPSS_C_ABSTRACT",
    "JPSS_C_ACTIONS",
    "JPSS_C_BOUNDARY_CHAIN",
    "JPSS_C_CANONICAL_CYCLE",
    "JPSS_C_CANONICAL_QUESTIONS",
    "JPSS_C_CLASSIFICATIONS",
    "JPSS_C_DAR_Z_QA",
    "JPSS_C_DRIFT_INDEX_COMPONENTS",
    "JPSS_C_DRIFT_MODE_DESCRIPTIONS",
    "JPSS_C_DRIFT_MODES",
    "JPSS_C_DRIFT_SIGNALS",
    "JPSS_C_DRIFT_TYPES",
    "JPSS_C_ELEVATION_CRITERIA",
    "JPSS_C_GOVERNANCE_CHAIN",
    "JPSS_C_INVARIANTS",
    "JPSS_C_MIN_DRIFT_INDEX",
    "JPSS_C_REFERENCE",
    "JPSS_C_REGISTER_NAMES",
    "JPSS_C_RETIREMENT_CRITERIA",
    "JPSS_C_RETIREMENT_STEPS",
    "JPSS_C_RETIREMENT_TRIGGERS",
    "JPSS_C_SELECTION_DIMENSIONS",
    "JPSS_C_SELECTION_INPUTS",
    "JPSS_C_SELECTION_OUTCOMES",
    "JPSS_C_TRANSFERABILITY_PASSING_CONDITION",
    "JPSS_C_TRANSFERABILITY_TEST_COMPONENTS",
    "JPSS_C_VERSION",
    "SelectionDimension",
    "SelectionOutcome",
]
