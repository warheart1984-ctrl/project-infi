"""ECK-1 Continuity Suite — all seven continuity runtimes."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.eck1.calibration_continuity_runtime import CalibrationContinuityRuntime
from constitutional.eck1.failure_history_runtime import FailureHistoryRuntime
from constitutional.eck1.models import ContinuityState
from constitutional.priors.drift_detector import PriorDriftDetector
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.continuity_runtime import SalienceContinuityRuntime
from constitutional.salience.perceptual_drift import PerceptualDriftDetector
from constitutional.significance.decision_environment_runtime import DecisionEnvironmentRuntime
from constitutional.significance.significance_judgment_runtime import SignificanceJudgmentRuntime
from constitutional.significance.significance_review_runtime import SignificanceReviewRuntime


class ECK1ContinuitySuiteResult(BaseModel):
    snapshot_at: datetime
    continuity: ContinuityState
    all_pass: bool
    failures: list[str] = Field(default_factory=list)


class ECK1ContinuitySuite:
    """Run all ECK-1 continuity requirements (§6)."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def run(self, now: datetime | None = None) -> ECK1ContinuitySuiteResult:
        now = now or datetime.now(UTC).replace(microsecond=0)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        prior = PriorDriftDetector(self.csr).run(now)
        salience = SalienceContinuityRuntime(self.csr).run(now)
        perceptual = PerceptualDriftDetector(self.csr).run(now)
        environment = DecisionEnvironmentRuntime(self.csr).run(snapshot_at=now)
        calibration = CalibrationContinuityRuntime(self.csr).run(now)
        significance_review = SignificanceReviewRuntime(self.csr).run_review(snapshot_at=now)
        failure_history = FailureHistoryRuntime(self.csr).run(now)

        from constitutional.significance.significance_judgment_runtime import load_significance_judgment_state

        judgment_state = load_significance_judgment_state(self.csr)
        if judgment_state and judgment_state.last_result:
            judgment_passed = judgment_state.last_result.passed
        else:
            judgment_passed = True

        continuity = ContinuityState(
            prior_drift_index=prior.drift_index,
            salience_index=salience.salience_index,
            perceptual_drift_index=perceptual.drift_index,
            environment_health_index=environment.environment_health_index,
            calibration_index=calibration.calibration_index,
            significance_continuity_index=significance_review.continuity_index,
            failure_continuity_index=failure_history.failure_continuity_index,
            judgment_passed=judgment_passed,
            captured_at=now,
        )

        failures: list[str] = []
        if prior.failed_surfaces:
            failures.extend(f.value for f in prior.failed_surfaces)
        if salience.failed_surfaces:
            failures.extend(f.value for f in salience.failed_surfaces)
        if perceptual.failed_surfaces:
            failures.extend(f.value for f in perceptual.failed_surfaces)
        if environment.failed_surfaces:
            failures.extend(f.value for f in environment.failed_surfaces)
        if calibration.failed_surfaces:
            failures.extend(f.value for f in calibration.failed_surfaces)
        if not judgment_passed:
            failures.append("judgment_test_failed")

        all_pass = not failures

        return ECK1ContinuitySuiteResult(
            snapshot_at=now,
            continuity=continuity,
            all_pass=all_pass,
            failures=failures,
        )
