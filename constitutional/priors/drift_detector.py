"""Prior Drift Detector — Q-PF failure classes."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.priors.ledger import StewardshipPriorLedger, load_prior_ledger
from constitutional.runtime.runtime import ConstitutionalStateRuntime

PRIOR_DRIFT_STATE_ID = "prior_drift__global"
PRIOR_DRIFT_MIN_INDEX = 0.8


class PriorDriftFailure(str, Enum):
    PRIOR_DRIFT = "Q-PF1 PriorDrift"
    PRIOR_INVERSION = "Q-PF2 PriorInversion"
    PRIOR_COLLAPSE = "Q-PF3 PriorCollapse"
    PRIOR_OVERFITTING = "Q-PF4 PriorOverfitting"
    PRIOR_BLINDNESS = "Q-PF5 PriorBlindness"


class StewardPriorMap(BaseModel):
    expected_signals: list[str] = Field(default_factory=list)
    expected_risks: list[str] = Field(default_factory=list)
    assumed_stabilities: list[str] = Field(default_factory=list)
    assumed_volatilities: list[str] = Field(default_factory=list)
    feared_failures: list[str] = Field(default_factory=list)
    ignored_possibilities: list[str] = Field(default_factory=list)


class PriorDriftState(BaseModel):
    state_id: str = PRIOR_DRIFT_STATE_ID
    state_type: str = "prior_drift"
    snapshot_at: datetime
    version: int = Field(default=1, ge=1)
    drift_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: list[PriorDriftFailure] = Field(default_factory=list)
    drift_cases: list[str] = Field(default_factory=list)
    inversions: list[str] = Field(default_factory=list)
    collapses: list[str] = Field(default_factory=list)
    overfits: list[str] = Field(default_factory=list)
    blindspots: list[str] = Field(default_factory=list)


class PriorDriftDetector:
    """Detect when steward priors diverge from historical expectation patterns."""

    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        prior_ledger: StewardshipPriorLedger | None = None,
        steward_priors: StewardPriorMap | None = None,
    ) -> None:
        self.csr = csr
        self.prior_ledger = prior_ledger or load_prior_ledger(csr)
        self.steward_priors = steward_priors or StewardPriorMap()

    def run(self, now: datetime | None = None) -> PriorDriftState:
        now = now or datetime.now(UTC).replace(microsecond=0)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        failed: list[PriorDriftFailure] = []
        drift: list[str] = []
        inversions: list[str] = []
        collapses: list[str] = []
        overfits: list[str] = []
        blindspots: list[str] = []

        historical_expected = self._aggregate("expected_signals")
        historical_volatile = self._aggregate("assumed_volatilities")

        steward_expected = {signal.lower() for signal in self.steward_priors.expected_signals}

        for signal in steward_expected:
            if signal not in {item.lower() for item in historical_expected} and historical_expected:
                failed.append(PriorDriftFailure.PRIOR_DRIFT)
                drift.append(signal)

        for stability in self.steward_priors.assumed_stabilities:
            if stability.lower() in {item.lower() for item in historical_volatile}:
                failed.append(PriorDriftFailure.PRIOR_INVERSION)
                inversions.append(stability)

        if self._is_collapse(self.steward_priors):
            failed.append(PriorDriftFailure.PRIOR_COLLAPSE)
            collapses.append("collapse_detected")

        if self._is_overfit(self.steward_priors, historical_expected):
            failed.append(PriorDriftFailure.PRIOR_OVERFITTING)
            overfits.append("overfit_detected")

        for signal in historical_expected:
            if signal.lower() not in steward_expected:
                failed.append(PriorDriftFailure.PRIOR_BLINDNESS)
                blindspots.append(signal)

        from constitutional.eck1.registers import load_failure_register
        from constitutional.failure.bridge import historical_failure_classes_for_layer

        register = load_failure_register(self.csr)
        steward_feared = {item.lower() for item in self.steward_priors.feared_failures}
        for failure_class in historical_failure_classes_for_layer(register, "prior"):
            if failure_class.lower() not in steward_feared:
                failed.append(PriorDriftFailure.PRIOR_BLINDNESS)
                blindspots.append(failure_class)

        unique_failed = list(dict.fromkeys(failed))
        drift_index = 1.0 - (len(unique_failed) / len(PriorDriftFailure))

        prev = load_prior_drift_state(self.csr)
        version = (prev.version + 1) if prev else 1

        state = PriorDriftState(
            snapshot_at=now,
            version=version,
            drift_index=drift_index,
            failed_surfaces=unique_failed,
            drift_cases=drift,
            inversions=inversions,
            collapses=collapses,
            overfits=overfits,
            blindspots=blindspots,
        )
        self._register_state(state)
        return state

    def _aggregate(self, field: str) -> set[str]:
        values: list[str] = []
        for entry in self.prior_ledger.entries:
            values.extend(getattr(entry, field))
        return set(values)

    def _is_collapse(self, priors: StewardPriorMap) -> bool:
        return len(priors.expected_signals) > 10 or (
            len(priors.expected_signals) > 0
            and len(priors.expected_signals) == len(priors.ignored_possibilities)
        )

    def _is_overfit(self, priors: StewardPriorMap, historical_expected: set[str]) -> bool:
        if not historical_expected or len(historical_expected) < 3:
            return False
        steward_set = {signal.lower() for signal in priors.expected_signals}
        historical_set = {signal.lower() for signal in historical_expected}
        return steward_set == historical_set

    def _register_state(self, state: PriorDriftState) -> None:
        self.csr.register_or_replace_state(
            StateObject(
                state_id=PRIOR_DRIFT_STATE_ID,
                state_type="prior_drift",
                current_state="Observed" if state.drift_index >= PRIOR_DRIFT_MIN_INDEX else "Proposed",
            )
        )
        self.csr.put_domain_doc(PRIOR_DRIFT_STATE_ID, "prior_drift", state)


def load_prior_drift_state(csr: ConstitutionalStateRuntime) -> PriorDriftState | None:
    try:
        doc = csr.get_domain_doc(PRIOR_DRIFT_STATE_ID, PriorDriftState)
        assert isinstance(doc, PriorDriftState)
        return doc
    except KeyError:
        return None
