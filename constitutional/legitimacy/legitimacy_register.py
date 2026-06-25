"""Stewardship Legitimacy Register — certified stewards authorized to touch invariants."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.legitimacy.spec import MIN_PLURALITY_FOR_INVARIANT_ALTERATION
from constitutional.runtime.runtime import ConstitutionalStateRuntime

LEGITIMACY_REGISTER_DOC_ID = "legitimacy_register__global"


class CertifiedStewardEntry(BaseModel):
    steward_id: str
    certified_at: datetime
    certified_by: list[str] = Field(default_factory=list)
    exam_passed: bool = False
    process_passed: bool = False
    legitimacy_index: float = Field(ge=0.0, le=1.0, default=0.0)
    active: bool = True
    receipt_refs: list[str] = Field(default_factory=list)


class StewardshipLegitimacyRegister(BaseModel):
    register_id: str = LEGITIMACY_REGISTER_DOC_ID
    minimum_plurality: int = MIN_PLURALITY_FOR_INVARIANT_ALTERATION
    entries: list[CertifiedStewardEntry] = Field(default_factory=list)

    def append(self, entry: CertifiedStewardEntry) -> None:
        self.entries.append(entry)

    def active_stewards(self) -> list[CertifiedStewardEntry]:
        return [
            entry
            for entry in self.entries
            if entry.active and entry.exam_passed and entry.process_passed
        ]

    def get_active(self, steward_id: str) -> CertifiedStewardEntry | None:
        matches = [
            entry
            for entry in self.entries
            if entry.steward_id == steward_id and entry.active and entry.exam_passed and entry.process_passed
        ]
        if not matches:
            return None
        return sorted(matches, key=lambda entry: entry.certified_at)[-1]

    def plurality_satisfied(self) -> bool:
        return len(self.active_stewards()) >= self.minimum_plurality


def load_legitimacy_register(csr: ConstitutionalStateRuntime) -> StewardshipLegitimacyRegister:
    try:
        doc = csr.get_domain_doc(LEGITIMACY_REGISTER_DOC_ID, StewardshipLegitimacyRegister)
        assert isinstance(doc, StewardshipLegitimacyRegister)
        return doc
    except KeyError:
        return StewardshipLegitimacyRegister()


def save_legitimacy_register(csr: ConstitutionalStateRuntime, register: StewardshipLegitimacyRegister) -> None:
    csr.put_domain_doc(LEGITIMACY_REGISTER_DOC_ID, "legitimacy_register", register)


def certify_steward(
    csr: ConstitutionalStateRuntime,
    *,
    steward_id: str,
    certified_by: list[str],
    exam_passed: bool,
    legitimacy_index: float,
    process_passed: bool = False,
    receipt_refs: list[str] | None = None,
    certified_at: datetime | None = None,
) -> CertifiedStewardEntry:
    now = certified_at or datetime.now(UTC).replace(microsecond=0)
    entry = CertifiedStewardEntry(
        steward_id=steward_id,
        certified_at=now,
        certified_by=list(certified_by),
        exam_passed=exam_passed,
        process_passed=process_passed,
        legitimacy_index=legitimacy_index,
        receipt_refs=receipt_refs or [],
    )
    register = load_legitimacy_register(csr)
    register.append(entry)
    save_legitimacy_register(csr, register)
    return entry
