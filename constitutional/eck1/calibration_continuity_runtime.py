"""Calibration Continuity Runtime — ECK-1 §6."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.eck1.registers import CalibrationRegister, load_calibration_register
from constitutional.runtime.runtime import ConstitutionalStateRuntime

CALIBRATION_CONTINUITY_STATE_ID = "calibration_continuity__global"
CALIBRATION_CONTINUITY_MIN_INDEX = 0.8


class CalibrationFailure(str, Enum):
    THRESHOLD_DRIFT = "ECK-C1 ThresholdDrift"
    EVIDENCE_MISMATCH = "ECK-C2 EvidenceMismatch"
    RISK_MISALIGNMENT = "ECK-C3 RiskMisalignment"
    MISSING_CALIBRATION = "ECK-C4 MissingCalibration"


class CalibrationContinuityState(BaseModel):
    state_id: str = CALIBRATION_CONTINUITY_STATE_ID
    state_type: str = "calibration_continuity"
    snapshot_at: datetime
    version: int = Field(default=1, ge=1)
    calibration_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: list[CalibrationFailure] = Field(default_factory=list)
    missing_entries: list[str] = Field(default_factory=list)
    drift_cases: list[str] = Field(default_factory=list)


class CalibrationContinuityRuntime:
    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        calibration_register: CalibrationRegister | None = None,
    ) -> None:
        self.csr = csr
        self.calibration_register = calibration_register or load_calibration_register(csr)

    def run(self, now: datetime | None = None) -> CalibrationContinuityState:
        now = now or datetime.now(UTC).replace(microsecond=0)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        failed: list[CalibrationFailure] = []
        missing: list[str] = []
        drift: list[str] = []

        if not self.calibration_register.entries:
            failed.append(CalibrationFailure.MISSING_CALIBRATION)
            missing.append("no_calibration_entries")

        thresholds = [e.evidence_threshold for e in self.calibration_register.entries]
        if thresholds and (max(thresholds) - min(thresholds)) > 0.4:
            failed.append(CalibrationFailure.THRESHOLD_DRIFT)
            drift.append("threshold_spread")

        for entry in self.calibration_register.entries:
            if entry.evidence_missing and not entry.evidence_available:
                failed.append(CalibrationFailure.EVIDENCE_MISMATCH)
                drift.append(entry.decision_id)
            if entry.risk_tolerance < 0.2 and entry.evidence_missing:
                failed.append(CalibrationFailure.RISK_MISALIGNMENT)
                drift.append(f"risk_{entry.decision_id}")

        unique_failed = list(dict.fromkeys(failed))
        calibration_index = 1.0 - (len(unique_failed) / len(CalibrationFailure))

        try:
            prev = load_calibration_continuity_state(self.csr)
            version = (prev.version + 1) if prev else 1
        except KeyError:
            version = 1

        state = CalibrationContinuityState(
            snapshot_at=now,
            version=version,
            calibration_index=calibration_index,
            failed_surfaces=unique_failed,
            missing_entries=missing,
            drift_cases=drift,
        )
        self._register_state(state)
        return state

    def _register_state(self, state: CalibrationContinuityState) -> None:
        self.csr.register_or_replace_state(
            StateObject(
                state_id=CALIBRATION_CONTINUITY_STATE_ID,
                state_type="calibration_continuity",
                current_state="Observed" if state.calibration_index >= CALIBRATION_CONTINUITY_MIN_INDEX else "Proposed",
            )
        )
        self.csr.put_domain_doc(CALIBRATION_CONTINUITY_STATE_ID, "calibration_continuity", state)


def load_calibration_continuity_state(csr: ConstitutionalStateRuntime) -> CalibrationContinuityState | None:
    try:
        doc = csr.get_domain_doc(CALIBRATION_CONTINUITY_STATE_ID, CalibrationContinuityState)
        assert isinstance(doc, CalibrationContinuityState)
        return doc
    except KeyError:
        return None
