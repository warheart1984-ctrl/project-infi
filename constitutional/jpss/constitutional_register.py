"""Constitutional Register — records JPSS-C boundary governance decisions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from constitutional.legitimacy.jpss_c_spec import ConstitutionalAction, ConstitutionalClassification

CONSTITUTIONAL_REGISTER_DOC_ID = "jpss_c_constitutional_register__global"

BoundaryLayer = Literal["adaptive", "invariant", "constitutional"]


class ConstitutionalDecisionEntry(BaseModel):
    timestamp: datetime
    steward_id: str
    action: ConstitutionalAction
    target_layer: BoundaryLayer
    item: str
    classification: ConstitutionalClassification
    rationale: str
    reconstruction_evidence: list[str] = Field(default_factory=list)
    consequence_simulation: str | None = None
    prior_classification: BoundaryLayer | None = None
    new_classification: BoundaryLayer | None = None


class ConstitutionalRegister(BaseModel):
    register_id: str = CONSTITUTIONAL_REGISTER_DOC_ID
    entries: list[ConstitutionalDecisionEntry] = Field(default_factory=list)

    def append(self, entry: ConstitutionalDecisionEntry) -> None:
        self.entries.append(entry)

    def for_item(self, item: str) -> list[ConstitutionalDecisionEntry]:
        return [entry for entry in self.entries if entry.item == item]


def load_constitutional_register(csr) -> ConstitutionalRegister:
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    assert isinstance(csr, ConstitutionalStateRuntime)
    try:
        doc = csr.get_domain_doc(CONSTITUTIONAL_REGISTER_DOC_ID, ConstitutionalRegister)
        assert isinstance(doc, ConstitutionalRegister)
        return doc
    except KeyError:
        return ConstitutionalRegister()


def save_constitutional_register(csr, register: ConstitutionalRegister) -> None:
    csr.put_domain_doc(CONSTITUTIONAL_REGISTER_DOC_ID, "jpss_c_constitutional_register", register)
