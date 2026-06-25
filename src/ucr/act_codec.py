"""Serialize/deserialize UnifiedCognitiveAct for kernel commit."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from src.ucr.corridor import CognitiveActAdmission
from src.ucr.types import UnifiedCognitiveAct


def serialize_act_payload(
    act: UnifiedCognitiveAct,
    *,
    risk_level: str = "low",
    producer_id: str = "ucr.default",
    required_scopes: list[str] | None = None,
    uses_tools: bool = False,
    memory_write: bool = False,
    ledger_ref: bytes = b"",
) -> bytes:
    payload: dict[str, Any] = {
        "act_id": act.act_id,
        "turn_id": act.turn_id,
        "contract_id": act.contract_id,
        "status": act.status,
        "merged_payload": dict(act.merged_payload),
        "vetoed": act.vetoed,
        "veto_reason": act.veto_reason,
        "risk_level": risk_level,
        "producer_id": producer_id,
        "required_scopes": list(required_scopes or []),
        "uses_tools": uses_tools,
        "memory_write": memory_write,
        "ledger_ref": ledger_ref.hex(),
    }
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def deserialize_act_payload(act_payload: bytes) -> tuple[UnifiedCognitiveAct, CognitiveActAdmission]:
    data = json.loads(act_payload.decode("utf-8"))
    act = UnifiedCognitiveAct(
        act_id=data["act_id"],
        turn_id=data["turn_id"],
        contract_id=data["contract_id"],
        status=data["status"],
        merged_payload=dict(data.get("merged_payload") or {}),
        vetoed=bool(data.get("vetoed")),
        veto_reason=data.get("veto_reason"),
    )
    ledger_ref = bytes.fromhex(data.get("ledger_ref") or "")
    admission = CognitiveActAdmission(
        act_id=act.act_id,
        risk_level=str(data.get("risk_level") or "low"),
        required_scopes=list(data.get("required_scopes") or []),
        uses_tools=bool(data.get("uses_tools")),
        memory_write=bool(data.get("memory_write")),
        producer_id=str(data.get("producer_id") or "ucr.default"),
        vetoed=act.vetoed,
        ledger_ref=ledger_ref,
    )
    return act, admission


def ledger_ref_matches(act_payload: bytes, ledger_ref: bytes) -> bool:
    _, admission = deserialize_act_payload(act_payload)
    return admission.ledger_ref == ledger_ref
