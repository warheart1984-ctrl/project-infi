"""Salience Ledger — perceptual memory of constitutional judgment (Article Q-6)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

SALIENCE_LEDGER_DOC_ID = "salience_ledger__global"


class SalienceEntry(BaseModel):
    timestamp: datetime
    decision_id: str
    artifact_id: str | None = None
    primary_signals: list[str] = Field(default_factory=list)
    secondary_signals: list[str] = Field(default_factory=list)
    ignored_signals: list[str] = Field(default_factory=list)
    risk_salience: list[str] = Field(default_factory=list)
    deprioritized_risks: list[str] = Field(default_factory=list)
    attention_triggers: list[str] = Field(default_factory=list)
    attention_suppressors: list[str] = Field(default_factory=list)
    steward_id: str = "steward"
    notes: str | None = None


class SalienceLedger(BaseModel):
    ledger_id: str = SALIENCE_LEDGER_DOC_ID
    entries: list[SalienceEntry] = Field(default_factory=list)

    def append(self, entry: SalienceEntry) -> None:
        self.entries.append(entry)

    def entries_for_artifact(self, artifact_id: str) -> list[SalienceEntry]:
        return [entry for entry in self.entries if entry.artifact_id == artifact_id]

    def latest_for_artifact(self, artifact_id: str) -> SalienceEntry | None:
        matches = self.entries_for_artifact(artifact_id)
        if not matches:
            return None
        return sorted(matches, key=lambda entry: entry.timestamp)[-1]


def load_salience_ledger(csr) -> SalienceLedger:
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    assert isinstance(csr, ConstitutionalStateRuntime)
    try:
        doc = csr.get_domain_doc(SALIENCE_LEDGER_DOC_ID, SalienceLedger)
        assert isinstance(doc, SalienceLedger)
        return doc
    except KeyError:
        return SalienceLedger()


def save_salience_ledger(csr, ledger: SalienceLedger) -> None:
    csr.put_domain_doc(SALIENCE_LEDGER_DOC_ID, "salience_ledger", ledger)
