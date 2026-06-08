"""Operator constitutional ecosystem charter registry (Stage 12 / Release 43)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CHARTER_VERSION = "operator_ecosystem_charter.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_ecosystem_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_ecosystem_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_charters(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_ecosystem_registry(repo_root=repo_root)
    return list(doc.get("charters") or [])


def save_adopted_charter(charter: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_ecosystem_registry.v1.json"
    doc = load_ecosystem_registry(repo_root=root)
    charters = list(doc.get("charters") or [])
    charter_id = str(charter.get("charter_id") or "")
    charters = [c for c in charters if str(c.get("charter_id") or "") != charter_id]
    charters.append(charter)
    doc["charters"] = charters
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return charter


def validate_ecosystem_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_ecosystem_registry(repo_root=repo_root)
    if doc.get("operator_ecosystem_registry_version") != "operator_ecosystem_registry.v1":
        errors.append("invalid operator_ecosystem_registry_version")
    for charter in list(doc.get("charters") or []):
        cid = str(charter.get("charter_id") or "")
        if not cid:
            errors.append("charter missing charter_id")
        if charter.get("charter_version") != CHARTER_VERSION:
            errors.append(f"invalid charter_version on {cid}")
        if not charter.get("operator_promoted"):
            errors.append(f"registry charter must be operator_promoted: {cid}")
        if len(list(charter.get("admitted_pact_ids") or [])) < 2:
            errors.append(f"charter requires >=2 admitted_pact_ids: {cid}")
    return errors
