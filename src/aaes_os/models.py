"""AAES-OS v1.0 typed records."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any
from uuid import uuid4

from src.aaes_os.types import EventType, Role, SpanState


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class AuthEnvelope:
    role: Role
    actor_id: str
    signature_hash: str

    def validate(self) -> None:
        if not str(self.actor_id or "").strip():
            raise ValueError("actor_id is required")
        if not str(self.signature_hash or "").strip():
            raise ValueError("signature_hash is required")


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    runtime_version: str
    invariant_version: str
    prompt_hash: str
    decision_policy_hash: str
    toolchain_hash: str
    memory_snapshot_hash: str

    def validate(self) -> None:
        for name in (
            "runtime_version",
            "invariant_version",
            "prompt_hash",
            "decision_policy_hash",
            "toolchain_hash",
            "memory_snapshot_hash",
        ):
            if not str(getattr(self, name) or "").strip():
                raise ValueError(f"{name} is required")

    def as_dict(self) -> dict[str, str]:
        return {
            "runtime_version": self.runtime_version,
            "invariant_version": self.invariant_version,
            "prompt_hash": self.prompt_hash,
            "decision_policy_hash": self.decision_policy_hash,
            "toolchain_hash": self.toolchain_hash,
            "memory_snapshot_hash": self.memory_snapshot_hash,
        }


@dataclass(slots=True)
class TraceEvent:
    span_id: str
    event_type: EventType
    auth: AuthEnvelope
    runtime_context: RuntimeContext
    payload: dict[str, Any] = field(default_factory=dict)
    parent_event_id: str | None = None
    parent_span_id: str | None = None
    event_id: str = ""
    timestamp_utc: str = ""
    event_hash: str = ""

    def __post_init__(self) -> None:
        if not str(self.span_id or "").strip():
            raise ValueError("span_id is required")
        if not self.event_id:
            self.event_id = f"aaes_{uuid4().hex}"
        if not self.timestamp_utc:
            self.timestamp_utc = _utc_now_iso()
        body = self.canonical_body()
        digest = sha256(_stable_json(body).encode("utf-8")).hexdigest()
        if not self.event_hash:
            self.event_hash = digest
        elif self.event_hash != digest:
            raise ValueError("event_hash does not match canonical body")

    def canonical_body(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "span_id": self.span_id,
            "event_type": self.event_type.value,
            "timestamp_utc": self.timestamp_utc,
            "auth": {
                "role": self.auth.role.value,
                "actor_id": self.auth.actor_id,
                "signature_hash": self.auth.signature_hash,
            },
            "runtime_context": self.runtime_context.as_dict(),
            "payload": dict(self.payload),
            "parent_event_id": self.parent_event_id,
            "parent_span_id": self.parent_span_id,
        }

    def as_dict(self) -> dict[str, Any]:
        row = self.canonical_body()
        row["event_hash"] = self.event_hash
        return row


@dataclass(frozen=True, slots=True)
class ReconstructedSpan:
    span_id: str
    state: SpanState
    events: tuple[TraceEvent, ...]
    runtime_context: RuntimeContext
