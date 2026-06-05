"""Runtime paths for temporal replay indices."""

from __future__ import annotations

import os
from pathlib import Path


EVENT_VERSION = "aais.temporal_replay_event.v1"
BUNDLE_VERSION = "aais.temporal_replay_bundle.v1"

VALID_SUBJECT_TYPES = frozenset(
    {
        "mission",
        "session",
        "workflow_run",
        "ugr_trace",
        "slingshot_case",
        "jarvis_run",
        "platform_job",
    }
)


def default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[2] / ".runtime"


def timeline_path(subject_type: str, subject_id: str, *, runtime_dir: Path | None = None) -> Path:
    root = runtime_dir or default_runtime_dir()
    safe_type = "".join(c if c.isalnum() or c in "-_" else "_" for c in subject_type)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in subject_id)
    return root / "temporal_replay" / safe_type / safe_id / "timeline.jsonl"


def bridge_audit_path(subject_id: str, *, runtime_dir: Path | None = None) -> Path:
    root = runtime_dir or default_runtime_dir()
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in subject_id)
    return root / "temporal_replay" / "capability_audit" / safe_id / "events.jsonl"
