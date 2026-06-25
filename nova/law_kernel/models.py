"""Nova Law Kernel v1.0 — core schemas."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


class LawStatus(str, Enum):
    ADMITTED = "admitted"
    EXPERIMENTAL = "experimental"
    REVOKED = "revoked"


class LawDecision(str, Enum):
    ADMIT = "admit"
    DENY = "deny"
    TRANSFORM = "transform"
    PANIC = "panic"


@dataclass(frozen=True, slots=True)
class Intent:
    id: str
    kind: str
    payload: dict[str, Any]
    origin: str

    def with_suffix(self, suffix: str) -> Intent:
        return replace(self, id=f"{self.id}:{suffix}")


@dataclass(frozen=True, slots=True)
class LawRecord:
    id: str
    code: str
    text: str
    status: LawStatus
    fitness: float
    created_at: str
    epoch: str
    proof_ref: str = ""
    domains: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "text": self.text,
            "status": self.status.value,
            "fitness": self.fitness,
            "created_at": self.created_at,
            "epoch": self.epoch,
            "proof_ref": self.proof_ref,
            "domains": list(self.domains),
        }

    def applies_to_domain(self, domain: str) -> bool:
        if not self.domains:
            return True
        return domain in self.domains


@dataclass(frozen=True, slots=True)
class LawContext:
    actor_id: str
    domain: str
    epoch: str
    lineage_contract_id: str
    t5_ref_signal_hash: str
    lineage_event_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "domain": self.domain,
            "epoch": self.epoch,
            "lineage_contract_id": self.lineage_contract_id,
            "lineage_event_id": self.lineage_event_id,
            "t5_ref_signal_hash": self.t5_ref_signal_hash,
        }


@dataclass(frozen=True, slots=True)
class LawEvalPayload:
    context: LawContext
    candidate_intent: Intent
    applicable_laws: tuple[LawRecord, ...]
    decision: LawDecision
    reasons: tuple[str, ...]
    t5_ref_signal_hash: str
    invariant_proof_id: str
    transformed_intent: Intent | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "candidate_intent": {
                "id": self.candidate_intent.id,
                "kind": self.candidate_intent.kind,
                "payload": dict(self.candidate_intent.payload),
                "origin": self.candidate_intent.origin,
            },
            "applicable_laws": [law.to_dict() for law in self.applicable_laws],
            "decision": self.decision.value,
            "reasons": list(self.reasons),
            "t5_ref_signal_hash": self.t5_ref_signal_hash,
            "invariant_proof_id": self.invariant_proof_id,
            "transformed_intent": (
                {
                    "id": self.transformed_intent.id,
                    "kind": self.transformed_intent.kind,
                    "payload": dict(self.transformed_intent.payload),
                    "origin": self.transformed_intent.origin,
                }
                if self.transformed_intent
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class LineageContract:
    id: str
    subject: str
    current_ref_signal_hash: str
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class LineageEvent:
    id: str
    contract_id: str
    kind: str
    payload: dict[str, Any]
    ref_signal_hash: str
    invariant_proof_id: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "kind": self.kind,
            "payload": dict(self.payload),
            "ref_signal_hash": self.ref_signal_hash,
            "invariant_proof_id": self.invariant_proof_id,
            "created_at": self.created_at,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_intent(*, kind: str, payload: dict[str, Any], origin: str) -> Intent:
    return Intent(
        id=f"intent-{uuid.uuid4().hex[:12]}",
        kind=kind,
        payload=dict(payload),
        origin=origin,
    )


def new_law_record(
    *,
    code: str,
    text: str,
    status: LawStatus = LawStatus.ADMITTED,
    fitness: float = 1.0,
    epoch: str = "EPOCH:0:T0",
    proof_ref: str = "",
    domains: tuple[str, ...] | list[str] = (),
) -> LawRecord:
    domain_tuple = tuple(domains) if domains else ()
    return LawRecord(
        id=f"law-{uuid.uuid4().hex[:10]}",
        code=code,
        text=text,
        status=status,
        fitness=fitness,
        created_at=_now_iso(),
        epoch=epoch,
        proof_ref=proof_ref,
        domains=domain_tuple,
    )
