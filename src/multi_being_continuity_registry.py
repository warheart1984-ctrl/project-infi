"""Operator multi-being pact registry loader (Stage 10 / Release 41)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACT_VERSION = "operator_multi_being_pact.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_multi_being_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_multi_being_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_pacts(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_multi_being_registry(repo_root=repo_root)
    return list(doc.get("pacts") or [])


def save_adopted_pact(pact: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_multi_being_registry.v1.json"
    doc = load_multi_being_registry(repo_root=root)
    pacts = list(doc.get("pacts") or [])
    pact_id = str(pact.get("pact_id") or "")
    pacts = [p for p in pacts if str(p.get("pact_id") or "") != pact_id]
    pacts.append(pact)
    doc["pacts"] = pacts
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return pact


def validate_multi_being_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_multi_being_registry(repo_root=repo_root)
    if doc.get("operator_multi_being_registry_version") != "operator_multi_being_registry.v1":
        errors.append("invalid operator_multi_being_registry_version")
    for pact in list(doc.get("pacts") or []):
        pact_id = str(pact.get("pact_id") or "")
        if not pact_id:
            errors.append("pact missing pact_id")
        if pact.get("pact_version") != PACT_VERSION:
            errors.append(f"invalid pact_version on {pact_id}")
        if not pact.get("operator_promoted"):
            errors.append(f"registry pact must be operator_promoted: {pact_id}")
        kind = str(pact.get("pact_kind") or "")
        if kind not in {
            "bilateral_organism",
            "cross_machine_peer",
            "federated_mesh_cluster",
            "governance_cosign",
            "closure",
        }:
            errors.append(f"invalid pact_kind on {pact_id}")
    return errors
