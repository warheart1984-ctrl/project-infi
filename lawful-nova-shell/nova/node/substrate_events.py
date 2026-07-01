from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal
import time
from uuid import uuid4

from fastapi import APIRouter, Query

from nova.node.ledger import append_jsonl, read_jsonl, runtime_dir


SCHEMA_VERSION = "substrate-event-v1"
router = APIRouter()


IntentSource = Literal["USER", "AGENT", "SYSTEM"]
CausalKind = Literal["DERIVED", "FORK", "MERGE", "EMIT"]


@dataclass(frozen=True)
class IntentRef:
    intentId: str
    source: IntentSource


@dataclass(frozen=True)
class SubstrateEvent:
    eventId: str
    timestamp: int
    type: str
    kernel: str
    payload: dict[str, Any]
    sequence: int | None = None
    sessionId: str | None = None
    threadId: str | None = None
    streamId: str | None = None
    intent: IntentRef | None = None
    parentEventIds: list[str] = field(default_factory=list)
    causalKind: CausalKind | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.intent is not None:
            payload["intent"] = asdict(self.intent)
        return {key: value for key, value in payload.items() if value not in (None, [], {})}


def substrate_event_log_path():
    return runtime_dir() / "substrate-events.jsonl"


def make_substrate_event(
    *,
    type_: str,
    kernel: str,
    payload: dict[str, Any],
    stream_id: str | None = None,
    intent: dict[str, str] | IntentRef | None = None,
    session_id: str | None = None,
    thread_id: str | None = None,
    parent_event_ids: list[str] | None = None,
    causal_kind: CausalKind | None = "EMIT",
    metadata: dict[str, Any] | None = None,
) -> SubstrateEvent:
    sequence = len(read_jsonl(substrate_event_log_path())) + 1
    event_metadata = {"schemaVersion": SCHEMA_VERSION}
    event_metadata.update(metadata or {})
    return SubstrateEvent(
        eventId="evt_" + uuid4().hex[:16],
        timestamp=int(time.time() * 1000),
        sequence=sequence,
        type=type_,
        kernel=kernel,
        sessionId=session_id,
        threadId=thread_id,
        streamId=stream_id,
        intent=_intent_ref(intent),
        parentEventIds=list(parent_event_ids or []),
        causalKind=causal_kind,
        payload={**payload, "type": payload.get("type") or type_},
        metadata=event_metadata,
    )


def append_substrate_event(event: SubstrateEvent) -> dict[str, Any]:
    return append_jsonl(substrate_event_log_path(), event.to_dict())


