"""JPSS-1 canonical registers — reconstructability substrate."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

PERCEPTION_REGISTER_DOC_ID = "jpss_perception_register__global"
DECISION_REGISTER_DOC_ID = "jpss_decision_register__global"
OUTCOME_REGISTER_DOC_ID = "jpss_outcome_register__global"
REFLECTION_REGISTER_DOC_ID = "jpss_reflection_register__global"
JPSS_CYCLE_STATE_ID = "jpss_cycle__latest"


class PerceptionEntry(BaseModel):
    timestamp: datetime
    decision_id: str
    available_signals: list[str] = Field(default_factory=list)
    missing_signals: list[str] = Field(default_factory=list)
    intake_channels: list[str] = Field(default_factory=list)
    steward_id: str = "steward"


class PerceptionRegister(BaseModel):
    register_id: str = PERCEPTION_REGISTER_DOC_ID
    entries: list[PerceptionEntry] = Field(default_factory=list)

    def append(self, entry: PerceptionEntry) -> None:
        self.entries.append(entry)

    def latest_for_decision(self, decision_id: str) -> PerceptionEntry | None:
        matches = [entry for entry in self.entries if entry.decision_id == decision_id]
        if not matches:
            return None
        return sorted(matches, key=lambda entry: entry.timestamp)[-1]


class DecisionEntry(BaseModel):
    timestamp: datetime
    decision_id: str
    outcome: str
    rationale: str
    applied_invariants: list[str] = Field(default_factory=list)
    applied_purpose_clauses: list[str] = Field(default_factory=list)
    steward_id: str = "steward"


class DecisionRegister(BaseModel):
    register_id: str = DECISION_REGISTER_DOC_ID
    entries: list[DecisionEntry] = Field(default_factory=list)

    def append(self, entry: DecisionEntry) -> None:
        self.entries.append(entry)

    def latest_for_decision(self, decision_id: str) -> DecisionEntry | None:
        matches = [entry for entry in self.entries if entry.decision_id == decision_id]
        if not matches:
            return None
        return sorted(matches, key=lambda entry: entry.timestamp)[-1]


class OutcomeEntry(BaseModel):
    timestamp: datetime
    decision_id: str
    observed_result: str
    expected_result: str | None = None
    success: bool | None = None
    steward_id: str = "steward"


class OutcomeRegister(BaseModel):
    register_id: str = OUTCOME_REGISTER_DOC_ID
    entries: list[OutcomeEntry] = Field(default_factory=list)

    def append(self, entry: OutcomeEntry) -> None:
        self.entries.append(entry)

    def latest_for_decision(self, decision_id: str) -> OutcomeEntry | None:
        matches = [entry for entry in self.entries if entry.decision_id == decision_id]
        if not matches:
            return None
        return sorted(matches, key=lambda entry: entry.timestamp)[-1]


class ReflectionEntry(BaseModel):
    timestamp: datetime
    decision_id: str
    expectation_delta: str = ""
    lessons: list[str] = Field(default_factory=list)
    steward_id: str = "steward"


class ReflectionRegister(BaseModel):
    register_id: str = REFLECTION_REGISTER_DOC_ID
    entries: list[ReflectionEntry] = Field(default_factory=list)

    def append(self, entry: ReflectionEntry) -> None:
        self.entries.append(entry)

    def latest_for_decision(self, decision_id: str) -> ReflectionEntry | None:
        matches = [entry for entry in self.entries if entry.decision_id == decision_id]
        if not matches:
            return None
        return sorted(matches, key=lambda entry: entry.timestamp)[-1]


def _load_register(csr, doc_id: str, model: type[BaseModel], default: BaseModel) -> BaseModel:
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    assert isinstance(csr, ConstitutionalStateRuntime)
    try:
        doc = csr.get_domain_doc(doc_id, model)
        assert isinstance(doc, model)
        return doc
    except KeyError:
        return default


def _save_register(csr, doc_id: str, doc_type: str, register: BaseModel) -> None:
    csr.put_domain_doc(doc_id, doc_type, register)


def load_perception_register(csr) -> PerceptionRegister:
    return _load_register(csr, PERCEPTION_REGISTER_DOC_ID, PerceptionRegister, PerceptionRegister())  # type: ignore[return-value]


def save_perception_register(csr, register: PerceptionRegister) -> None:
    _save_register(csr, PERCEPTION_REGISTER_DOC_ID, "jpss_perception_register", register)


def load_decision_register(csr) -> DecisionRegister:
    return _load_register(csr, DECISION_REGISTER_DOC_ID, DecisionRegister, DecisionRegister())  # type: ignore[return-value]


def save_decision_register(csr, register: DecisionRegister) -> None:
    _save_register(csr, DECISION_REGISTER_DOC_ID, "jpss_decision_register", register)


def load_outcome_register(csr) -> OutcomeRegister:
    return _load_register(csr, OUTCOME_REGISTER_DOC_ID, OutcomeRegister, OutcomeRegister())  # type: ignore[return-value]


def save_outcome_register(csr, register: OutcomeRegister) -> None:
    _save_register(csr, OUTCOME_REGISTER_DOC_ID, "jpss_outcome_register", register)


def load_reflection_register(csr) -> ReflectionRegister:
    return _load_register(csr, REFLECTION_REGISTER_DOC_ID, ReflectionRegister, ReflectionRegister())  # type: ignore[return-value]


def save_reflection_register(csr, register: ReflectionRegister) -> None:
    _save_register(csr, REFLECTION_REGISTER_DOC_ID, "jpss_reflection_register", register)
