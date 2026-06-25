"""Invariant Register — identity anchor ledger for JPSS-I / ECK-2."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

INVARIANT_REGISTER_DOC_ID = "invariant_register__global"


class InvariantEntry(BaseModel):
    timestamp: datetime
    steward_id: str

    purpose_clauses: list[str] = Field(default_factory=list)
    core_values: list[str] = Field(default_factory=list)
    commitments: list[str] = Field(default_factory=list)
    identity_markers: list[str] = Field(default_factory=list)
    sacred_constraints: list[str] = Field(default_factory=list)

    notes: str | None = None


class InvariantRegister(BaseModel):
    register_id: str = INVARIANT_REGISTER_DOC_ID
    entries: list[InvariantEntry] = Field(default_factory=list)

    def append(self, entry: InvariantEntry) -> None:
        self.entries.append(entry)

    def latest(self) -> InvariantEntry | None:
        if not self.entries:
            return None
        return sorted(self.entries, key=lambda entry: entry.timestamp)[-1]


def load_invariant_register(csr) -> InvariantRegister:
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    assert isinstance(csr, ConstitutionalStateRuntime)
    try:
        doc = csr.get_domain_doc(INVARIANT_REGISTER_DOC_ID, InvariantRegister)
        assert isinstance(doc, InvariantRegister)
        return doc
    except KeyError:
        return InvariantRegister()


def save_invariant_register(csr, register: InvariantRegister) -> None:
    csr.put_domain_doc(INVARIANT_REGISTER_DOC_ID, "invariant_register", register)
