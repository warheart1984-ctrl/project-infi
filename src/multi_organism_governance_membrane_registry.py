"""Operator governance membrane policy registry (Stage 13 / Release 44)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

POLICY_VERSION = "operator_membrane_policy.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_membrane_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_membrane_registry.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def adopted_policies(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    doc = load_membrane_registry(repo_root=repo_root)
    return list(doc.get("policies") or [])


def save_adopted_policy(policy: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / "governance" / "operator_membrane_registry.v1.json"
    doc = load_membrane_registry(repo_root=root)
    policies = list(doc.get("policies") or [])
    policy_id = str(policy.get("policy_id") or "")
    policies = [p for p in policies if str(p.get("policy_id") or "") != policy_id]
    policies.append(policy)
    doc["policies"] = policies
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return policy


def validate_membrane_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_membrane_registry(repo_root=repo_root)
    if doc.get("operator_membrane_registry_version") != "operator_membrane_registry.v1":
        errors.append("invalid operator_membrane_registry_version")
    for policy in list(doc.get("policies") or []):
        pid = str(policy.get("policy_id") or "")
        if not pid:
            errors.append("policy missing policy_id")
        if policy.get("policy_version") != POLICY_VERSION:
            errors.append(f"invalid policy_version on {pid}")
        if not policy.get("operator_promoted"):
            errors.append(f"registry policy must be operator_promoted: {pid}")
    return errors
