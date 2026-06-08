"""Operator civilization charter registry (Mythic Stage 18 / Release 48)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CIVILIZATION_VERSION = "operator_civilization_charter.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_civilization_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_civilization_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_civilizations(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_civilization_registry(repo_root=repo_root)
    return list(doc.get("civilizations") or [])


def save_adopted_civilization(civilization: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_civilization_registry.v1.json"
    doc = load_civilization_registry(repo_root=root)
    civilizations = list(doc.get("civilizations") or [])
    civilization_id = str(civilization.get("civilization_id") or "")
    civilizations = [c for c in civilizations if str(c.get("civilization_id") or "") != civilization_id]
    civilizations.append(civilization)
    doc["civilizations"] = civilizations
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return civilization


def validate_civilization_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_civilization_registry(repo_root=repo_root)
    if doc.get("operator_civilization_registry_version") != "operator_civilization_registry.v1":
        errors.append("invalid operator_civilization_registry_version")
    for civilization in list(doc.get("civilizations") or []):
        cid = str(civilization.get("civilization_id") or "")
        if not cid:
            errors.append("civilization missing civilization_id")
        if civilization.get("civilization_version") != CIVILIZATION_VERSION:
            errors.append(f"invalid civilization_version on {cid}")
        if not civilization.get("operator_promoted"):
            errors.append(f"registry civilization must be operator_promoted: {cid}")
    return errors
