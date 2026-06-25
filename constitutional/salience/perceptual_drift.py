"""Perceptual Drift Detector — Q-PD failure classes (Article Q-6)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.ledger import SalienceLedger, load_salience_ledger

PERCEPTUAL_DRIFT_STATE_ID = "perceptual_drift__global"


class PerceptualDriftFailure(str, Enum):
    SALIENCE_DRIFT = "Q-PD1 SalienceDrift"
    SALIENCE_INVERSION = "Q-PD2 SalienceInversion"
    SALIENCE_COLLAPSE = "Q-PD3 SalienceCollapse"
    SALIENCE_OVERFITTING = "Q-PD4 SalienceOverfitting"
    SALIENCE_BLINDNESS = "Q-PD5 SalienceBlindness"


class StewardSalienceMap(BaseModel):
    primary_signals: list[str] = Field(default_factory=list)
    secondary_signals: list[str] = Field(default_factory=list)
    ignored_signals: list[str] = Field(default_factory=list)


class PerceptualDriftState(BaseModel):
    state_id: str = PERCEPTUAL_DRIFT_STATE_ID
    state_type: str = "perceptual_drift"
    snapshot_at: datetime
    version: int = Field(default=1, ge=1)
    drift_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: list[PerceptualDriftFailure] = Field(default_factory=list)
    drift_cases: list[str] = Field(default_factory=list)
    inversions: list[str] = Field(default_factory=list)
    collapses: list[str] = Field(default_factory=list)
    overfits: list[str] = Field(default_factory=list)
    blindspots: list[str] = Field(default_factory=list)


class PerceptualDriftDetector:
    """Detect when steward salience diverges from historical perceptual patterns."""

    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        salience_ledger: SalienceLedger | None = None,
        steward_salience_map: StewardSalienceMap | None = None,
    ) -> None:
        self.csr = csr
        self.salience_ledger = salience_ledger or load_salience_ledger(csr)
        self.steward_salience_map = steward_salience_map or StewardSalienceMap()

    def run(self, now: datetime | None = None) -> PerceptualDriftState:
        now = now or datetime.now(UTC).replace(microsecond=0)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        failed: list[PerceptualDriftFailure] = []
        drift_cases: list[str] = []
        inversions: list[str] = []
        collapses: list[str] = []
        overfits: list[str] = []
        blindspots: list[str] = []

        historical_primary = self._aggregate("primary_signals")
        historical_ignored = self._aggregate("ignored_signals")

        steward_primary = {signal.lower() for signal in self.steward_salience_map.primary_signals}

        for signal in steward_primary:
            if signal not in {item.lower() for item in historical_primary} and historical_primary:
                failed.append(PerceptualDriftFailure.SALIENCE_DRIFT)
                drift_cases.append(signal)

        for signal in steward_primary:
            if signal in {item.lower() for item in historical_ignored}:
                failed.append(PerceptualDriftFailure.SALIENCE_INVERSION)
                inversions.append(signal)

        if self._is_collapse(self.steward_salience_map):
            failed.append(PerceptualDriftFailure.SALIENCE_COLLAPSE)
            collapses.append("collapse_detected")

        if self._is_overfit(self.steward_salience_map, historical_primary):
            failed.append(PerceptualDriftFailure.SALIENCE_OVERFITTING)
            overfits.append("overfit_detected")

        for signal in historical_primary:
            if signal.lower() not in steward_primary:
                failed.append(PerceptualDriftFailure.SALIENCE_BLINDNESS)
                blindspots.append(signal)

        unique_failed = list(dict.fromkeys(failed))
        drift_index = 1.0 - (len(unique_failed) / len(PerceptualDriftFailure))

        prev = load_perceptual_drift_state(self.csr)
        version = (prev.version + 1) if prev else 1

        state = PerceptualDriftState(
            snapshot_at=now,
            version=version,
            drift_index=drift_index,
            failed_surfaces=unique_failed,
            drift_cases=drift_cases,
            inversions=inversions,
            collapses=collapses,
            overfits=overfits,
            blindspots=blindspots,
        )
        self._register_state(state)
        return state

    def _aggregate(self, field: str) -> set[str]:
        values: list[str] = []
        for entry in self.salience_ledger.entries:
            values.extend(getattr(entry, field))
        return set(values)

    def _is_collapse(self, salience_map: StewardSalienceMap) -> bool:
        return (
            len(salience_map.primary_signals) > 10
            or (
                len(salience_map.primary_signals) > 0
                and len(salience_map.primary_signals) == len(salience_map.secondary_signals)
            )
        )

    def _is_overfit(self, salience_map: StewardSalienceMap, historical_primary: set[str]) -> bool:
        if not historical_primary or len(historical_primary) < 3:
            return False
        steward_set = {signal.lower() for signal in salience_map.primary_signals}
        historical_set = {signal.lower() for signal in historical_primary}
        return steward_set == historical_set

    def _register_state(self, state: PerceptualDriftState) -> None:
        self.csr.register_or_replace_state(
            StateObject(
                state_id=PERCEPTUAL_DRIFT_STATE_ID,
                state_type="perceptual_drift",
                current_state="Observed" if state.drift_index >= 0.8 else "Proposed",
            )
        )
        self.csr.put_domain_doc(PERCEPTUAL_DRIFT_STATE_ID, "perceptual_drift", state)


def load_perceptual_drift_state(csr: ConstitutionalStateRuntime) -> PerceptualDriftState | None:
    try:
        doc = csr.get_domain_doc(PERCEPTUAL_DRIFT_STATE_ID, PerceptualDriftState)
        assert isinstance(doc, PerceptualDriftState)
        return doc
    except KeyError:
        return None
