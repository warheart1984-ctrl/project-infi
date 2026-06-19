"""Admission proof gate for operator-scoped Nova sessions."""

from __future__ import annotations

from dataclasses import dataclass

from nova.exceptions import GovernanceViolationError
from nova.identity import NovaIdentity


@dataclass(frozen=True)
class AdmissionProof:
    admitted: bool
    reason: str = "ok"


def run_proof_gate(
    identity: NovaIdentity,
    *,
    operator_session_active: bool,
) -> AdmissionProof:
    if not operator_session_active:
        return AdmissionProof(admitted=False, reason="operator session inactive")
    if not identity.operator_session_id:
        return AdmissionProof(admitted=False, reason="operator session id required")
    return AdmissionProof(admitted=True)


def require_admitted(proof: AdmissionProof) -> AdmissionProof:
    if not proof.admitted:
        raise GovernanceViolationError(proof.reason, code="NOVA-ADMISSION-DENIED")
    return proof
