from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

KIND_REFLEXIVE_EVAL = "REFLEXIVE_EVAL"
KIND_REFLEXIVE_EPOCH_SUMMARY = "REFLEXIVE_EPOCH_SUMMARY"

_events: list[dict[str, Any]] = []
_hydrated = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_hydrated() -> None:
    global _hydrated
    if _hydrated or _events:
        return
    try:
        from nova.bridges.panel_store import get_panel_store

        stored = get_panel_store().list_reflexive_events()
        if stored:
            _events.extend(stored)
    except Exception:
        pass
    _hydrated = True


def _persist_event(event: dict[str, Any]) -> None:
    try:
        from nova.bridges.panel_store import get_panel_store

        get_panel_store().append_reflexive_event(event)
    except Exception:
        pass


@dataclass
class ReflexiveLineageEvent:
    kind: str
    epoch_id: str
    intent_id: str | None
    lineage_event_id: str
    t5_ref_signal_hash: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now_iso)

    def stable_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "epoch_id": self.epoch_id,
            "intent_id": self.intent_id,
            "lineage_event_id": self.lineage_event_id,
            "t5_ref_signal_hash": self.t5_ref_signal_hash,
            "payload": self.payload,
        }


def emit_reflexive_eval(
    *,
    epoch_id: str,
    intent_id: str,
    lineage_event_id: str,
    t5_ref_signal_hash: str,
    report: dict[str, Any],
) -> ReflexiveLineageEvent:
    event = ReflexiveLineageEvent(
        kind=KIND_REFLEXIVE_EVAL,
        epoch_id=epoch_id,
        intent_id=intent_id,
        lineage_event_id=lineage_event_id,
        t5_ref_signal_hash=t5_ref_signal_hash,
        payload=dict(report),
    )
    row = {**event.stable_dict(), "timestamp": event.timestamp}
    _events.append(row)
    _persist_event(row)
    return event


def emit_reflexive_epoch_summary(
    *,
    epoch_id: str,
    lineage_event_id: str,
    t5_ref_signal_hash: str,
    summary: dict[str, Any],
) -> ReflexiveLineageEvent:
    event = ReflexiveLineageEvent(
        kind=KIND_REFLEXIVE_EPOCH_SUMMARY,
        epoch_id=epoch_id,
        intent_id=None,
        lineage_event_id=lineage_event_id,
        t5_ref_signal_hash=t5_ref_signal_hash,
        payload=dict(summary),
    )
    row = {**event.stable_dict(), "timestamp": event.timestamp}
    _events.append(row)
    _persist_event(row)
    return event


def list_reflexive_events() -> list[dict[str, Any]]:
    _ensure_hydrated()
    return list(_events)


def clear_reflexive_events() -> None:
    global _hydrated
    _events.clear()
    _hydrated = False
    try:
        from nova.bridges.panel_store import get_panel_store

        get_panel_store().clear_reflexive()
    except Exception:
        pass
