"""Prior succession gates — prior continuity readiness."""

from __future__ import annotations

from constitutional.core.articles import SUCCESSION_MIN_PRIOR_DRIFT_INDEX
from constitutional.environment.governance import succession_decision_environment_ready
from constitutional.priors.drift_detector import PriorDriftDetector, load_prior_drift_state
from constitutional.priors.judgment_runtime import (
    PriorJudgmentTest,
    StewardPriorAnswer,
    load_prior_judgment_state,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.governance import salience_aware_succession_gate


def succession_prior_judgment_ready(
    csr: ConstitutionalStateRuntime | None = None,
    *,
    steward_answers: dict[str, StewardPriorAnswer] | None = None,
) -> tuple[bool, list[str]]:
    if csr is None and steward_answers is None:
        return False, ["prior_judgment_not_evaluated"]

    if steward_answers is not None:
        result = PriorJudgmentTest().evaluate(steward_answers)
        if not result.passed:
            return False, [f"prior_judgment_failed_score_{result.score:.2f}"]
        return True, []

    state = load_prior_judgment_state(csr)  # type: ignore[arg-type]
    if state is None or state.last_result is None:
        return False, ["prior_judgment_not_completed"]
    if not state.passed:
        return False, [f"prior_judgment_failed_score_{state.last_result.score:.2f}"]
    return True, []


def succession_prior_continuity_ready(
    csr: ConstitutionalStateRuntime,
    *,
    min_index: float | None = None,
) -> tuple[bool, list[str]]:
    threshold = min_index if min_index is not None else SUCCESSION_MIN_PRIOR_DRIFT_INDEX
    state = load_prior_drift_state(csr)
    if state is None:
        state = PriorDriftDetector(csr).run()
    if state.drift_index < threshold:
        return False, [f"prior_drift_index_{state.drift_index:.2f}_below_{threshold:.2f}"]
    if state.failed_surfaces:
        codes = [failure.value for failure in state.failed_surfaces]
        return False, [f"prior_drift_failures_{','.join(codes)}"]
    return True, []


def prior_aware_succession_gate(csr: ConstitutionalStateRuntime) -> tuple[bool, str]:
    """Prior judgment + drift + environment + salience stack gate for succession."""
    judgment_ok, judgment_reasons = succession_prior_judgment_ready(csr)
    if not judgment_ok:
        return False, f"Succession blocked: Prior Judgment failure ({'; '.join(judgment_reasons)})"

    prior_ok, prior_reasons = succession_prior_continuity_ready(csr)
    if not prior_ok:
        return False, f"Succession blocked: Prior Drift ({'; '.join(prior_reasons)})"

    env_ok, env_reasons = succession_decision_environment_ready(csr)
    if not env_ok:
        return False, f"Succession blocked: Decision Environment ({'; '.join(env_reasons)})"

    salience_ok, salience_message = salience_aware_succession_gate(csr)
    if not salience_ok:
        return False, salience_message

    return True, "Succession readiness satisfied with full prior-aware perceptual competence."
