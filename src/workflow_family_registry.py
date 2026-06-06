"""Workflow-family organ registry loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_workflow_families(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "workflow_family_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def list_workflow_families(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_workflow_families(repo_root=repo_root)
    return list(doc.get("families") or [])


def family_by_id(family_id: str, *, repo_root: Path | None = None) -> dict[str, Any] | None:
    for item in list_workflow_families(repo_root=repo_root):
        if str(item.get("identity", {}).get("family_id") or "") == family_id:
            return item
    return None
