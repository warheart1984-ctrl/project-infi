"""Failure History Runtime — ECK-1 §6."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.eck1.registers import FailureRegister, load_failure_register
from constitutional.runtime.runtime import ConstitutionalStateRuntime

FAILURE_HISTORY_STATE_ID = "failure_history__global"
FAILURE_CONTINUITY_MIN_INDEX = 0.8


class FailureHistoryFailure(str, Enum):
    UNRESOLVED_FAILURE = "ECK-F1 UnresolvedFailure"
    MISSING_LINEAGE = "ECK-F2 MissingLineage"
    LAYER_BLINDNESS = "ECK-F3 LayerBlindness"


class FailureHistoryState(BaseModel):
    state_id: str = FAILURE_HISTORY_STATE_ID
    state_type: str = "failure_history"
    snapshot_at: datetime
    version: int = Field(default=1, ge=1)
    failure_continuity_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: list[FailureHistoryFailure] = Field(default_factory=list)
    unresolved_failures: list[str] = Field(default_factory=list)
    missing_lineage: list[str] = Field(default_factory=list)


class FailureHistoryRuntime:
    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        failure_register: FailureRegister | None = None,
    ) -> None:
        self.csr = csr
        self.failure_register = failure_register or load_failure_register(csr)

    def run(self, now: datetime | None = None) -> FailureHistoryState:
        now = now or datetime.now(UTC).replace(microsecond=0)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        failed: list[FailureHistoryFailure] = []
        unresolved: list[str] = []
        missing_lineage: list[str] = []

        for entry in self.failure_register.unresolved():
            failed.append(FailureHistoryFailure.UNRESOLVED_FAILURE)
            unresolved.append(entry.failure_class)

        layers = {e.layer for e in self.failure_register.entries}
        expected_layers = {"prior", "salience", "environment", "calibration", "judgment", "significance"}
        if self.failure_register.entries and not layers.intersection(expected_layers):
            failed.append(FailureHistoryFailure.LAYER_BLINDNESS)
            missing_lineage.append("no_layer_tags")

        for entry in self.failure_register.entries:
            if not entry.decision_id:
                failed.append(FailureHistoryFailure.MISSING_LINEAGE)
                missing_lineage.append(entry.failure_class)

        unique_failed = list(dict.fromkeys(failed))
        failure_continuity_index = 1.0 - (len(unique_failed) / len(FailureHistoryFailure))

        try:
            prev = load_failure_history_state(self.csr)
            version = (prev.version + 1) if prev else 1
        except KeyError:
            version = 1

        state = FailureHistoryState(
            snapshot_at=now,
            version=version,
            failure_continuity_index=failure_continuity_index,
            failed_surfaces=unique_failed,
            unresolved_failures=unresolved,
            missing_lineage=missing_lineage,
        )
        self._register_state(state)
        return state

    def _register_state(self, state: FailureHistoryState) -> None:
        self.csr.register_or_replace_state(
            StateObject(
                state_id=FAILURE_HISTORY_STATE_ID,
                state_type="failure_history",
                current_state="Observed" if state.failure_continuity_index >= FAILURE_CONTINUITY_MIN_INDEX else "Proposed",
            )
        )
        self.csr.put_domain_doc(FAILURE_HISTORY_STATE_ID, "failure_history", state)


def load_failure_history_state(csr: ConstitutionalStateRuntime) -> FailureHistoryState | None:
    try:
        doc = csr.get_domain_doc(FAILURE_HISTORY_STATE_ID, FailureHistoryState)
        assert isinstance(doc, FailureHistoryState)
        return doc
    except KeyError:
        return None
