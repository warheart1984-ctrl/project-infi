"""Stewardship context ledger — preserves decision environment at judgment time."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.runtime.runtime import ConstitutionalStateRuntime

STEWARDSHIP_CONTEXT_LEDGER_STATE_ID = "stewardship_context_ledger__global"


class StewardshipContextEntry(BaseModel):
    timestamp: datetime
    decision_id: str
    artifact_id: str | None = None

    signals_considered: list[str] = Field(default_factory=list)
    risks_salient: list[str] = Field(default_factory=list)
    constraints_active: list[str] = Field(default_factory=list)
    uncertainties_dominant: list[str] = Field(default_factory=list)
    incentives_present: list[str] = Field(default_factory=list)
    failure_modes_feared: list[str] = Field(default_factory=list)
    environmental_factors: list[str] = Field(default_factory=list)

    evidence_available: list[str] = Field(default_factory=list)
    evidence_missing: list[str] = Field(default_factory=list)

    steward_id: str = "steward"
    notes: str | None = None


class StewardshipContextLedger(BaseModel):
    ledger_id: str = STEWARDSHIP_CONTEXT_LEDGER_STATE_ID
    state_id: str = STEWARDSHIP_CONTEXT_LEDGER_STATE_ID
    state_type: str = "stewardship_context_ledger"
    entries: list[StewardshipContextEntry] = Field(default_factory=list)

    def append(self, entry: StewardshipContextEntry) -> None:
        self.entries.append(entry)

    def entries_for_artifact(self, artifact_id: str) -> list[StewardshipContextEntry]:
        return [entry for entry in self.entries if entry.artifact_id == artifact_id]

    def entries_for_decision(self, decision_id: str) -> list[StewardshipContextEntry]:
        return [entry for entry in self.entries if entry.decision_id == decision_id]


def load_stewardship_context_ledger(csr: ConstitutionalStateRuntime) -> StewardshipContextLedger:
    try:
        doc = csr.get_domain_doc(STEWARDSHIP_CONTEXT_LEDGER_STATE_ID, StewardshipContextLedger)
        assert isinstance(doc, StewardshipContextLedger)
        return doc
    except KeyError:
        return StewardshipContextLedger()


def save_stewardship_context_ledger(
    csr: ConstitutionalStateRuntime,
    ledger: StewardshipContextLedger,
) -> None:
    csr.register_or_replace_state(
        StateObject(
            state_id=STEWARDSHIP_CONTEXT_LEDGER_STATE_ID,
            state_type="stewardship_context_ledger",
            current_state="Observed",
        )
    )
    csr.put_domain_doc(STEWARDSHIP_CONTEXT_LEDGER_STATE_ID, "stewardship_context_ledger", ledger)


def append_stewardship_context(
    csr: ConstitutionalStateRuntime,
    entry: StewardshipContextEntry,
) -> StewardshipContextLedger:
    ledger = load_stewardship_context_ledger(csr)
    ledger.append(entry)
    save_stewardship_context_ledger(csr, ledger)
    return ledger
