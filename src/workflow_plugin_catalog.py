"""Workflow bundle catalog from governance registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_workflow_bundles(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "workflow_plugin_bundles.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def list_workflow_bundles(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_workflow_bundles(repo_root=repo_root)
    return list(doc.get("bundles") or [])


def workflow_by_id(workflow_id: str, *, repo_root: Path | None = None) -> dict[str, Any] | None:
    for item in list_workflow_bundles(repo_root=repo_root):
        if str(item.get("workflow_id") or "") == workflow_id:
            return item
    return None


def list_pending_plug_steps(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    """Return workflow steps honestly marked pending_plug when MCP plug is unavailable."""
    pending: list[dict[str, Any]] = []
    for bundle in list_workflow_bundles(repo_root=repo_root):
        workflow_id = str(bundle.get("workflow_id") or "")
        for step in list(bundle.get("steps") or []):
            if str(step.get("status") or "") != "pending_plug":
                continue
            pending.append(
                {
                    "workflow_id": workflow_id,
                    "workflow_label": bundle.get("label"),
                    "step_id": step.get("step_id"),
                    "plug_id": step.get("plug_id"),
                    "mcp_server": step.get("mcp_server"),
                    "status": "pending_plug",
                }
            )
    return pending
