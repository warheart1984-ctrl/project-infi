"""Operator identity claim registry loader (Stage 6 / Release 37)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CLAIM_VERSION = "operator_identity_claim.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_identity_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_identity_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_claims(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_identity_registry(repo_root=repo_root)
    return list(doc.get("claims") or [])


def save_adopted_claim(claim: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_identity_registry.v1.json"
    doc = load_identity_registry(repo_root=root)
    claims = list(doc.get("claims") or [])
    claim_id = str(claim.get("claim_id") or "")
    claims = [c for c in claims if str(c.get("claim_id") or "") != claim_id]
    claims.append(claim)
    doc["claims"] = claims
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return claim


def validate_identity_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_identity_registry(repo_root=repo_root)
    if doc.get("operator_identity_registry_version") != "operator_identity_registry.v1":
        errors.append("invalid operator_identity_registry_version")
    for claim in list(doc.get("claims") or []):
        claim_id = str(claim.get("claim_id") or "")
        if not claim_id:
            errors.append("claim missing claim_id")
        if claim.get("claim_version") != CLAIM_VERSION:
            errors.append(f"invalid claim_version on {claim_id}")
        if not claim.get("operator_promoted"):
            errors.append(f"registry claim must be operator_promoted: {claim_id}")
        kind = str(claim.get("claim_kind") or "")
        if kind not in {"doctrine", "role", "boundary", "constitutional"}:
            errors.append(f"invalid claim_kind on {claim_id}")
    return errors
