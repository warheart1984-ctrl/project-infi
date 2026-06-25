"""JPSS-C canonical registers — preserve the constitutional process itself."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from constitutional.legitimacy.jpss_c_spec import SelectionOutcome

INVARIANT_CANDIDATE_LEDGER_ID = "jpss_c_invariant_candidate_ledger__global"
ELEVATION_REVIEW_LEDGER_ID = "jpss_c_elevation_review_ledger__global"
RETIREMENT_REVIEW_LEDGER_ID = "jpss_c_retirement_review_ledger__global"
# boundary_decisions_ledger aliases constitutional_register


class InvariantCandidateEntry(BaseModel):
    timestamp: datetime
    steward_id: str
    candidate_value: str
    signal: str = ""
    purpose_clauses: list[str] = Field(default_factory=list)
    historical_failures: list[str] = Field(default_factory=list)
    identity_markers: list[str] = Field(default_factory=list)
    steward_proposal: str = ""


class InvariantCandidateLedger(BaseModel):
    ledger_id: str = INVARIANT_CANDIDATE_LEDGER_ID
    entries: list[InvariantCandidateEntry] = Field(default_factory=list)

    def append(self, entry: InvariantCandidateEntry) -> None:
        self.entries.append(entry)


class ElevationReviewEntry(BaseModel):
    timestamp: datetime
    steward_id: str
    candidate_value: str
    criteria_met: list[str] = Field(default_factory=list)
    criteria_failed: list[str] = Field(default_factory=list)
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    outcome: SelectionOutcome
    rationale: str = ""
    ratified: bool = False


class ElevationReviewLedger(BaseModel):
    ledger_id: str = ELEVATION_REVIEW_LEDGER_ID
    entries: list[ElevationReviewEntry] = Field(default_factory=list)

    def append(self, entry: ElevationReviewEntry) -> None:
        self.entries.append(entry)


RetirementStepStatus = Literal["pending", "completed", "blocked"]


class RetirementReviewEntry(BaseModel):
    timestamp: datetime
    steward_id: str
    invariant_item: str
    triggers: list[str] = Field(default_factory=list)
    steps_completed: list[str] = Field(default_factory=list)
    retirement_approved: bool = False
    continuity_verdict: str = ""
    rationale: str = ""


class RetirementReviewLedger(BaseModel):
    ledger_id: str = RETIREMENT_REVIEW_LEDGER_ID
    entries: list[RetirementReviewEntry] = Field(default_factory=list)

    def append(self, entry: RetirementReviewEntry) -> None:
        self.entries.append(entry)


def _load_ledger(csr, doc_id: str, model_type: type[BaseModel]) -> BaseModel:
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    assert isinstance(csr, ConstitutionalStateRuntime)
    try:
        doc = csr.get_domain_doc(doc_id, model_type)
        assert isinstance(doc, model_type)
        return doc
    except KeyError:
        return model_type()


def _save_ledger(csr, doc_id: str, doc_type: str, ledger: BaseModel) -> None:
    csr.put_domain_doc(doc_id, doc_type, ledger)


def load_invariant_candidate_ledger(csr) -> InvariantCandidateLedger:
    ledger = _load_ledger(csr, INVARIANT_CANDIDATE_LEDGER_ID, InvariantCandidateLedger)
    assert isinstance(ledger, InvariantCandidateLedger)
    return ledger


def save_invariant_candidate_ledger(csr, ledger: InvariantCandidateLedger) -> None:
    _save_ledger(csr, INVARIANT_CANDIDATE_LEDGER_ID, "jpss_c_invariant_candidate_ledger", ledger)


def load_elevation_review_ledger(csr) -> ElevationReviewLedger:
    ledger = _load_ledger(csr, ELEVATION_REVIEW_LEDGER_ID, ElevationReviewLedger)
    assert isinstance(ledger, ElevationReviewLedger)
    return ledger


def save_elevation_review_ledger(csr, ledger: ElevationReviewLedger) -> None:
    _save_ledger(csr, ELEVATION_REVIEW_LEDGER_ID, "jpss_c_elevation_review_ledger", ledger)


def load_retirement_review_ledger(csr) -> RetirementReviewLedger:
    ledger = _load_ledger(csr, RETIREMENT_REVIEW_LEDGER_ID, RetirementReviewLedger)
    assert isinstance(ledger, RetirementReviewLedger)
    return ledger


def save_retirement_review_ledger(csr, ledger: RetirementReviewLedger) -> None:
    _save_ledger(csr, RETIREMENT_REVIEW_LEDGER_ID, "jpss_c_retirement_review_ledger", ledger)
