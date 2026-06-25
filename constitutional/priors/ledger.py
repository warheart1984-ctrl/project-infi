"""Stewardship Prior Ledger — expectations that shape salience and judgment."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

PRIOR_LEDGER_DOC_ID = "stewardship_prior_ledger__global"


class PriorEntry(BaseModel):
    timestamp: datetime
    decision_id: str
    artifact_id: str | None = None
    expected_signals: list[str] = Field(default_factory=list)
    expected_risks: list[str] = Field(default_factory=list)
    assumed_stabilities: list[str] = Field(default_factory=list)
    assumed_volatilities: list[str] = Field(default_factory=list)
    predictive_models: list[str] = Field(default_factory=list)
    feared_failures: list[str] = Field(default_factory=list)
    ignored_possibilities: list[str] = Field(default_factory=list)
    steward_id: str = "steward"
    notes: str | None = None


class StewardshipPriorLedger(BaseModel):
    ledger_id: str = PRIOR_LEDGER_DOC_ID
    entries: list[PriorEntry] = Field(default_factory=list)

    def append(self, entry: PriorEntry) -> None:
        self.entries.append(entry)


def load_prior_ledger(csr) -> StewardshipPriorLedger:
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    assert isinstance(csr, ConstitutionalStateRuntime)
    try:
        doc = csr.get_domain_doc(PRIOR_LEDGER_DOC_ID, StewardshipPriorLedger)
        assert isinstance(doc, StewardshipPriorLedger)
        return doc
    except KeyError:
        return StewardshipPriorLedger()


def save_prior_ledger(csr, ledger: StewardshipPriorLedger) -> None:
    csr.put_domain_doc(PRIOR_LEDGER_DOC_ID, "stewardship_prior_ledger", ledger)
