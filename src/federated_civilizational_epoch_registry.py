"""Federated civilizational epoch registry — Stage 19 / Release 49."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHARTER_VERSION = "operator_federated_epoch_charter.v1"
REGISTRY_VERSION = "operator_federated_epoch_registry.v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_utc(value: str) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def registry_path(*, repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root()
    return root / "governance" / "operator_federated_epoch_registry.v1.json"


def load_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    path = registry_path(repo_root=repo_root)
    return json.loads(path.read_text(encoding="utf-8"))


def list_epochs(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    return list(load_registry(repo_root=repo_root).get("epochs") or [])


def default_epoch_id(*, repo_root: Path | None = None) -> str:
    reg = load_registry(repo_root=repo_root)
    return str(reg.get("default_epoch_id") or "")


def get_charter_template(template_id: str, *, repo_root: Path | None = None) -> dict[str, Any] | None:
    reg = load_registry(repo_root=repo_root)
    for template in reg.get("charter_templates") or []:
        if str(template.get("template_id")) == template_id:
            return template
    return None


def adopted_charters_path(*, runtime_dir: Path) -> Path:
    return runtime_dir / "federated_epoch_charters_adopted.v1.json"


def load_adopted_charters(*, runtime_dir: Path) -> list[dict[str, Any]]:
    path = adopted_charters_path(runtime_dir=runtime_dir)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("charters") or [])


def save_adopted_charter(
    charter: dict[str, Any],
    *,
    runtime_dir: Path,
) -> dict[str, Any]:
    path = adopted_charters_path(runtime_dir=runtime_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_adopted_charters(runtime_dir=runtime_dir)
    charter_id = str(charter.get("charter_id") or "")
    existing = [c for c in existing if str(c.get("charter_id") or "") != charter_id]
    existing.append(charter)
    payload = {"charter_version": CHARTER_VERSION, "charters": existing}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return charter


def get_epoch_by_id(epoch_id: str, *, repo_root: Path | None = None) -> dict[str, Any] | None:
    for epoch in list_epochs(repo_root=repo_root):
        if str(epoch.get("epoch_id")) == epoch_id:
            return epoch
    return None


def is_epoch_amendable(
    epoch_id: str,
    *,
    repo_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    epoch = get_epoch_by_id(epoch_id, repo_root=repo_root)
    if not epoch:
        return {"amendable": False, "reason": "epoch_not_found", "violations": ["epoch_not_found"]}
    violations: list[str] = []
    if epoch.get("frozen"):
        violations.append("epoch_frozen")
    if not epoch.get("amendable", True):
        violations.append("epoch_not_amendable")
    moment = now or datetime.now(timezone.utc)
    start = _parse_utc(str(epoch.get("epoch_start_utc") or ""))
    end = _parse_utc(str(epoch.get("epoch_end_utc") or ""))
    if start and moment < start:
        violations.append("epoch_not_started")
    if end and moment >= end:
        violations.append("epoch_ended")
    return {
        "amendable": len(violations) == 0,
        "reason": violations[0] if violations else "epoch_amendable",
        "violations": violations,
        "epoch_id": epoch_id,
    }


def validate_witness_quorum(
    external_witnesses: list[dict[str, Any]],
    *,
    operator_org_domain: str | None = None,
    min_external: int = 1,
) -> dict[str, Any]:
    violations: list[str] = []
    if len(external_witnesses) < min_external:
        violations.append("insufficient_external_witnesses")
    domains: set[str] = set()
    for witness in external_witnesses:
        witness_id = str(witness.get("witness_id") or "").strip()
        domain = str(witness.get("witness_org_domain") or "").strip().lower()
        if not witness_id:
            violations.append("witness_missing_id")
        if not domain:
            violations.append("witness_missing_org_domain")
        elif operator_org_domain and domain == operator_org_domain.strip().lower():
            violations.append("witness_org_must_differ_from_operator")
        if domain:
            domains.add(domain)
    if len(domains) < min_external:
        violations.append("witness_org_domains_not_distinct")
    return {"aligned": len(violations) == 0, "violations": violations}


def validate_federated_epoch_registry(*, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    doc = load_registry(repo_root=repo_root)
    if doc.get("registry_version") != REGISTRY_VERSION:
        errors.append("invalid registry_version")
    if doc.get("charter_version") != CHARTER_VERSION:
        errors.append("invalid charter_version")
    default_id = str(doc.get("default_epoch_id") or "")
    if not default_id:
        errors.append("missing default_epoch_id")
    elif not get_epoch_by_id(default_id, repo_root=repo_root):
        errors.append("default_epoch_id not found in epochs")
    for epoch in list_epochs(repo_root=repo_root):
        eid = str(epoch.get("epoch_id") or "")
        if not eid:
            errors.append("epoch missing epoch_id")
        if not epoch.get("epoch_start_utc") or not epoch.get("epoch_end_utc"):
            errors.append(f"epoch {eid} missing window bounds")
    for template in doc.get("charter_templates") or []:
        tid = str(template.get("template_id") or "")
        if not tid:
            errors.append("charter template missing template_id")
        min_w = int(template.get("min_external_witnesses") or 0)
        if min_w < 1:
            errors.append(f"template {tid} requires min_external_witnesses >= 1")
    return errors
