"""AAIS library registry loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_library_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "aais_library_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def list_libraries(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_library_registry(repo_root=repo_root)
    return list(doc.get("libraries") or [])


def library_by_id(library_id: str, *, repo_root: Path | None = None) -> dict[str, Any] | None:
    for item in list_libraries(repo_root=repo_root):
        if str(item.get("identity", {}).get("library_id") or "") == library_id:
            return item
    return None
