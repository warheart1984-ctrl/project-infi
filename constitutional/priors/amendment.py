"""Prior-driven amendment generator — prior drift remediation."""

from __future__ import annotations

from typing import Any

from constitutional.core.articles import (
    ARTICLE_P_REFERENCE,
    ARTICLE_Q3_REFERENCE,
    ARTICLE_Q5_REFERENCE,
    ARTICLE_Q7_REFERENCE,
)
from constitutional.priors.drift_detector import PriorDriftState

PRIOR_AMENDMENT_TEMPLATE_ID = "UGR-AMENDMENT-Q-PRIOR-v0"


def generate_prior_amendment(prior_drift_state: PriorDriftState | None) -> dict[str, Any]:
    amendment: dict[str, Any] = {
        "template_id": PRIOR_AMENDMENT_TEMPLATE_ID,
        "amendment_type": "PRIOR CONTINUITY REMEDIATION",
        "problem_statement": [],
        "evidence": {},
        "required_actions": [],
        "success_criteria": [
            "Prior Drift Index ≥ 0.80",
            "No Q-PF failures in red zone",
            "Steward passes Prior Judgment Test v1",
        ],
        "constitutional_linkage": [
            ARTICLE_Q7_REFERENCE,
            ARTICLE_Q5_REFERENCE,
            ARTICLE_Q3_REFERENCE,
            ARTICLE_P_REFERENCE,
        ],
        "telic_statement": (
            "A system preserves judgment only when it preserves the expectations, fears, "
            "and assumed stabilities that shaped how stewards saw the world."
        ),
    }

    if prior_drift_state and prior_drift_state.failed_surfaces:
        amendment["problem_statement"].append(
            f"Prior Drift Failures: {[f.value for f in prior_drift_state.failed_surfaces]}"
        )
        amendment["evidence"]["drift_cases"] = prior_drift_state.drift_cases
        amendment["evidence"]["inversions"] = prior_drift_state.inversions
        amendment["evidence"]["blindspots"] = prior_drift_state.blindspots
        amendment["evidence"]["collapses"] = prior_drift_state.collapses

    if prior_drift_state and prior_drift_state.blindspots:
        amendment["required_actions"].append(
            "Reconstruct missing expected signals in stewardship prior ledger."
        )
    if prior_drift_state and prior_drift_state.inversions:
        amendment["required_actions"].append(
            "Document justified stability/volatility inversions with environmental evidence."
        )
    if prior_drift_state and prior_drift_state.drift_cases:
        amendment["required_actions"].append(
            "Ground novel steward expectations in historical prior ledger entries."
        )

    return amendment
