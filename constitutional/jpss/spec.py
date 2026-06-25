"""JPSS-1 normative constants — Judgment Preservation & Stewardship Science v1.0."""

from __future__ import annotations

from typing import Literal

JPSS_VERSION = "1.0"
JPSS_REFERENCE = "JPSS-1 — Judgment Preservation & Stewardship Science"

JPSSStage = Literal[
    "environment",
    "perception",
    "salience",
    "calibration",
    "decision",
    "outcome",
    "reflection",
    "calibration_update",
]

JPSS_CANONICAL_CYCLE: tuple[JPSSStage, ...] = (
    "environment",
    "perception",
    "salience",
    "calibration",
    "decision",
    "outcome",
    "reflection",
    "calibration_update",
)

JPSSInvariant = Literal[
    "environment_invariant",
    "salience_invariant",
    "calibration_invariant",
    "reflection_invariant",
    "continuity_invariant",
]

JPSS_INVARIANTS: tuple[JPSSInvariant, ...] = (
    "environment_invariant",
    "salience_invariant",
    "calibration_invariant",
    "reflection_invariant",
    "continuity_invariant",
)

JPSS_INVARIANT_DESCRIPTIONS: dict[JPSSInvariant, str] = {
    "environment_invariant": "Judgment must be interpreted relative to the environment in which it was formed.",
    "salience_invariant": "Attention allocation is a first-class causal variable in judgment formation.",
    "calibration_invariant": "Thresholds and evidence weights must be reconstructable.",
    "reflection_invariant": "Judgment evolves through outcome-driven updates.",
    "continuity_invariant": "A future steward must reconstruct the cycle from preserved artifacts.",
}

JPSSDriftClass = Literal[
    "environmental_drift",
    "perceptual_drift",
    "salience_drift",
    "calibration_drift",
    "decision_drift",
    "outcome_drift",
    "reflection_drift",
    "failure_drift",
]

JPSS_DRIFT_CLASSES: tuple[JPSSDriftClass, ...] = (
    "environmental_drift",
    "perceptual_drift",
    "salience_drift",
    "calibration_drift",
    "decision_drift",
    "outcome_drift",
    "reflection_drift",
    "failure_drift",
)

JPSS_REGISTER_NAMES: tuple[str, ...] = (
    "environment",
    "perception",
    "salience",
    "calibration",
    "decision",
    "outcome",
    "reflection",
    "failure",
)

ECK2_REFERENCE = "ECK-2 — Unified Epistemic Kernel (formation + reconstruction)"
ECK2_MIN_DRIFT_SYMMETRY_INDEX = 0.80
