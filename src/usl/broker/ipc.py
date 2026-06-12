"""IPC message types for guest → broker → gate."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class BrokerMessage:
    """Guest syscall envelope routed through the broker."""

    msg_type: str
    capability_id: str
    ceiling_id: str
    path: str = ""
    payload_b64: str = ""
    guest_process_id: str = "guest-1"
    profile_id: str = "daily-driver"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, raw: str | bytes) -> BrokerMessage:
        data = json.loads(raw)
        return cls(
            msg_type=str(data.get("msg_type", "syscall")),
            capability_id=str(data.get("capability_id", "")),
            ceiling_id=str(data.get("ceiling_id", "fs.basic")),
            path=str(data.get("path", "")),
            payload_b64=str(data.get("payload_b64", "")),
            guest_process_id=str(data.get("guest_process_id", "guest-1")),
            profile_id=str(data.get("profile_id", "daily-driver")),
            extra=dict(data.get("extra") or {}),
        )


@dataclass
class BrokerResponse:
    ok: bool
    decision: str
    transition_id: str = ""
    error: str = ""
    substrate: dict[str, Any] | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, raw: str | bytes) -> BrokerResponse:
        data = json.loads(raw)
        return cls(
            ok=bool(data.get("ok")),
            decision=str(data.get("decision", "")),
            transition_id=str(data.get("transition_id", "")),
            error=str(data.get("error", "")),
            substrate=data.get("substrate"),
        )
