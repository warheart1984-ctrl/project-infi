"""Temporal replay timeline assembly and verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.temporal_replay.event import TEMPORAL_REPLAY_EVENT_VERSION
from src.temporal_replay.ingestors import ingest_subject
from src.temporal_replay.paths import REPLAY_SUBJECT_TYPES, default_runtime_dir


def build_timeline(
    subject_type: str,
    subject_id: str,
    *,
    runtime_dir: Path | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Build ordered temporal replay timeline for a subject."""
    normalized_type = str(subject_type or "").strip()
    normalized_id = str(subject_id or "").strip()
    if normalized_type not in REPLAY_SUBJECT_TYPES:
        return {
            "temporal_replay_version": TEMPORAL_REPLAY_EVENT_VERSION,
            "subject_type": normalized_type,
            "subject_id": normalized_id,
            "events": [],
            "event_count": 0,
            "error": "unsupported subject_type",
        }
    events = ingest_subject(
        normalized_type,
        normalized_id,
        runtime_dir=runtime_dir or default_runtime_dir(),
        tenant_id=tenant_id,
    )
    events.sort(key=lambda item: (int(item.get("sequence") or 0), str(item.get("timestamp_utc") or "")))
    return {
        "temporal_replay_version": TEMPORAL_REPLAY_EVENT_VERSION,
        "subject_type": normalized_type,
        "subject_id": normalized_id,
        "events": events,
        "event_count": len(events),
    }


def verify_timeline(timeline: dict[str, Any]) -> dict[str, Any]:
    """Verify monotonic sequence and required envelope fields."""
    events = list(timeline.get("events") or [])
    errors: list[str] = []
    prev_seq = -1
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"row {index}: not an object")
            continue
        for key in ("event_id", "subject_type", "subject_id", "kind", "sequence"):
            if key not in event:
                errors.append(f"row {index}: missing {key}")
        raw_seq = event.get("sequence")
        seq = int(raw_seq) if raw_seq is not None else -1
        if seq <= prev_seq:
            errors.append(f"row {index}: non-monotonic sequence")
        prev_seq = seq
    return {
        "valid": not errors,
        "event_count": len(events),
        "errors": errors[:12],
    }


def get_replay_state(
    subject_type: str,
    subject_id: str,
    *,
    runtime_dir: Path | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Return lightweight replay state summary."""
    timeline = build_timeline(
        subject_type,
        subject_id,
        runtime_dir=runtime_dir,
        tenant_id=tenant_id,
    )
    verify = verify_timeline(timeline)
    kinds: dict[str, int] = {}
    for event in timeline.get("events") or []:
        kind = str(event.get("kind") or "unknown")
        kinds[kind] = kinds.get(kind, 0) + 1
    return {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "event_count": timeline.get("event_count", 0),
        "kind_counts": kinds,
        "verify": verify,
    }