def read_substrate_events(
    *,
    stream_id: str | None = None,
    type_: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    events = read_jsonl(substrate_event_log_path())
    if stream_id:
        events = [event for event in events if event.get("streamId") == stream_id]
    if type_:
        events = [event for event in events if event.get("type") == type_]
    if limit is not None:
        events = events[-limit:]
    return events


@router.get("/node/substrate-events")
async def get_substrate_events(
    stream_id: str | None = None,
    type_: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "canonical": "jsonl",
        "events": read_substrate_events(stream_id=stream_id, type_=type_, limit=limit),
    }


def legacy_event_to_substrate(event: Any) -> SubstrateEvent | None:
    channel = str(getattr(event, "channel", ""))
    payload = dict(getattr(event, "payload", {}) or {})
    trace_id = str(payload.get("trace_id") or payload.get("intent_id") or "").strip()
    intent = {"intentId": trace_id, "source": "AGENT"} if trace_id else None
    legacy_metadata = {"extensions": {"legacyEventId": getattr(event, "id", "")}}

    if channel == "tool.invoked":
        tool_name = str(payload.get("tool_name") or "unknown")
        return make_substrate_event(
            type_="Capability.Invoked",
            kernel="UL",
            stream_id=f"capability:{tool_name}",
            intent=intent,
            payload={
                "name": tool_name,
                "capabilityKind": _capability_kind(tool_name),
                "riskLevel": _risk_level(tool_name),
                "args": {
                    "argsHash": payload.get("args_hash"),
                    "governedState": payload.get("governed_state"),
                },
            },
            metadata={
                **legacy_metadata,
                "governanceDecision": {
                    "decisionId": trace_id or "unknown",
                    "result": _governance_result(str(payload.get("governed_state") or "")),
                    "invariantsChecked": [],
                    "violations": [],
                },
            },
        )

    if channel == "tool.completed":
        tool_name = str(payload.get("tool_name") or "unknown")
        parent = _last_event_id_for_trace(trace_id)
        return make_substrate_event(
            type_="Capability.Completed",
            kernel="UL",
            stream_id=f"capability:{tool_name}",
            intent=intent,
            parent_event_ids=[parent] if parent else [],
            causal_kind="DERIVED",
            payload={
                "name": tool_name,
                "result": {
                    "outputHash": payload.get("output_hash"),
                    "durationMs": payload.get("duration_ms"),
                },
                "receiptId": trace_id or None,
            },
            metadata=legacy_metadata,
        )

    if channel in {"governance.receipt_verified", "governance.receipt_blocked"}:
        blocked = channel.endswith("blocked")
        return make_substrate_event(
            type_="Governance.Decision",
            kernel="CKCE-1",
            stream_id="governance",
            intent=intent,
            causal_kind="DERIVED",
            payload={
                "decisionId": trace_id or str(payload.get("receipt_hash") or "unknown"),
                "result": "BLOCKED" if blocked else "ALLOWED",
                "invariantsChecked": [str(payload.get("policy_version") or "policy")],
                "violations": [payload.get("reason")] if payload.get("reason") else [],
                "appliesToEventId": _last_event_id_for_trace(trace_id),
            },
            metadata=legacy_metadata,
        )

    if channel == "governance.patch_generated":
        return make_substrate_event(
            type_="Receipt.Created",
            kernel="Governance",
            stream_id="governance",
            intent=intent,
            causal_kind="DERIVED",
            payload={
                "receiptId": trace_id or str(payload.get("diff_hash") or "patch"),
                "hash": str(payload.get("diff_hash") or ""),
                "status": "PENDING",
                "filePath": payload.get("file_path"),
            },
            metadata=legacy_metadata,
        )

    if channel.startswith("replay."):
        return make_substrate_event(
            type_="Replay.State",
            kernel="Continuity",
            stream_id="replay",
            intent=intent,
            payload={
                "mode": "REPLAY",
                "currentIndex": len(read_jsonl(substrate_event_log_path())),
                "metrics": payload,
            },
            metadata=legacy_metadata,
        )

    if channel.startswith("node."):
        status = "IDLE"
        if channel == "node.offline":
            status = "ERROR"
        return make_substrate_event(
            type_="Nova.StatusChanged",
            kernel="Governance",
            stream_id="status",
            payload={"status": status, "detail": channel},
            metadata=legacy_metadata,
        )

    return None


_TRACE_LAST_EVENTS: dict[str, str] = {}


def remember_trace_event(event: dict[str, Any]) -> None:
    intent = event.get("intent") or {}
    trace_id = str(intent.get("intentId") or "")
    if trace_id:
        _TRACE_LAST_EVENTS[trace_id] = str(event.get("eventId") or "")


def _last_event_id_for_trace(trace_id: str) -> str | None:
    if not trace_id:
        return None
    return _TRACE_LAST_EVENTS.get(trace_id)


def _intent_ref(intent: dict[str, str] | IntentRef | None) -> IntentRef | None:
    if intent is None or isinstance(intent, IntentRef):
        return intent
    return IntentRef(intentId=str(intent["intentId"]), source=str(intent.get("source") or "AGENT"))  # type: ignore[arg-type]


def _capability_kind(tool_name: str) -> str:
    if tool_name in {"code", "wire", "explain"}:
        return "MODEL_CALL"
    return "SYSTEM"


def _risk_level(tool_name: str) -> str:
    if tool_name == "wire":
        return "HIGH"
    if tool_name in {"code", "explain"}:
        return "MEDIUM"
    return "LOW"


def _governance_result(value: str) -> str:
    normalized = value.upper()
    if normalized == "ALLOWED":
        return "ALLOWED"
    if normalized == "BLOCKED":
        return "BLOCKED"
    return "CONSTRAINED"
