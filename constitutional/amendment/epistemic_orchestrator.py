"""Cross-layer epistemic remediation — Q-PF + Q-PD + Q-SC co-occurrence."""

from __future__ import annotations

from typing import Any

from constitutional.core.articles import (
    ARTICLE_P_REFERENCE,
    ARTICLE_Q3_REFERENCE,
    ARTICLE_Q5_REFERENCE,
    ARTICLE_Q6_REFERENCE,
    ARTICLE_Q7_REFERENCE,
)
from constitutional.failure.bridge import record_epistemic_failures
from constitutional.priors.amendment import generate_prior_amendment
from constitutional.priors.drift_detector import PriorDriftDetector, load_prior_drift_state
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.amendment import generate_salience_amendment
from constitutional.salience.continuity_runtime import (
    SalienceContinuityRuntime,
    load_salience_continuity_state,
)
from constitutional.salience.perceptual_drift import PerceptualDriftDetector, load_perceptual_drift_state

EPISTEMIC_AMENDMENT_TEMPLATE_ID = "UGR-AMENDMENT-Q-EPISTEMIC-STACK-v0"


def _load_or_run_states(csr: ConstitutionalStateRuntime):
    salience_cont = load_salience_continuity_state(csr)
    if salience_cont is None:
        salience_cont = SalienceContinuityRuntime(csr).run()
    perceptual = load_perceptual_drift_state(csr)
    if perceptual is None:
        perceptual = PerceptualDriftDetector(csr).run()
    prior = load_prior_drift_state(csr)
    if prior is None:
        prior = PriorDriftDetector(csr).run()
    return prior, perceptual, salience_cont


def epistemic_failures_co_occur(
    prior_drift_state,
    perceptual_drift_state,
    salience_continuity_state,
) -> bool:
    return bool(
        prior_drift_state.failed_surfaces
        and perceptual_drift_state.failed_surfaces
        and salience_continuity_state.failed_surfaces
    )


def generate_epistemic_remediation_amendment(
    csr: ConstitutionalStateRuntime,
    *,
    record_failures: bool = True,
) -> dict[str, Any] | None:
    """Single remediation artifact when prior, perceptual, and salience continuity all fail."""
    prior, perceptual, salience_cont = _load_or_run_states(csr)
    if not epistemic_failures_co_occur(prior, perceptual, salience_cont):
        return None

    if record_failures:
        record_epistemic_failures(
            csr,
            prior_drift_state=prior,
            perceptual_drift_state=perceptual,
            salience_continuity_state=salience_cont,
        )

    salience_amendment = generate_salience_amendment(salience_cont, perceptual)
    prior_amendment = generate_prior_amendment(prior)

    return {
        "template_id": EPISTEMIC_AMENDMENT_TEMPLATE_ID,
        "amendment_type": "EPISTEMIC STACK REMEDIATION",
        "problem_statement": [
            "Co-occurring prior drift (Q-PF), perceptual drift (Q-PD), and salience continuity (Q-SC) failures.",
            *salience_amendment.get("problem_statement", []),
            *prior_amendment.get("problem_statement", []),
        ],
        "evidence": {
            "prior_drift": prior.model_dump(mode="json"),
            "perceptual_drift": perceptual.model_dump(mode="json"),
            "salience_continuity": salience_cont.model_dump(mode="json"),
        },
        "required_actions": list(
            dict.fromkeys(
                salience_amendment.get("required_actions", [])
                + prior_amendment.get("required_actions", [])
                + [
                    "Run full epistemic stack review: priors → salience → environment → significance.",
                    "Record failure lineage in ECK-1 failure register before closing amendment.",
                ]
            )
        ),
        "success_criteria": [
            "Prior Drift Index ≥ 0.80 with no Q-PF hard failures",
            "Perceptual Drift Index ≥ 0.80 with no Q-PD hard failures",
            "Salience Index ≥ 0.80 with no Q-SC failures",
            "Steward passes Prior and Salience Judgment Tests",
        ],
        "constitutional_linkage": [
            ARTICLE_Q7_REFERENCE,
            ARTICLE_Q6_REFERENCE,
            ARTICLE_Q5_REFERENCE,
            ARTICLE_Q3_REFERENCE,
            ARTICLE_P_REFERENCE,
        ],
        "telic_statement": (
            "Legitimate succession requires aligned priors, perception, and salience — "
            "not merely preserved decisions."
        ),
    }
