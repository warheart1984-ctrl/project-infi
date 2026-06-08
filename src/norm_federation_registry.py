"""Operator norm federation treaty registry (Mythic Stage 16 / Release 46)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TREATY_VERSION = "operator_norm_federation_treaty.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_norm_federation_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_norm_federation_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_treaties(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_norm_federation_registry(repo_root=repo_root)
    return list(doc.get("treaties") or [])


def save_adopted_treaty(treaty: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_norm_federation_registry.v1.json"
    doc = load_norm_federation_registry(repo_root=root)
    treaties = list(doc.get("treaties") or [])
    treaty_id = str(treaty.get("treaty_id") or "")
    treaties = [t for t in treaties if str(t.get("treaty_id") or "") != treaty_id]
    treaties.append(treaty)
    doc["treaties"] = treaties
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return treaty


def validate_norm_federation_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_norm_federation_registry(repo_root=repo_root)
    if doc.get("operator_norm_federation_registry_version") != "operator_norm_federation_registry.v1":
        errors.append("invalid operator_norm_federation_registry_version")
    for treaty in list(doc.get("treaties") or []):
        tid = str(treaty.get("treaty_id") or "")
        if not tid:
            errors.append("treaty missing treaty_id")
        if treaty.get("treaty_version") != TREATY_VERSION:
            errors.append(f"invalid treaty_version on {tid}")
        if not treaty.get("operator_promoted"):
            errors.append(f"registry treaty must be operator_promoted: {tid}")
    return errors
