"""CSS-1 — Full Continuity Stack Specification (final form, nine layers)."""

from __future__ import annotations

from typing import Literal

CSS1_REFERENCE = "Full Continuity Stack CSS-1"
CSS1_VERSION = "2.0"

# Nine integrated layers
MODULE_CE1 = "CE-1"
MODULE_SED1 = "SED-1"
MODULE_LIGP1 = "LIGP-1"
MODULE_CER1 = "CER-1"
MODULE_FAP1 = "FAP-1"
MODULE_FCRM1 = "FCRM-1"
MODULE_SSDE1 = "SSDE-1"
MODULE_ADM1 = "ADM-1"
MODULE_K4 = "K4"

# Legacy alias
MODULE_SEC1 = MODULE_SED1

CSS1_LAYERS: tuple[str, ...] = (
    MODULE_CE1,
    MODULE_SED1,
    MODULE_LIGP1,
    MODULE_CER1,
    MODULE_FAP1,
    MODULE_FCRM1,
    MODULE_SSDE1,
    MODULE_ADM1,
    MODULE_K4,
)

CSS1_MODULES = CSS1_LAYERS  # backward compatible

ContinuityStackPhase = Literal[
    "propagation",
    "convergence",
    "accumulation",
    "pre_stewardship_compounding",
    "steward_emergence",
    "stewardability",
    "full_continuity",
]

PHASE_3_5_LABEL = "Phase 3.5 — Pre-Stewardship Compounding"
PHASE_4_LABEL = "Phase 4 — Steward Emergence"

CONTINUITY_HEART = "Maximizing transmissible judgment — not maximizing knowledge, insight, or structure."

COMPOUNDING_DOMINANCE_FORMULA = "A(t) > P(t) + C(t)"
SED1_FORMULA = "SED = (PT_3 ∧ CT_2 ∧ MAT_3 ∧ G > 0)"
SEC1_FORMULA = SED1_FORMULA  # legacy alias
FAP1_FORMULA = "FA = (S > F) ∧ F_recognizes(S) ∧ F_integrates(S)"
SSDE1_FORMULA = "SS = (A3 ∨ A4) ∧ (E_gain > 0) ∧ (I_integration > F)"
FCRM1_FORMULA = "FCR = αR + βB + γD + δS"
ADM1_FORMULA = "AD = αI + βF + γO + δL + εC"

UNIFIED_CONTINUITY_CONDITION = (
    "PT_3 ∧ CT_2 ∧ MAT_3 ∧ SED_1 ∧ FA ∧ (FCR low) ∧ (AD low) "
    "∧ K1 ∧ K2 ∧ K3 ∧ K4"
)

# FCRM-1 weights
FCRM_ALPHA_REJECTION = 0.3
FCRM_BETA_BOTTLENECK = 0.25
FCRM_GAMMA_DOGMATISM = 0.25
FCRM_DELTA_SUPPRESSION = 0.2
FCRM_HIGH_RISK_THRESHOLD = 0.6

# ADM-1 weights
ADM_ALPHA_INFLATION = 0.25
ADM_BETA_FRAGMENTATION = 0.20
ADM_GAMMA_OSSIFICATION = 0.20
ADM_DELTA_OVERLOAD = 0.20
ADM_EPSILON_CAPTURE = 0.15
ADM_HIGH_THRESHOLD = 0.6

ADM1_REFERENCE = "Accumulation Drift Model ADM-1"
K4_REFERENCE = "K4 — Reconstructability Invariant"

ACCUMULATION_DRIFT_MODES: tuple[tuple[str, str], ...] = (
    ("inflation", "Accumulation Inflation — new concepts added faster than integrated."),
    ("fragmentation", "Accumulation Fragmentation — pile of insights, not a grammar."),
    ("ossification", "Accumulation Ossification — prior structure prevents innovation."),
    ("overload", "Accumulation Overload — future stewards cannot reconstruct the lineage."),
    ("capture", "Accumulation Capture — generation rewarded over integration."),
)

K4_REQUIREMENTS: tuple[str, ...] = (
    "Compression — lineage remains compressible.",
    "Clarity — primitives stay legible.",
    "Modularity — components recombine without collapse.",
    "Grammar-level coherence — shared structural alignment.",
    "Bounded complexity — chain depth within threshold.",
    "Survivable cognitive load — accumulation does not outpace transmission.",
)

FULL_CONTINUITY_REQUIREMENTS: tuple[str, ...] = (
    "Propagation (PT-3)",
    "Convergence (CT-2)",
    "Accumulation (MAT-3)",
    "Steward Emergence (SED-1)",
    "Founder Acceptance (FAP-1)",
    "Founder-Capture Avoidance (FCRM-1 low)",
    "Accumulation Drift Avoidance (ADM-1 low)",
    "Identity Invariants (K1–K3)",
    "Reconstructability (K4)",
    "Successor Surpassment (SSDE-1)",
    "Stewardability (successors can govern)",
)
