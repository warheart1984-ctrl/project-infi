"""Runtime path helpers for temporal replay and operator ledger stores."""

from __future__ import annotations

import os
from pathlib import Path

REPLAY_SUBJECT_TYPES = frozenset(
    {
        "mission",
        "session",
        "workflow_run",
        "ugr_trace",
        "slingshot_case",
        "jarvis_run",
        "operator_session",
        "platform_job",
    }
)


def default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[2] / ".runtime"


def operator_ledger_path(scope_id: str, *, runtime_dir: Path | None = None) -> Path:
    root = runtime_dir or default_runtime_dir()
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in scope_id)
    return root / "operator_ledger" / safe_id / "events.jsonl"


def operator_ledger_index_path(scope_id: str, *, runtime_dir: Path | None = None) -> Path:
    root = runtime_dir or default_runtime_dir()
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in scope_id)
    return root / "operator_ledger" / safe_id / "graph_index.json"


def bridge_audit_path(subject_id: str, *, runtime_dir: Path | None = None) -> Path:
    root = runtime_dir or default_runtime_dir()
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in subject_id)
    return root / "temporal_replay" / "capability_audit" / safe_id / "events.jsonl"
