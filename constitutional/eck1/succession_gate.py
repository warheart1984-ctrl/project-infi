"""ECK-1 Succession Gate — §7 normative thresholds."""

from __future__ import annotations

from constitutional.core.articles import (
    ECK1_MIN_CALIBRATION_INDEX,
    ECK1_MIN_ENVIRONMENT_HEALTH,
    ECK1_MIN_FAILURE_CONTINUITY,
    ECK1_MIN_PERCEPTUAL_DRIFT_INDEX,
    ECK1_MIN_PRIOR_DRIFT_INDEX,
    ECK1_MIN_SALIENCE_INDEX,
    ECK1_MIN_SIGNIFICANCE_CONTINUITY,
)
from constitutional.eck1.calibration_continuity_runtime import (
    CalibrationContinuityRuntime,
    load_calibration_continuity_state,
)
from constitutional.eck1.continuity_suite import ECK1ContinuitySuite
from constitutional.eck1.failure_history_runtime import FailureHistoryRuntime, load_failure_history_state
from constitutional.priors.drift_detector import PriorDriftDetector, load_prior_drift_state
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.continuity_runtime import SalienceContinuityRuntime, load_salience_continuity_state
from constitutional.salience.perceptual_drift import PerceptualDriftDetector, load_perceptual_drift_state
from constitutional.significance.decision_environment_runtime import (
    DecisionEnvironmentRuntime,
    load_decision_environment_state,
)
from constitutional.significance.significance_governance import succession_significance_judgment_ready
from constitutional.significance.significance_review_runtime import (
    SignificanceReviewRuntime,
    load_significance_review_state,
)


def check_eck1_succession_gate(csr: ConstitutionalStateRuntime) -> tuple[bool, str]:
    """A steward may inherit authority only if all ECK-1 indices pass (§7)."""
    prior = load_prior_drift_state(csr) or PriorDriftDetector(csr).run()
    if prior.drift_index < ECK1_MIN_PRIOR_DRIFT_INDEX:
        return False, f"Succession blocked: Prior Drift Index {prior.drift_index:.2f} < {ECK1_MIN_PRIOR_DRIFT_INDEX:.2f}"

    salience = load_salience_continuity_state(csr) or SalienceContinuityRuntime(csr).run()
    if salience.salience_index < ECK1_MIN_SALIENCE_INDEX:
        return False, f"Succession blocked: Salience Index {salience.salience_index:.2f} < {ECK1_MIN_SALIENCE_INDEX:.2f}"

    perceptual = load_perceptual_drift_state(csr) or PerceptualDriftDetector(csr).run()
    if perceptual.drift_index < ECK1_MIN_PERCEPTUAL_DRIFT_INDEX:
        return False, (
            f"Succession blocked: Perceptual Drift Index {perceptual.drift_index:.2f} "
            f"< {ECK1_MIN_PERCEPTUAL_DRIFT_INDEX:.2f}"
        )

    try:
        environment = load_decision_environment_state(csr)
    except KeyError:
        environment = DecisionEnvironmentRuntime(csr).run()
    if environment.environment_health_index < ECK1_MIN_ENVIRONMENT_HEALTH:
        return False, (
            f"Succession blocked: Environment Health Index {environment.environment_health_index:.2f} "
            f"< {ECK1_MIN_ENVIRONMENT_HEALTH:.2f}"
        )

    calibration = load_calibration_continuity_state(csr) or CalibrationContinuityRuntime(csr).run()
    if calibration.calibration_index < ECK1_MIN_CALIBRATION_INDEX:
        return False, (
            f"Succession blocked: Calibration Index {calibration.calibration_index:.2f} "
            f"< {ECK1_MIN_CALIBRATION_INDEX:.2f}"
        )

    judgment_ok, judgment_reasons = succession_significance_judgment_ready(csr)
    if not judgment_ok:
        return False, f"Succession blocked: Judgment Test FAIL ({'; '.join(judgment_reasons)})"

    try:
        sig_review = load_significance_review_state(csr)
    except KeyError:
        sig_review = SignificanceReviewRuntime(csr).run_review()
    if sig_review.continuity_index < ECK1_MIN_SIGNIFICANCE_CONTINUITY:
        return False, (
            f"Succession blocked: Significance Continuity Index {sig_review.continuity_index:.2f} "
            f"< {ECK1_MIN_SIGNIFICANCE_CONTINUITY:.2f}"
        )

    failure = load_failure_history_state(csr) or FailureHistoryRuntime(csr).run()
    if failure.failure_continuity_index < ECK1_MIN_FAILURE_CONTINUITY:
        return False, (
            f"Succession blocked: Failure Continuity Index {failure.failure_continuity_index:.2f} "
            f"< {ECK1_MIN_FAILURE_CONTINUITY:.2f}"
        )

    return True, "ECK-1 succession gate satisfied."


def run_eck1_succession_evaluation(csr: ConstitutionalStateRuntime) -> tuple[bool, str, ECK1ContinuitySuite]:
    """Run full continuity suite then gate."""
    suite = ECK1ContinuitySuite(csr)
    suite.run()
    ready, message = check_eck1_succession_gate(csr)
    return ready, message, suite
