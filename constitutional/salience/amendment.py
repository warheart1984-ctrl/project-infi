"""Salience-driven amendment generator — perceptual drift remediation."""

from __future__ import annotations

from typing import Any

from constitutional.core.articles import (
    ARTICLE_P_REFERENCE,
    ARTICLE_Q3_REFERENCE,
    ARTICLE_Q5_REFERENCE,
    ARTICLE_Q6_REFERENCE,
)
from constitutional.salience.continuity_runtime import SalienceContinuityState
from constitutional.salience.perceptual_drift import PerceptualDriftState


def generate_salience_amendment(
    salience_cont_state: SalienceContinuityState | None,
    perceptual_drift_state: PerceptualDriftState | None,
) -> dict[str, Any]:
    amendment: dict[str, Any] = {
        "amendment_type": "SALIENCE CONTINUITY REMEDIATION",
        "problem_statement": [],
        "evidence": {},
        "required_actions": [],
        "success_criteria": [
            "Salience Index ≥ 0.85",
            "No Q-SC failures in red zone",
            "No perceptual drift failures",
            "Steward can pass Salience Judgment Test v1",
        ],
        "constitutional_linkage": [
            ARTICLE_Q6_REFERENCE,
            ARTICLE_Q5_REFERENCE,
            ARTICLE_Q3_REFERENCE,
            ARTICLE_P_REFERENCE,
        ],
        "telic_statement": (
            "A system is constitutionally legitimate only when it preserves not "
            "just what was decided, but what was noticed, foregrounded, and "
            "considered meaningful in the act of judgment."
        ),
    }

    if salience_cont_state and salience_cont_state.failed_surfaces:
        amendment["problem_statement"].append(
            f"Salience Continuity Failures: {[f.value for f in salience_cont_state.failed_surfaces]}"
        )
    if perceptual_drift_state and perceptual_drift_state.failed_surfaces:
        amendment["problem_statement"].append(
            f"Perceptual Drift Failures: {[f.value for f in perceptual_drift_state.failed_surfaces]}"
        )

    if salience_cont_state:
        amendment["evidence"]["missing_salience_entries"] = salience_cont_state.missing_salience_entries
    if perceptual_drift_state:
        amendment["evidence"]["drift_cases"] = perceptual_drift_state.drift_cases
        amendment["evidence"]["inversions"] = perceptual_drift_state.inversions
        amendment["evidence"]["blindspots"] = perceptual_drift_state.blindspots

    if salience_cont_state and salience_cont_state.missing_salience_entries:
        amendment["required_actions"].append(
            "Reconstruct missing salience entries for Tier 0/1 artifacts."
        )
    if perceptual_drift_state and perceptual_drift_state.drift_cases:
        amendment["required_actions"].append(
            "Re-evaluate steward salience maps and produce corrected salience receipts."
        )
    if perceptual_drift_state and perceptual_drift_state.inversions:
        amendment["required_actions"].append(
            "Investigate salience inversions and determine justified evolution vs drift."
        )
    if perceptual_drift_state and perceptual_drift_state.blindspots:
        amendment["required_actions"].append(
            "Update steward training to address salience blindspots."
        )

    return amendment
