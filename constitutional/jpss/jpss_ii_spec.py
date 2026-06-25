"""JPSS-II — continuity science: recursive self-governance and transferability."""

from __future__ import annotations

from typing import Literal

JPSS_II_VERSION = "2.0"
JPSS_II_REFERENCE = "JPSS-II — Judgment Preservation & Stewardship Science (Continuity Edition)"

# Recursive condition: JPSS must satisfy its own stewardship requirements
JPSS_RECURSIVE_CONDITION = "JPSS itself is subject to JPSS."

JPSS_II_TRANSFERABILITY_LAW = (
    "A judgment-preservation system must be transferable without its original stewards. "
    "Otherwise it has failed its own stewardship requirements."
)

JPSS_II_TRANSFERABILITY_REQUIREMENTS: tuple[str, ...] = (
    "learnable_by_stewards_who_never_met_the_founder",
    "reconstructable_from_artifacts",
    "extendable_by_future_stewards",
    "criticizable_without_collapsing",
    "improvable_without_losing_identity",
)

ValidityAxis = Literal["epistemic_validity", "stewardship_validity"]

JPSS_II_VALIDITY_AXES: tuple[ValidityAxis, ...] = (
    "epistemic_validity",
    "stewardship_validity",
)

JPSS_II_VALIDITY_DESCRIPTIONS: dict[ValidityAxis, str] = {
    "epistemic_validity": "Is the model correct?",
    "stewardship_validity": "Can the model survive new stewards?",
}

# Theory must be: correct, reconstructable, transferable, evolvable, identity-preserving
JPSS_II_CONTINUITY_SCIENCE_MARKS: tuple[str, ...] = (
    "correct",
    "reconstructable",
    "transferable",
    "evolvable",
    "identity_preserving",
)

# Continuity-science evidence hierarchy (strongest evidence = independent steward replication)
EvidenceTier = Literal[
    "theory",
    "case_studies",
    "cross_domain_validation",
    "independent_steward",
    "independent_application",
    "independent_improvement",
]

JPSS_II_EVIDENCE_HIERARCHY: tuple[EvidenceTier, ...] = (
    "theory",
    "case_studies",
    "cross_domain_validation",
    "independent_steward",
    "independent_application",
    "independent_improvement",
)

JPSS_II_EVIDENCE_DESCRIPTIONS: dict[EvidenceTier, str] = {
    "theory": "Formal spec, diagrams, and normative constants.",
    "case_studies": "Recorded judgment cycles and boundary decisions in registers.",
    "cross_domain_validation": "JPSS validated across adaptive, invariant, and constitutional layers.",
    "independent_steward": "A steward who never met the founder applies JPSS competently.",
    "independent_application": "Independent steward runs dual-pipeline formation and reconstruction.",
    "independent_improvement": "Independent steward extends JPSS without identity collapse.",
}

# Three-layer architecture (JPSS-A / JPSS-I / JPSS-C)
JPSSLayerCode = Literal["adaptive", "invariant", "constitutional"]

JPSS_II_THREE_LAYER_STACK: tuple[JPSSLayerCode, ...] = (
    "adaptive",
    "invariant",
    "constitutional",
)

JPSS_II_LAYER_LABELS: dict[JPSSLayerCode, str] = {
    "adaptive": "JPSS-A — What should change",
    "invariant": "JPSS-I — What must remain true",
    "constitutional": "JPSS-C — How the system decides what belongs in A vs B",
}

# Dar-z insight: the adaptive/invariant boundary is itself a judgment
JPSS_II_BOUNDARY_IS_JUDGMENT = (
    "The classification of core values, constitutional commitments, sacred constraints, "
    "and identity markers is itself a judgment — not a given."
)

JPSS_II_IDENTITY_EVOLUTION_PARADOX = (
    "Preserve identity, evolve identity, without losing identity. "
    "Constitutional judgment governs invariant selection so invariants are not permanently "
    "frozen merely because they were historically classified as invariant."
)

JPSS_II_MIN_TRANSFERABILITY_INDEX = 0.80

__all__ = [
    "EvidenceTier",
    "JPSSLayerCode",
    "JPSS_II_BOUNDARY_IS_JUDGMENT",
    "JPSS_II_CONTINUITY_SCIENCE_MARKS",
    "JPSS_II_EVIDENCE_DESCRIPTIONS",
    "JPSS_II_EVIDENCE_HIERARCHY",
    "JPSS_II_IDENTITY_EVOLUTION_PARADOX",
    "JPSS_II_LAYER_LABELS",
    "JPSS_II_MIN_TRANSFERABILITY_INDEX",
    "JPSS_II_REFERENCE",
    "JPSS_II_THREE_LAYER_STACK",
    "JPSS_II_TRANSFERABILITY_LAW",
    "JPSS_II_TRANSFERABILITY_REQUIREMENTS",
    "JPSS_II_VALIDITY_AXES",
    "JPSS_II_VALIDITY_DESCRIPTIONS",
    "JPSS_II_VERSION",
    "JPSS_RECURSIVE_CONDITION",
    "ValidityAxis",
]
