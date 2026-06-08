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


def handoffs_for(family_id: str, *, repo_root: Path | None = None) -> list[dict[str, Any]]:
    family = family_by_id(family_id, repo_root=repo_root)
    if not family:
        return []
    rows: list[dict[str, Any]] = []
    for handoff in list(family.get("handoffs") or []):
        row = dict(handoff)
        row["source_family_id"] = family_id
        rows.append(row)
    return rows


def list_handoff_edges(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for family in list_workflow_families(repo_root=repo_root):
        family_id = str(family.get("identity", {}).get("family_id") or "")
        if family_id:
            edges.extend(handoffs_for(family_id, repo_root=repo_root))
    return edges


def validate_handoff_graph(*, repo_root: Path | None = None) -> list[str]:
    """Validate registry handoff edges — fail-closed gate for organ mesh."""
    errors: list[str] = []
    known_ids = {
        str(f.get("identity", {}).get("family_id") or "")
        for f in list_workflow_families(repo_root=repo_root)
    }
    known_ids.discard("")
    for edge in list_handoff_edges(repo_root=repo_root):
        source_id = str(edge.get("source_family_id") or "")
        target_id = str(edge.get("target_family_id") or "")
        chain_id = str(edge.get("chain_id") or "")
        source_chain_id = str(edge.get("source_chain_id") or "")
        if source_id not in known_ids:
            errors.append(f"unknown source family: {source_id}")
        if target_id not in known_ids:
            errors.append(f"unknown target family: {target_id}")
        if source_id == target_id:
            errors.append(f"self-handoff disallowed: {source_id}")
        target_family = family_by_id(target_id, repo_root=repo_root)
        if target_family and chain_id:
            chain_ids = {str(c.get("chain_id") or "") for c in list(target_family.get("chains") or [])}
            if chain_id not in chain_ids:
                errors.append(f"unknown target chain {chain_id} on {target_id}")
        source_family = family_by_id(source_id, repo_root=repo_root)
        if source_family and source_chain_id:
            source_chain_ids = {str(c.get("chain_id") or "") for c in list(source_family.get("chains") or [])}
            if source_chain_id not in source_chain_ids:
                errors.append(f"unknown source chain {source_chain_id} on {source_id}")
        occ = str(edge.get("occ_class") or "")
        if occ and occ not in {"OCC-0", "OCC-1", "OCC-2"}:
            errors.append(f"invalid occ_class on {source_id}->{target_id}: {occ}")
    return errors
