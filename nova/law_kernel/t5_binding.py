"""T5 Reference Integrity Layer — reference signals and invariant proofs."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class T5ReferenceSignal:
    id: str
    hash: str
    issued_at: str
    issuer: str
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def current(cls, *, allow_fallback: bool = False, ref_hash: str | None = None) -> T5ReferenceSignal:
        """
        Resolve T5 binding via reference_bridge first.
        Fallback to ref-hash-default only when allow_fallback=True or T5_ALLOW_FALLBACK=1.
        """
        explicit_fallback = allow_fallback or os.environ.get("T5_ALLOW_FALLBACK", "").strip() in {
            "1",
            "true",
            "yes",
        }
        try:
            from nova.bridges.reference_bridge import current_reference_binding, resolve_reference

            if ref_hash:
                binding = resolve_reference(ref_hash)
                if binding is None:
                    if not explicit_fallback:
                        raise RuntimeError(f"T5 reference hash mismatch: {ref_hash}")
                    return cls._fallback_signal()
            else:
                binding = current_reference_binding()

            return cls(
                id="t5-ril-current",
                hash=binding.ref_hash,
                issued_at="runtime",
                issuer="crk-t5",
                payload={"metrics": binding.metrics, "bound": binding.bound},
            )
        except Exception:
            if explicit_fallback:
                return cls._fallback_signal()
            raise

    @classmethod
    def _fallback_signal(cls) -> T5ReferenceSignal:
        return cls(
            id="t5-default",
            hash="ref-hash-default",
            issued_at="1970-01-01T00:00:00Z",
            issuer="t5-ril",
            payload={},
        )


@dataclass(frozen=True, slots=True)
class InvariantProof:
    id: str
    subject_type: str
    subject_id: str
    ref_signal_hash: str
    invariants: tuple[str, ...]
    proof_blob: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "ref_signal_hash": self.ref_signal_hash,
            "invariants": list(self.invariants),
            "proof_blob": self.proof_blob,
            "created_at": self.created_at,
        }


class InvariantViolation(RuntimeError):
    def __init__(self, code: str, *, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.details = dict(details or {})
        super().__init__(f"{code}: {self.details}")


class InvariantLedger:
    """Records and verifies T5 invariant proofs for law decisions."""

    _proofs: dict[str, InvariantProof] = {}

    @classmethod
    def issue(
        cls,
        *,
        subject_type: str,
        subject_id: str,
        ref_signal_hash: str,
        invariants: tuple[str, ...],
        payload: dict[str, Any],
    ) -> InvariantProof:
        proof_id = f"proof-{uuid.uuid4().hex[:12]}"
        blob = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        proof = InvariantProof(
            id=proof_id,
            subject_type=subject_type,
            subject_id=subject_id,
            ref_signal_hash=ref_signal_hash,
            invariants=invariants,
            proof_blob=blob,
            created_at="runtime",
        )
        cls._proofs[proof_id] = proof
        return proof

    @classmethod
    def verify(
        cls,
        proof: InvariantProof | str,
        *,
        contract_id: str | None = None,
        event_id: str | None = None,
        ref_signal_hash: str | None = None,
    ) -> bool:
        resolved = cls._proofs.get(proof) if isinstance(proof, str) else proof
        if resolved is None:
            return False
        if ref_signal_hash and resolved.ref_signal_hash != ref_signal_hash:
            return False
        subject_id = event_id or contract_id or ""
        if subject_id and resolved.subject_id != subject_id:
            return False
        return True

    @classmethod
    def reset(cls) -> None:
        cls._proofs.clear()


def bind_law_eval_proof(eval_payload: dict[str, Any]) -> InvariantProof:
    """T5-LAW-1..3 — attach reproducible proof to a law evaluation."""
    return InvariantLedger.issue(
        subject_type="LAW_EVAL",
        subject_id=str(eval_payload.get("candidate_intent", {}).get("id", "unknown")),
        ref_signal_hash=str(eval_payload.get("t5_ref_signal_hash", "")),
        invariants=("T5-LAW-1", "T5-LAW-2", "T5-LAW-3"),
        payload=eval_payload,
    )
