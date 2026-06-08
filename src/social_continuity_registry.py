"""Operator social bond registry loader (Stage 9 / Release 40)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BOND_VERSION = "operator_social_bond.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_social_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_social_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_bonds(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_social_registry(repo_root=repo_root)
    return list(doc.get("bonds") or [])


def save_adopted_bond(bond: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_social_registry.v1.json"
    doc = load_social_registry(repo_root=root)
    bonds = list(doc.get("bonds") or [])
    bond_id = str(bond.get("bond_id") or "")
    bonds = [b for b in bonds if str(b.get("bond_id") or "") != bond_id]
    bonds.append(bond)
    doc["bonds"] = bonds
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return bond


def validate_social_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_social_registry(repo_root=repo_root)
    if doc.get("operator_social_registry_version") != "operator_social_registry.v1":
        errors.append("invalid operator_social_registry_version")
    for bond in list(doc.get("bonds") or []):
        bond_id = str(bond.get("bond_id") or "")
        if not bond_id:
            errors.append("bond missing bond_id")
        if bond.get("bond_version") != BOND_VERSION:
            errors.append(f"invalid bond_version on {bond_id}")
        if not bond.get("operator_promoted"):
            errors.append(f"registry bond must be operator_promoted: {bond_id}")
        kind = str(bond.get("bond_kind") or "")
        if kind not in {
            "operator_dyad",
            "federated_peer",
            "organ_collaborator",
            "workflow_counterparty",
            "closure",
        }:
            errors.append(f"invalid bond_kind on {bond_id}")
    return errors
