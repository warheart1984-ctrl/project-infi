from __future__ import annotations

from typing import Any


def format_visual_recall_lines(payload: dict[str, Any] | None) -> list[str]:
    summary = dict(payload or {})
    if not summary.get("triggered"):
        return []
    artifact_ids = ", ".join(summary.get("artifact_ids", [])) or "none"
    hooks = ", ".join(summary.get("hooks", [])) or "none"
    context = str(summary.get("context", "") or "eligible artifact match")
    return [
        "[Visual Recall Triggered]",
        f"Artifacts: {artifact_ids}",
        f"Hooks: {hooks}",
        f"Context: {context}",
    ]


def format_visual_artifact_line(payload: dict[str, Any] | None) -> str | None:
    summary = dict(payload or {})
    if not summary.get("stored"):
        return None
    artifact_id = str(summary.get("artifact_id", "")).strip()
    if not artifact_id:
        return None
    return f"[Visual Artifact Stored] {artifact_id}"
