"""JPSS-I integrated formal specification — adaptive + invariant + stewardship."""

from __future__ import annotations

from typing import Literal

JPSS_I_VERSION = "1.0"
JPSS_I_REFERENCE = "JPSS-I — Integrated Judgment Preservation & Stewardship Science"

# Three-layer judgment model (JPSS-I core); see constitutional.legitimacy for full four-layer stack
JPSSLayer = Literal["adaptive", "invariant", "stewardship"]

JPSS_I_LAYERS: tuple[JPSSLayer, ...] = ("adaptive", "invariant", "stewardship")

# Adaptive layer — canonical cycle (JPSS-1)
JPSS_I_ADAPTIVE_CYCLE: tuple[str, ...] = (
    "environment",
    "perception",
    "salience",
    "calibration",
    "decision",
    "outcome",
    "reflection",
    "calibration_update",
)

# Invariant layer — identity chain (does not update through reflection)
JPSS_I_INVARIANT_CHAIN: tuple[str, ...] = (
    "purpose",
    "core_values",
    "constitutional_commitments",
    "identity",
    "sacred_constraints",
)

# Adaptive invariants (plasticity must remain governed)
JPSS_I_ADAPTIVE_INVARIANTS: tuple[str, ...] = (
    "salience_must_be_explicit",
    "calibration_must_be_reconstructable",
    "reflection_must_update_calibration",
    "failure_must_inform_future_thresholds",
)

# Invariant invariants (identity must remain stable)
JPSS_I_INVARIANT_INVARIANTS: tuple[str, ...] = (
    "purpose_must_not_drift",
    "core_values_must_remain_stable",
    "constitutional_commitments_must_remain_binding",
    "identity_must_remain_recognizable",
    "sacred_constraints_must_remain_unbroken",
)

# Stewardship invariants (balance between layers)
JPSS_I_STEWARDSHIP_INVARIANTS: tuple[str, ...] = (
    "adaptive_updates_must_not_violate_invariant_anchors",
    "invariant_anchors_must_not_block_necessary_adaptation",
    "drift_must_be_detectable_in_both_layers",
    "succession_must_test_both_layers",
)

# Canonical register families
JPSS_I_ADAPTIVE_REGISTERS: tuple[str, ...] = (
    "environment",
    "perception",
    "salience",
    "calibration",
    "decision",
    "outcome",
    "reflection",
    "failure",
    "prior",
)

JPSS_I_INVARIANT_REGISTERS: tuple[str, ...] = (
    "purpose",
    "core_values",
    "constitutional_commitments",
    "identity",
    "sacred_constraints",
)

# Drift classes
JPSS_I_ADAPTIVE_DRIFT_CLASSES: tuple[str, ...] = (
    "environmental_drift",
    "perceptual_drift",
    "salience_drift",
    "calibration_drift",
    "decision_drift",
    "outcome_drift",
    "reflection_drift",
    "prior_drift",
)

JPSS_I_INVARIANT_DRIFT_CLASSES: tuple[str, ...] = (
    "purpose_erosion",
    "value_reinterpretation",
    "commitment_weakening",
    "identity_drift",
    "sacred_constraint_bypass",
)

# Succession competence requirements
JPSS_I_SUCCESSION_REQUIREMENTS: tuple[str, ...] = (
    "run_adaptive_cycle",
    "run_reconstruction_cycle",
    "preserve_invariant_anchors",
    "detect_drift_in_both_layers",
    "balance_adaptation_and_identity",
)

ECK2_MIN_INVARIANT_DRIFT_INDEX = 0.80

__all__ = [
    "ECK2_MIN_INVARIANT_DRIFT_INDEX",
    "JPSSLayer",
    "JPSS_I_ADAPTIVE_CYCLE",
    "JPSS_I_ADAPTIVE_DRIFT_CLASSES",
    "JPSS_I_ADAPTIVE_INVARIANTS",
    "JPSS_I_ADAPTIVE_REGISTERS",
    "JPSS_I_INVARIANT_CHAIN",
    "JPSS_I_INVARIANT_DRIFT_CLASSES",
    "JPSS_I_INVARIANT_INVARIANTS",
    "JPSS_I_INVARIANT_REGISTERS",
    "JPSS_I_LAYERS",
    "JPSS_I_REFERENCE",
    "JPSS_I_STEWARDSHIP_INVARIANTS",
    "JPSS_I_SUCCESSION_REQUIREMENTS",
    "JPSS_I_VERSION",
]
