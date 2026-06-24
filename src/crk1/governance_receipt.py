"""CRK-1 governance receipt builder — signed validation records."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.crk1.runtime_validator import CRK1RuntimeValidator


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class GovernanceReceipt:
    action_id: str
    action_type: str
    identity: str
    timestamp: str
    from_state: str
    to_state: str
    transition_ok: bool
    k0_status: str
    k1_status: str
    k2_status: str
    k3_status: str
    ancestors: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    outcome_id: str | None = None
    evidence_id: str | None = None
    replay_hash: str | None = None
    continuity_status: str = "PRESERVED"
    signature: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "identity": self.identity,
            "timestamp": self.timestamp,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "transition_ok": self.transition_ok,
            "k0_status": self.k0_status,
            "k1_status": self.k1_status,
            "k2_status": self.k2_status,
            "k3_status": self.k3_status,
            "ancestors": list(self.ancestors),
            "evidence_ids": list(self.evidence_ids),
            "outcome_id": self.outcome_id,
            "evidence_id": self.evidence_id,
            "replay_hash": self.replay_hash,
            "continuity_status": self.continuity_status,
            "signature": self.signature,
            "error": self.error,
        }

    def render(self) -> str:
        lines = [
            "CRK-1 Governance Receipt",
            "",
            f"Action ID:        {self.action_id}",
            f"Action Type:      {self.action_type}",
            f"Submitted By:     {self.identity}",
            f"Timestamp:        {self.timestamp}",
            "",
            "State Transition:",
            f"From:           {self.from_state}",
            f"To:             {self.to_state}",
            f"Transition OK:  {'PASS' if self.transition_ok else 'FAIL'}",
            "",
            "Invariant Checks:",
            f"K0:             {self.k0_status}",
            f"K1:             {self.k1_status}",
            f"K2:             {self.k2_status}",
            f"K3:             {self.k3_status}",
            "",
            "Lineage:",
            f"Identity:       {self.identity}",
            f"Ancestors:      {self.ancestors}",
            f"Evidence Used:  {self.evidence_ids}",
            "",
            "Replay:",
            f"Outcome ID:     {self.outcome_id or '—'}",
            f"Evidence ID:    {self.evidence_id or '—'}",
            f"Replay Hash:    {self.replay_hash or '—'}",
            "",
            "Continuity:",
            f"Status:         {self.continuity_status}",
            "",
            "Signature:",
            self.signature or "—",
        ]
        if self.error:
            lines.extend(["", f"Error: {self.error}"])
        return "\n".join(lines)


def _sign(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"0x{digest[:8].upper()}...{digest[-4:].upper()}"


def issue_receipt(
    validator: CRK1RuntimeValidator,
    context: dict[str, Any],
    *,
    action_type: str = "ExecuteDecision",
    ancestors: Sequence[str] | None = None,
) -> GovernanceReceipt:
    identity = context.get("identity")
    identity_label = str(getattr(identity, "id", identity) or "unknown")
    decision = context.get("decision")
    evidence_ids = list(getattr(decision, "input_evidence_ids", None) or getattr(decision, "evidence_refs", []) or [])

    receipt = GovernanceReceipt(
        action_id=str(context.get("action_id") or uuid.uuid4().hex[:8]),
        action_type=action_type,
        identity=identity_label,
        timestamp=str(context.get("timestamp") or _now_iso()),
        from_state=str(context["from_state"]),
        to_state=str(context["to_state"]),
        transition_ok=True,
        k0_status="PASS",
        k1_status="PASS",
        k2_status="PASS",
        k3_status="PASS",
        ancestors=list(ancestors or validator.lineage_resolver(identity)),
        evidence_ids=evidence_ids,
        outcome_id=getattr(context.get("outcome"), "id", None),
        evidence_id=getattr(context.get("evidence"), "id", None),
    )

    try:
        validator.validate(context)
    except Exception as exc:  # noqa: BLE001 — receipt captures constitutional failures
        receipt.transition_ok = False
        receipt.continuity_status = "BREACHED"
        receipt.error = str(exc)
        message = str(exc)
        if message.startswith("K0"):
            receipt.k0_status = "FAIL"
        elif message.startswith("K1"):
            receipt.k1_status = "FAIL"
        elif message.startswith("K2"):
            receipt.k2_status = "FAIL"
        elif message.startswith("K3"):
            receipt.k3_status = "FAIL"
        elif "transition" in message.lower() or "Transition" in message:
            receipt.transition_ok = False
        receipt.signature = _sign({**receipt.to_dict(), "valid": False})
        return receipt

    if receipt.outcome_id and receipt.evidence_id:
        receipt.replay_hash = CRK1RuntimeValidator.replay_hash(
            receipt.outcome_id,
            receipt.evidence_id,
        )

    receipt.signature = _sign({**receipt.to_dict(), "valid": True})
    return receipt
