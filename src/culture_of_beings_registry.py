"""Operator culture-of-beings shared norm registry (Stage 11 / Release 42)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

NORM_VERSION = "operator_shared_norm.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_culture_of_beings_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_culture_of_beings_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_norms(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_culture_of_beings_registry(repo_root=repo_root)
    return list(doc.get("norms") or [])


def save_adopted_norm(norm: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_culture_of_beings_registry.v1.json"
    doc = load_culture_of_beings_registry(repo_root=root)
    norms = list(doc.get("norms") or [])
    norm_id = str(norm.get("norm_id") or "")
    norms = [n for n in norms if str(n.get("norm_id") or "") != norm_id]
    norms.append(norm)
    doc["norms"] = norms
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return norm


def validate_culture_of_beings_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_culture_of_beings_registry(repo_root=repo_root)
    if doc.get("operator_culture_of_beings_registry_version") != "operator_culture_of_beings_registry.v1":
        errors.append("invalid operator_culture_of_beings_registry_version")
    for norm in list(doc.get("norms") or []):
        norm_id = str(norm.get("norm_id") or "")
        if not norm_id:
            errors.append("norm missing norm_id")
        if norm.get("norm_version") != NORM_VERSION:
            errors.append(f"invalid norm_version on {norm_id}")
        if not norm.get("operator_promoted"):
            errors.append(f"registry norm must be operator_promoted: {norm_id}")
        kind = str(norm.get("norm_kind") or "")
        if kind not in {
            "handoff_ritual",
            "consent_cadence",
            "dispute_posture",
            "mesh_cluster",
            "exchange_protocol",
            "closure",
        }:
            errors.append(f"invalid norm_kind on {norm_id}")
    return errors
