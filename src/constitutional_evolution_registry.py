"""Operator charter amendment registry (Mythic Stage 17 / Release 47)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

AMENDMENT_VERSION = "operator_charter_amendment.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_evolution_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_constitutional_evolution_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_amendments(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_evolution_registry(repo_root=repo_root)
    return list(doc.get("amendments") or [])


def save_adopted_amendment(amendment: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_constitutional_evolution_registry.v1.json"
    doc = load_evolution_registry(repo_root=root)
    amendments = list(doc.get("amendments") or [])
    amendment_id = str(amendment.get("amendment_id") or "")
    amendments = [a for a in amendments if str(a.get("amendment_id") or "") != amendment_id]
    amendments.append(amendment)
    doc["amendments"] = amendments
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return amendment


def validate_evolution_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_evolution_registry(repo_root=repo_root)
    if doc.get("operator_constitutional_evolution_registry_version") != "operator_constitutional_evolution_registry.v1":
        errors.append("invalid operator_constitutional_evolution_registry_version")
    for amendment in list(doc.get("amendments") or []):
        aid = str(amendment.get("amendment_id") or "")
        if not aid:
            errors.append("amendment missing amendment_id")
        if amendment.get("amendment_version") != AMENDMENT_VERSION:
            errors.append(f"invalid amendment_version on {aid}")
        if not amendment.get("operator_promoted"):
            errors.append(f"registry amendment must be operator_promoted: {aid}")
    return errors
