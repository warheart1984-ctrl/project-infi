"""Decision Environment Runtime — context continuity across judgments."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.runtime.receipts_v2 import DecisionReceiptV2
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.significance.significance_failures import (
    QEC_SURFACE_COUNT,
    DecisionEnvironmentFailure,
)
from constitutional.significance.stewardship_context_ledger import (
    StewardshipContextLedger,
    load_stewardship_context_ledger,
)

DECISION_ENVIRONMENT_STATE_ID = "decision_environment__global"
DECISION_ENVIRONMENT_RUNTIME_NAME = "DecisionEnvironmentRuntime"


class DecisionEnvironmentState(BaseModel):
    state_id: str = DECISION_ENVIRONMENT_STATE_ID
    state_type: str = "decision_environment"
    snapshot_at: datetime
    version: int = Field(ge=1)

    environment_health_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: list[DecisionEnvironmentFailure] = Field(default_factory=list)

    context_loss_decisions: list[str] = Field(default_factory=list)
    misaligned_context_decisions: list[str] = Field(default_factory=list)
    drift_candidates: list[str] = Field(default_factory=list)
    fossilized_context_decisions: list[str] = Field(default_factory=list)
    context_blind_stewards: list[str] = Field(default_factory=list)


def load_decision_environment_state(csr: ConstitutionalStateRuntime) -> DecisionEnvironmentState:
    doc = csr.get_domain_doc(DECISION_ENVIRONMENT_STATE_ID, DecisionEnvironmentState)
    assert isinstance(doc, DecisionEnvironmentState)
    return doc


def iter_decision_ids(csr: ConstitutionalStateRuntime) -> list[str]:
    ids: list[str] = []
    for receipt in csr.get_all_receipts():
        if isinstance(receipt, DecisionReceiptV2) or receipt.lifecycle.stage == "decision":
            ids.append(receipt.receipt_id)
    return ids


class DecisionEnvironmentRuntime:
    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        *,
        context_ledger: StewardshipContextLedger | None = None,
        current_env_snapshot: dict[str, Any] | None = None,
    ) -> None:
        self.csr = csr
        self.context_ledger = context_ledger or load_stewardship_context_ledger(csr)
        self.current_env_snapshot = current_env_snapshot or {}

    def run(self, snapshot_at: datetime | None = None) -> DecisionEnvironmentState:
        now = snapshot_at or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        failed: list[DecisionEnvironmentFailure] = []
        context_loss: list[str] = []
        misaligned: list[str] = []
        drift_candidates: list[str] = []
        fossilized: list[str] = []
        blind_stewards: list[str] = []

        decision_ids_with_context = {entry.decision_id for entry in self.context_ledger.entries}
        for decision_id in iter_decision_ids(self.csr):
            if decision_id not in decision_ids_with_context:
                failed.append(DecisionEnvironmentFailure.CONTEXT_LOSS)
                context_loss.append(decision_id)

        for entry in self.context_ledger.entries:
            if self._environment_changed(entry.environmental_factors, self.current_env_snapshot):
                drift_candidates.append(entry.decision_id)
                if DecisionEnvironmentFailure.CONTEXT_DRIFT not in failed:
                    failed.append(DecisionEnvironmentFailure.CONTEXT_DRIFT)
            if self._calibration_misaligned(entry, self.current_env_snapshot):
                misaligned.append(entry.decision_id)
                if DecisionEnvironmentFailure.CONTEXT_MISALIGNMENT not in failed:
                    failed.append(DecisionEnvironmentFailure.CONTEXT_MISALIGNMENT)
            if self._fossilized(entry, self.current_env_snapshot):
                fossilized.append(entry.decision_id)
                if DecisionEnvironmentFailure.CONTEXT_FOSSILIZATION not in failed:
                    failed.append(DecisionEnvironmentFailure.CONTEXT_FOSSILIZATION)
            if not entry.signals_considered and not entry.risks_salient:
                blind_stewards.append(entry.steward_id)
                if DecisionEnvironmentFailure.CONTEXT_BLINDNESS not in failed:
                    failed.append(DecisionEnvironmentFailure.CONTEXT_BLINDNESS)

        failed = list(dict.fromkeys(failed))
        environment_health_index = max(0.0, 1.0 - len(failed) / float(QEC_SURFACE_COUNT))

        try:
            prev = load_decision_environment_state(self.csr)
            version = prev.version + 1
        except KeyError:
            version = 1

        state = DecisionEnvironmentState(
            snapshot_at=now,
            version=version,
            environment_health_index=environment_health_index,
            failed_surfaces=failed,
            context_loss_decisions=context_loss,
            misaligned_context_decisions=misaligned,
            drift_candidates=drift_candidates,
            fossilized_context_decisions=fossilized,
            context_blind_stewards=list(dict.fromkeys(blind_stewards)),
        )

        self.csr.register_or_replace_state(
            StateObject(
                state_id=DECISION_ENVIRONMENT_STATE_ID,
                state_type="decision_environment",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(DECISION_ENVIRONMENT_STATE_ID, "decision_environment", state)
        return state

    def _environment_changed(
        self,
        historical_factors: list[str],
        current_env_snapshot: dict[str, Any],
    ) -> bool:
        if not historical_factors or not current_env_snapshot:
            return False
        current_tags = set(current_env_snapshot.get("environmental_factors", []))
        return bool(current_tags) and not current_tags.intersection(historical_factors)

    def _calibration_misaligned(self, entry, current_env_snapshot: dict[str, Any]) -> bool:
        current_risks = set(current_env_snapshot.get("risks_salient", []))
        if not current_risks or not entry.risks_salient:
            return False
        overlap = current_risks.intersection(entry.risks_salient)
        return len(overlap) == 0

    def _fossilized(self, entry, current_env_snapshot: dict[str, Any]) -> bool:
        if not entry.environmental_factors:
            return False
        current_constraints = set(current_env_snapshot.get("constraints_active", []))
        if not current_constraints:
            return False
        return not current_constraints.intersection(entry.constraints_active)
