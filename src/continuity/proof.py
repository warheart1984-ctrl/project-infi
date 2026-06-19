"""Proof as trace-backed continuity validity — not a label."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

from src.continuity.ccs import CCSStore, ContinuityTrace, continuity_trace_fingerprint, replay_trace_from_store
from src.continuity.ugr_trace import evaluate_trace_ugr_invariants, valid_continuity_trace


class ProofStatus(str, Enum):
    PROVEN = "PROVEN"
    REVOKED = "REVOKED"
    PENDING = "PENDING"


DEFAULT_PROOF_LAW_SURFACES = ("ugr.continuity", "aais.proof")
REQUIRED_PROOF_LAW_SURFACES = frozenset({"ugr.continuity", "aais.proof"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Proof:
    proof_id: str
    subject_ref: str
    continuity_trace_ref: str
    law_surfaces: list[str] = field(default_factory=lambda: list(DEFAULT_PROOF_LAW_SURFACES))
    status: ProofStatus = ProofStatus.PENDING
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    continuity_invariants: dict[str, dict[str, str]] = field(default_factory=dict)
    replay_fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "subject_ref": self.subject_ref,
            "continuity_trace_ref": self.continuity_trace_ref,
            "law_surfaces": list(self.law_surfaces),
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "continuity_invariants": dict(self.continuity_invariants),
            "replay_fingerprint": self.replay_fingerprint,
        }


def new_proof_id() -> str:
    return f"proof:{uuid.uuid4().hex[:16]}"


def proof_law_surfaces_valid(proof: Proof) -> bool:
    """LS-3: Proof must declare ugr.continuity (and aais.proof) in law_surfaces."""
    declared = set(proof.law_surfaces)
    return REQUIRED_PROOF_LAW_SURFACES.issubset(declared)


def create_proof(
    *,
    store: CCSStore,
    subject_ref: str,
    trace: ContinuityTrace,
    proof_id: str | None = None,
) -> Proof:
    """Create a Proof bound to a ContinuityTrace. Status is PROVEN only when valid."""
    proof_id = proof_id or new_proof_id()
    invariants = evaluate_trace_ugr_invariants(store, trace)
    replay_fp = continuity_trace_fingerprint(replay_trace_from_store(store, trace))
    is_valid = valid_continuity_trace(store, trace)
    return Proof(
        proof_id=proof_id,
        subject_ref=subject_ref,
        continuity_trace_ref=trace.id,
        status=ProofStatus.PROVEN if is_valid else ProofStatus.PENDING,
        continuity_invariants=invariants,
        replay_fingerprint=replay_fp,
    )


def valid_proof(store: CCSStore, proof: Proof) -> tuple[bool, dict[str, Any]]:
    """
    Valid(Proof) ⇔ Valid(CT) ∧ Replay(CT) == CT ∧ All(UGR invariants satisfied).

    Returns (is_valid, detail).
    """
    if proof.status == ProofStatus.REVOKED:
        return False, {"reason": "proof_revoked"}

    if not proof_law_surfaces_valid(proof):
        return False, {"reason": "invalid_proof_law_surfaces", "required": sorted(REQUIRED_PROOF_LAW_SURFACES)}

    trace = store.traces.get(proof.continuity_trace_ref)
    if trace is None:
        return False, {"reason": "missing_continuity_trace"}

    if not valid_continuity_trace(store, trace):
        return False, {"reason": "invalid_continuity_trace"}

    replayed = replay_trace_from_store(store, trace)
    replay_fp = continuity_trace_fingerprint(replayed)
    original_fp = continuity_trace_fingerprint(trace)
    if replay_fp != original_fp:
        return False, {"reason": "replay_unstable", "replay_fp": replay_fp, "original_fp": original_fp}

    invariants = evaluate_trace_ugr_invariants(store, trace)
    if not all(entry["status"] == "pass" for entry in invariants.values()):
        return False, {"reason": "ugr_invariant_failure", "invariants": invariants}

    if proof.replay_fingerprint and proof.replay_fingerprint != replay_fp:
        return False, {"reason": "proof_fingerprint_mismatch"}

    return True, {"reason": "valid", "replay_fingerprint": replay_fp, "invariants": invariants}


def revoke_proof(proof: Proof, *, reason: str = "") -> Proof:
    """Revoking proof invalidates the proof object (trace may be superseded separately)."""
    proof.status = ProofStatus.REVOKED
    proof.updated_at = _now_iso()
    if reason:
        proof.continuity_invariants = {
            **proof.continuity_invariants,
            "revocation": {"status": "revoked", "detail": reason},
        }
    return proof
