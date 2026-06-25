"""Salience Continuity Runtime — Article Q-6 (Q-SC failure classes)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.ledger import (
    SalienceEntry,
    SalienceLedger,
    load_salience_ledger,
    save_salience_ledger,
)
from constitutional.stewardship.artifact_index import ArtifactIndex, default_artifact_index

SALIENCE_CONTINUITY_STATE_ID = "salience_continuity__global"
SALIENCE_CONTINUITY_MIN_INDEX = 0.8


class SalienceFailure(str, Enum):
    SALIENCE_LOSS = "Q-SC1 SalienceLoss"
    SALIENCE_DRIFT = "Q-SC2 SalienceDrift"
    SALIENCE_INVERSION = "Q-SC3 SalienceInversion"
    SALIENCE_BLINDNESS = "Q-SC4 SalienceBlindness"
    SALIENCE_OVERFITTING = "Q-SC5 SalienceOverfitting"


class StewardKnowledgeIndex:
    """Whether the steward can explain historical salience for an artifact."""

    def __init__(self, explainable: set[str] | None = None) -> None:
        self._explainable = explainable or set()

    def can_explain_salience(self, artifact_id: str) -> bool:
        return artifact_id in self._explainable

    @classmethod
    def from_ledger(cls, ledger: SalienceLedger) -> StewardKnowledgeIndex:
        return cls({entry.artifact_id for entry in ledger.entries if entry.artifact_id})


class SalienceContinuityState(BaseModel):
    state_id: str = SALIENCE_CONTINUITY_STATE_ID
    state_type: str = "salience_continuity"
    snapshot_at: datetime
    version: int = Field(default=1, ge=1)
    salience_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: list[SalienceFailure] = Field(default_factory=list)
    missing_salience_entries: list[str] = Field(default_factory=list)
    drift_candidates: list[str] = Field(default_factory=list)
    inversions: list[str] = Field(default_factory=list)
    blind_stewards: list[str] = Field(default_factory=list)
    overfit_cases: list[str] = Field(default_factory=list)


class SalienceContinuityRuntime:
    """Detect whether stewards can reconstruct what was considered important."""

    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        salience_ledger: SalienceLedger | None = None,
        artifact_index: ArtifactIndex | None = None,
        steward_knowledge_index: StewardKnowledgeIndex | None = None,
    ) -> None:
        self.csr = csr
        self.salience_ledger = salience_ledger or load_salience_ledger(csr)
        self.artifact_index = artifact_index or default_artifact_index()
        self.steward_knowledge_index = steward_knowledge_index or StewardKnowledgeIndex.from_ledger(
            self.salience_ledger
        )

    def run(self, now: datetime | None = None) -> SalienceContinuityState:
        now = now or datetime.now(UTC).replace(microsecond=0)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        failed: list[SalienceFailure] = []
        missing: list[str] = []
        drift: list[str] = []
        inversions: list[str] = []
        blind: list[str] = []
        overfit: list[str] = []

        recorded = {
            entry.artifact_id
            for entry in self.salience_ledger.entries
            if entry.artifact_id
        }
        for artifact in self.artifact_index.tier_0_and_1():
            if artifact.id not in recorded:
                failed.append(SalienceFailure.SALIENCE_LOSS)
                missing.append(artifact.id)

            if not self.steward_knowledge_index.can_explain_salience(artifact.id):
                failed.append(SalienceFailure.SALIENCE_BLINDNESS)
                blind.append(artifact.id)

        unique_failed = list(dict.fromkeys(failed))
        salience_index = 1.0 - (len(unique_failed) / len(SalienceFailure))

        try:
            prev = load_salience_continuity_state(self.csr)
            version = prev.version + 1 if prev else 1
        except KeyError:
            version = 1

        state = SalienceContinuityState(
            snapshot_at=now,
            version=version,
            salience_index=salience_index,
            failed_surfaces=unique_failed,
            missing_salience_entries=missing,
            drift_candidates=drift,
            inversions=inversions,
            blind_stewards=blind,
            overfit_cases=overfit,
        )
        self._register_state(state)
        return state

    def _register_state(self, state: SalienceContinuityState) -> None:
        self.csr.register_or_replace_state(
            StateObject(
                state_id=SALIENCE_CONTINUITY_STATE_ID,
                state_type="salience_continuity",
                current_state="Observed" if state.salience_index >= SALIENCE_CONTINUITY_MIN_INDEX else "Proposed",
            )
        )
        self.csr.put_domain_doc(SALIENCE_CONTINUITY_STATE_ID, "salience_continuity", state)


def load_salience_continuity_state(csr: ConstitutionalStateRuntime) -> SalienceContinuityState | None:
    try:
        doc = csr.get_domain_doc(SALIENCE_CONTINUITY_STATE_ID, SalienceContinuityState)
        assert isinstance(doc, SalienceContinuityState)
        return doc
    except KeyError:
        return None


def append_salience_entry(csr: ConstitutionalStateRuntime, entry: SalienceEntry) -> SalienceLedger:
    ledger = load_salience_ledger(csr)
    ledger.append(entry)
    save_salience_ledger(csr, ledger)
    return ledger
