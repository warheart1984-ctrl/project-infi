"""Build and persist normalized replay timelines."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.temporal_replay.event import payload_hash, sort_events, summarize_event
from src.temporal_replay.ingestors import ingest_subject
from src.temporal_replay.paths import timeline_path, VALID_SUBJECT_TYPES


def build_timeline(
    subject_type: str,
    subject_id: str,
    *,
    runtime_dir: Path | None = None,
    tenant_id: str | None = None,
    workflow_run: dict[str, Any] | None = None,
    rebuild: bool = False,
) -> dict[str, Any]:
    if subject_type not in VALID_SUBJECT_TYPES:
        raise ValueError(f"unsupported subject_type: {subject_type}")
    sid = str(subject_id or "").strip()
    if not sid:
        raise ValueError("subject_id required")

    path = timeline_path(subject_type, sid, runtime_dir=runtime_dir)
    if path.is_file() and not rebuild:
        events = _load_timeline(path)
    else:
        events = ingest_subject(
            subject_type,
            sid,
            runtime_dir=runtime_dir,
            tenant_id=tenant_id,
            workflow_run=workflow_run,
        )
        _persist_timeline(path, events)

    events = sort_events(events)
    return {
        "subject_type": subject_type,
        "subject_id": sid,
        "event_count": len(events),
        "timeline_path": str(path),
        "timeline_hash": payload_hash(events) if events else payload_hash([]),
        "events": events,
        "summaries": [summarize_event(e) for e in events],
        "coverage_notes": _coverage_notes(subject_type, events),
        "runtime_effect": "readout_only",
    }


def _coverage_notes(subject_type: str, events: list[dict[str, Any]]) -> list[str]:
    notes: list[str] = []
    kinds = {e.get("kind") for e in events}
    if subject_type == "mission" and "mission_receipt" not in kinds:
        notes.append("no_mission_receipt_indexed")
    if subject_type == "session" and "capability_audit" not in kinds:
        notes.append("capability_audit_partial_or_missing")
    if not events:
        notes.append("empty_timeline")
    return notes


def _load_timeline(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _persist_timeline(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")
