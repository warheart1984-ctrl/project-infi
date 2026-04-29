"""Structured seam capture for AAIS runtime-law enforcement.

AAIS Runtime Law -- Seam Capture:
Every detected seam, anomaly, or boundary violation must be recorded as a
structured seam event and appended to the seam log.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import threading
from typing import Any
import uuid


SEAM_CAPTURE_LAW = "AAIS Runtime Law -- Seam Capture"
SEAM_EVENT_LIMIT = 500
SEAM_CLASSIFICATIONS = {"seam", "anomaly", "boundary_violation"}
SEAM_SEVERITIES = {"low", "medium", "high", "critical"}
_RUNTIME_SUFFIXES = {"module-governance", "governance", "immune-system", "seams"}
_LOCK = threading.Lock()


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _clip_text(value: Any, *, limit: int = 280) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_runtime_root(runtime_dir: str | Path | None) -> Path:
    base = Path(runtime_dir).expanduser() if runtime_dir is not None else _default_runtime_dir()
    while base.name in _RUNTIME_SUFFIXES:
        base = base.parent
    return base


def _events_path(runtime_dir: str | Path | None = None) -> Path:
    return _normalize_runtime_root(runtime_dir) / "seams" / "seam-events.jsonl"


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return _clip_text(value, limit=200)


def record_seam_event(
    *,
    classification: str,
    source: str,
    boundary: str,
    reason: Any,
    details: dict[str, Any] | None = None,
    severity: str | None = None,
    decision: str | None = None,
    vector: str | None = None,
    component_id: str | None = None,
    runtime_context: str | None = None,
    trace_id: str | None = None,
    event_type: str | None = None,
    runtime_dir: str | Path | None = None,
) -> dict[str, Any]:
    normalized_classification = str(classification or "seam").strip().lower()
    if normalized_classification not in SEAM_CLASSIFICATIONS:
        normalized_classification = "seam"

    normalized_severity = str(severity or "medium").strip().lower()
    if normalized_severity not in SEAM_SEVERITIES:
        normalized_severity = "medium"

    event = {
        "event_id": f"seam-{uuid.uuid4().hex}",
        "timestamp": _utc_now_iso(),
        "law": SEAM_CAPTURE_LAW,
        "classification": normalized_classification,
        "event_type": _clip_text(event_type or normalized_classification, limit=80).lower().replace(" ", "_"),
        "source": _clip_text(source or "runtime", limit=120).lower().replace(" ", "_"),
        "boundary": _clip_text(boundary or "runtime_boundary", limit=120).lower().replace(" ", "_"),
        "severity": normalized_severity,
        "decision": _clip_text(decision, limit=80).upper() or None,
        "vector": _clip_text(vector, limit=80).lower().replace(" ", "_") or None,
        "component_id": _clip_text(component_id, limit=160) or None,
        "runtime_context": _clip_text(runtime_context, limit=80).lower().replace(" ", "_") or None,
        "trace_id": _clip_text(trace_id, limit=160) or None,
        "reason": _clip_text(reason, limit=280) or normalized_classification,
        "details": _json_safe(details or {}),
    }

    path = _events_path(runtime_dir)
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        existing: list[str] = []
        if path.exists():
            existing = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        existing.append(json.dumps(event, ensure_ascii=True))
        if len(existing) > SEAM_EVENT_LIMIT:
            existing = existing[-SEAM_EVENT_LIMIT:]
        path.write_text("\n".join(existing) + ("\n" if existing else ""), encoding="utf-8")
    return event


def list_seam_events(*, runtime_dir: str | Path | None = None, limit: int = 50) -> list[dict[str, Any]]:
    normalized_limit = max(1, min(int(limit or 50), SEAM_EVENT_LIMIT))
    path = _events_path(runtime_dir)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events[-normalized_limit:]


def reset_seam_log(*, runtime_dir: str | Path | None = None) -> None:
    path = _events_path(runtime_dir)
    with _LOCK:
        if path.exists():
            path.unlink()
