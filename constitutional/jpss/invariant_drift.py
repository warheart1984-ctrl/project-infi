"""Invariant Drift Detector — identity immune system for JPSS-I."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from constitutional.jpss.invariant_register import InvariantEntry, InvariantRegister, load_invariant_register
from constitutional.runtime.runtime import ConstitutionalStateRuntime

INVARIANT_DRIFT_STATE_ID = "invariant_drift__latest"


class InvariantDriftFailure(str, Enum):
    PURPOSE_EROSION = "I-D1 PurposeErosion"
    VALUE_REINTERPRETATION = "I-D2 ValueReinterpretation"
    COMMITMENT_WEAKENING = "I-D3 CommitmentWeakening"
    IDENTITY_DRIFT = "I-D4 IdentityDrift"
    SACRED_BYPASS = "I-D5 SacredConstraintBypass"


class InvariantDriftState(BaseModel):
    snapshot_at: datetime
    version: int = 1
    drift_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: list[InvariantDriftFailure] = Field(default_factory=list)
    erosion_cases: list[str] = Field(default_factory=list)
    reinterpretations: list[str] = Field(default_factory=list)
    weakenings: list[str] = Field(default_factory=list)
    identity_shifts: list[str] = Field(default_factory=list)
    sacred_violations: list[str] = Field(default_factory=list)

    @property
    def drift_detected(self) -> bool:
        return bool(self.failed_surfaces)


class InvariantDriftDetector:
    """Detect erosion of purpose, values, commitments, identity, and sacred constraints."""

    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        invariant_register: InvariantRegister,
        current_invariants: InvariantEntry,
    ) -> None:
        self.csr = csr
        self.register = invariant_register
        self.current = current_invariants

    def _aggregate(self) -> dict[str, set[str]]:
        purpose: set[str] = set()
        values: set[str] = set()
        commitments: set[str] = set()
        identity: set[str] = set()
        sacred: set[str] = set()

        for entry in self.register.entries:
            purpose.update(entry.purpose_clauses)
            values.update(entry.core_values)
            commitments.update(entry.commitments)
            identity.update(entry.identity_markers)
            sacred.update(entry.sacred_constraints)

        return {
            "purpose": purpose,
            "values": values,
            "commitments": commitments,
            "identity": identity,
            "sacred": sacred,
        }

    def run(self) -> InvariantDriftState:
        historical = self._aggregate()

        failures: list[InvariantDriftFailure] = []
        erosion: list[str] = []
        reinterpret: list[str] = []
        weaken: list[str] = []
        identity: list[str] = []
        sacred: list[str] = []

        current_purpose = set(self.current.purpose_clauses)
        current_values = set(self.current.core_values)
        current_commitments = set(self.current.commitments)
        current_identity = set(self.current.identity_markers)
        current_sacred = set(self.current.sacred_constraints)

        for clause in historical["purpose"]:
            if clause not in current_purpose:
                failures.append(InvariantDriftFailure.PURPOSE_EROSION)
                erosion.append(clause)

        for value in historical["values"]:
            if value not in current_values:
                failures.append(InvariantDriftFailure.VALUE_REINTERPRETATION)
                reinterpret.append(value)

        for commitment in historical["commitments"]:
            if commitment not in current_commitments:
                failures.append(InvariantDriftFailure.COMMITMENT_WEAKENING)
                weaken.append(commitment)

        for marker in historical["identity"]:
            if marker not in current_identity:
                failures.append(InvariantDriftFailure.IDENTITY_DRIFT)
                identity.append(marker)

        for constraint in historical["sacred"]:
            if constraint not in current_sacred:
                failures.append(InvariantDriftFailure.SACRED_BYPASS)
                sacred.append(constraint)

        unique_failures = list(dict.fromkeys(failures))
        drift_index = 1.0 - (len(unique_failures) / 5.0)

        return InvariantDriftState(
            snapshot_at=datetime.now(UTC).replace(microsecond=0),
            version=1,
            drift_index=drift_index,
            failed_surfaces=unique_failures,
            erosion_cases=erosion,
            reinterpretations=reinterpret,
            weakenings=weaken,
            identity_shifts=identity,
            sacred_violations=sacred,
        )


def detect_invariant_drift(
    csr: ConstitutionalStateRuntime,
    *,
    current_invariants: InvariantEntry | None = None,
) -> InvariantDriftState:
    """Run invariant drift detection against the global register."""
    register = load_invariant_register(csr)
    current = current_invariants or register.latest()
    if current is None:
        return InvariantDriftState(
            snapshot_at=datetime.now(UTC).replace(microsecond=0),
            drift_index=1.0,
        )

    state = InvariantDriftDetector(csr, register, current).run()
    csr.put_domain_doc(INVARIANT_DRIFT_STATE_ID, "invariant_drift_state", state)
    return state


def load_invariant_drift_state(csr: ConstitutionalStateRuntime) -> InvariantDriftState | None:
    try:
        doc = csr.get_domain_doc(INVARIANT_DRIFT_STATE_ID, InvariantDriftState)
        assert isinstance(doc, InvariantDriftState)
        return doc
    except KeyError:
        return None
