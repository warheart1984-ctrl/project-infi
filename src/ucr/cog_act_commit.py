"""Kernel syscall: cog_act_commit — sole governed cognitive act commit boundary."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from src.ucr.act_codec import deserialize_act_payload, ledger_ref_matches
from src.ucr.authority_envelope import decode_envelope, validate_envelope
from src.ucr.binary_law_key import validate_law_key
from src.ucr.corridor import validate_envelope_against_corridor
from src.ucr.corridor_loader import get_trusted_corridors, is_sealed
from src.ucr.trust_root import get_trust_root, is_trust_root_sealed, to_ucr_context
from src.ucr.ucr_attestation import UCR_NOT_REGISTERED, get_registered_ucr_handle
from src.ucr.ucr_governed import require_governed_mode

INVALID_LAW_KEY = 1001
INVALID_AUTHORITY = 1002
ACT_LEDGER_MISMATCH = 1003
UNTRUSTED_PRODUCER = 1004
ERR_CORRIDOR_NOT_FOUND = 1005
ERR_TRUST_ROOT_MISMATCH = 1006
SAFETY_VETO = 2001

_TRUSTED_PRODUCERS: set[str] = {"ucr.default"}
_STATE_VERSION = 0
_DECISION_RECORDS: list["DecisionRecord"] = []


class CommitOutcome(str, Enum):
    OK = "OK"
    REFUSED = "REFUSED"
    ESCALATED = "ESCALATED"


@dataclass(slots=True)
class DecisionRecord:
    receipt_id: UUID
    act_id: UUID
    law_key: int
    authority_token_ref: str
    ledger_ref: bytes
    outcome: CommitOutcome
    reason_code: int | None
    timestamp: str
    detail: str = ""


@dataclass(slots=True)
class CommitResult:
    outcome: CommitOutcome
    receipt_id: UUID | None = None
    state_version: int | None = None
    reason_code: int | None = None
    reason_detail: str = ""
    escalation_id: UUID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def register_trusted_producer(producer_id: str) -> None:
    _TRUSTED_PRODUCERS.add(producer_id)


def reset_commit_state_for_tests() -> None:
    global _STATE_VERSION
    _STATE_VERSION = 0
    _DECISION_RECORDS.clear()
    _TRUSTED_PRODUCERS.clear()
    _TRUSTED_PRODUCERS.add("ucr.default")


def get_decision_records() -> tuple[DecisionRecord, ...]:
    return tuple(_DECISION_RECORDS)


def require_sealed_corridors() -> CommitResult | None:
    if not is_sealed() or not is_trust_root_sealed():
        return _refused(ERR_TRUST_ROOT_MISMATCH, "corridor loader or trust root not sealed")
    return None


def cog_act_commit(
    act_id: UUID,
    law_key: int,
    authority_token: bytes,
    act_payload: bytes,
    ledger_ref: bytes,
    metadata: bytes,
) -> CommitResult:
    global _STATE_VERSION

    sealed_error = require_sealed_corridors()
    if sealed_error is not None:
        return sealed_error

    if law_key == 0:
        return _refused(INVALID_LAW_KEY, "law_key must be non-zero")

    if not validate_law_key(law_key).ok:
        return _refused(INVALID_LAW_KEY, "BLK_UCR_V0 validation failed")

    kernel_trust = get_trust_root()
    ucr_context = to_ucr_context(kernel_trust)
    governed_refusal = require_governed_mode(
        ucr_context,
        kernel_trust,
        ucr_law_view=kernel_trust.h_law_spine,
        ucr_corridor_view=kernel_trust.h_corridors,
    )
    if governed_refusal is not None:
        return _refused(governed_refusal.reason_code, governed_refusal.reason_detail)

    if get_registered_ucr_handle() is None:
        return _refused(UCR_NOT_REGISTERED, "UCR instance not registered via ucr_register")

    try:
        envelope = decode_envelope(authority_token)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        return _refused(INVALID_AUTHORITY, f"authority token decode failed: {exc}")

    auth_result = validate_envelope(envelope, syscall_law_key=law_key)
    if not auth_result.ok:
        return _refused(auth_result.reason_code or INVALID_AUTHORITY, auth_result.reason_detail)

    trusted = get_trusted_corridors()
    corridor = next((c for c in trusted.corridors if c.corridor_id == envelope.corridor_id), None)
    if corridor is None:
        return _refused(ERR_CORRIDOR_NOT_FOUND, f"corridor not found: {envelope.corridor_id}")

    ok_corridor, corridor_detail = validate_envelope_against_corridor(envelope, corridor)
    if not ok_corridor:
        return _refused(INVALID_AUTHORITY, corridor_detail)

    try:
        act, admission = deserialize_act_payload(act_payload)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        return _refused(ACT_LEDGER_MISMATCH, f"act payload invalid: {exc}")

    if act.act_id != str(act_id):
        return _refused(ACT_LEDGER_MISMATCH, "act_id mismatch")

    if not ledger_ref_matches(act_payload, ledger_ref):
        return _refused(ACT_LEDGER_MISMATCH, "ledger_ref mismatch")

    if admission.producer_id not in _TRUSTED_PRODUCERS:
        return _refused(UNTRUSTED_PRODUCER, f"untrusted producer: {admission.producer_id}")

    if act.vetoed or admission.vetoed:
        return _refused(SAFETY_VETO, act.veto_reason or "safety veto")

    if admission.uses_tools and not envelope.permissions.allow_tools:
        return _refused(INVALID_AUTHORITY, "tools not permitted by authority envelope")

    if admission.memory_write and not envelope.permissions.allow_memory:
        return _refused(INVALID_AUTHORITY, "memory writes not permitted by authority envelope")

    if not envelope.risk_allows(admission.risk_level):
        return _refused(INVALID_AUTHORITY, "act risk exceeds envelope max_risk")

    _STATE_VERSION += 1
    receipt_id = uuid4()
    record = DecisionRecord(
        receipt_id=receipt_id,
        act_id=act_id,
        law_key=law_key,
        authority_token_ref=str(envelope.envelope_id),
        ledger_ref=ledger_ref,
        outcome=CommitOutcome.OK,
        reason_code=None,
        timestamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        detail=metadata.decode("utf-8", errors="replace")[:200],
    )
    _DECISION_RECORDS.append(record)
    return CommitResult(
        outcome=CommitOutcome.OK,
        receipt_id=receipt_id,
        state_version=_STATE_VERSION,
        metadata={"corridor_id": str(corridor.corridor_id), "corridor_name": corridor.name},
    )


def _refused(reason_code: int, reason_detail: str) -> CommitResult:
    record = DecisionRecord(
        receipt_id=uuid4(),
        act_id=UUID(int=0),
        law_key=0,
        authority_token_ref="",
        ledger_ref=b"",
        outcome=CommitOutcome.REFUSED,
        reason_code=reason_code,
        timestamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        detail=reason_detail,
    )
    _DECISION_RECORDS.append(record)
    return CommitResult(outcome=CommitOutcome.REFUSED, reason_code=reason_code, reason_detail=reason_detail)
