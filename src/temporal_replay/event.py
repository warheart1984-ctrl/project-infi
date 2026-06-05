"""Canonical temporal replay event model."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from src.temporal_replay.paths import EVENT_VERSION


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def payload_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def new_event_id(kind: str, subject_id: str, sequence: int) -> str:
    material = f"{kind}:{subject_id}:{sequence}:{uuid.uuid4().hex[:8]}"
    return f"tre-{hashlib.sha256(material.encode()).hexdigest()[:20]}"


def normalize_event(raw: dict[str, Any]) -> dict[str, Any]:
    event = dict(raw)
    event.setdefault("event_version", EVENT_VERSION)
    event.setdefault("causal_parents", [])
    event.setdefault("emitter", {})
    event.setdefault("law_context", {})
    event.setdefault("boundary", {})
    return event


def summarize_event(event: dict[str, Any]) -> dict[str, Any]:
    from src.temporal_replay.emitter_registry import jump_target

    emitter = dict(event.get("emitter") or {})
    law = dict(event.get("law_context") or {})
    boundary = dict(event.get("boundary") or {})
    flags = dict(event.get("invariant_flags") or {})
    jump = jump_target(emitter)
    return {
        "event_id": event.get("event_id"),
        "timestamp_utc": event.get("timestamp_utc"),
        "sequence": event.get("sequence"),
        "kind": event.get("kind"),
        "summary": event.get("summary"),
        "subsystem_id": emitter.get("subsystem_id"),
        "emitter_module": emitter.get("module"),
        "genome_ref": emitter.get("genome_ref"),
        "jump_target": jump,
        "hard_fail": bool(flags.get("hard_fail")),
        "invariant_codes": list(flags.get("codes") or []),
        "law_version": law.get("law_version"),
        "invariant_version": law.get("invariant_version"),
        "tenant_id": boundary.get("tenant_id"),
    }


def sort_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def _key(row: dict[str, Any]) -> tuple[str, int]:
        return (str(row.get("timestamp_utc") or ""), int(row.get("sequence") or 0))

    return sorted(events, key=_key)
