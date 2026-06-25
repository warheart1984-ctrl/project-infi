"""ECK-1 registers — ledgers for calibration and failure history."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

CALIBRATION_REGISTER_DOC_ID = "eck1_calibration_register__global"
FAILURE_REGISTER_DOC_ID = "eck1_failure_register__global"
ENVIRONMENT_REGISTER_DOC_ID = "eck1_environment_register__global"
ECK1_CONTINUITY_STATE_ID = "eck1_continuity__global"


class CalibrationEntry(BaseModel):
    timestamp: datetime
    decision_id: str
    evidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    required_invariants: list[str] = Field(default_factory=list)
    required_purpose_links: list[str] = Field(default_factory=list)
    evidence_available: list[str] = Field(default_factory=list)
    evidence_missing: list[str] = Field(default_factory=list)
    steward_id: str = "steward"
    notes: str | None = None


class CalibrationRegister(BaseModel):
    register_id: str = CALIBRATION_REGISTER_DOC_ID
    entries: list[CalibrationEntry] = Field(default_factory=list)

    def append(self, entry: CalibrationEntry) -> None:
        self.entries.append(entry)

    def latest_for_decision(self, decision_id: str) -> CalibrationEntry | None:
        matches = [e for e in self.entries if e.decision_id == decision_id]
        if not matches:
            return None
        return sorted(matches, key=lambda e: e.timestamp)[-1]


class FailureEntry(BaseModel):
    timestamp: datetime
    decision_id: str | None = None
    failure_class: str
    layer: str
    description: str = ""
    steward_id: str = "steward"
    resolved: bool = False


class FailureRegister(BaseModel):
    register_id: str = FAILURE_REGISTER_DOC_ID
    entries: list[FailureEntry] = Field(default_factory=list)

    def append(self, entry: FailureEntry) -> None:
        self.entries.append(entry)

    def unresolved(self) -> list[FailureEntry]:
        return [e for e in self.entries if not e.resolved]


class EnvironmentEntry(BaseModel):
    timestamp: datetime
    decision_id: str
    constraints_active: list[str] = Field(default_factory=list)
    incentives_present: list[str] = Field(default_factory=list)
    uncertainties_dominant: list[str] = Field(default_factory=list)
    environmental_factors: list[str] = Field(default_factory=list)
    failure_modes_feared: list[str] = Field(default_factory=list)
    steward_id: str = "steward"


class EnvironmentRegister(BaseModel):
    register_id: str = ENVIRONMENT_REGISTER_DOC_ID
    entries: list[EnvironmentEntry] = Field(default_factory=list)

    def append(self, entry: EnvironmentEntry) -> None:
        self.entries.append(entry)


def load_calibration_register(csr) -> CalibrationRegister:
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    assert isinstance(csr, ConstitutionalStateRuntime)
    try:
        doc = csr.get_domain_doc(CALIBRATION_REGISTER_DOC_ID, CalibrationRegister)
        assert isinstance(doc, CalibrationRegister)
        return doc
    except KeyError:
        return CalibrationRegister()


def save_calibration_register(csr, register: CalibrationRegister) -> None:
    csr.put_domain_doc(CALIBRATION_REGISTER_DOC_ID, "eck1_calibration_register", register)


def load_failure_register(csr) -> FailureRegister:
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    assert isinstance(csr, ConstitutionalStateRuntime)
    try:
        doc = csr.get_domain_doc(FAILURE_REGISTER_DOC_ID, FailureRegister)
        assert isinstance(doc, FailureRegister)
        return doc
    except KeyError:
        return FailureRegister()


def save_failure_register(csr, register: FailureRegister) -> None:
    csr.put_domain_doc(FAILURE_REGISTER_DOC_ID, "eck1_failure_register", register)


def load_environment_register(csr) -> EnvironmentRegister:
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    assert isinstance(csr, ConstitutionalStateRuntime)
    try:
        doc = csr.get_domain_doc(ENVIRONMENT_REGISTER_DOC_ID, EnvironmentRegister)
        assert isinstance(doc, EnvironmentRegister)
        return doc
    except KeyError:
        return EnvironmentRegister()


def save_environment_register(csr, register: EnvironmentRegister) -> None:
    csr.put_domain_doc(ENVIRONMENT_REGISTER_DOC_ID, "eck1_environment_register", register)
