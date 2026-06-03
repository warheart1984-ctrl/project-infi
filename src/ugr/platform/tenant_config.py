"""Governed updates to deploy/ugr/tenants.json (v3.0 cloud_forge profile)."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from src.ugr.platform.tenant_registry import TenantRegistry, normalize_tenant_id


def _tenants_path() -> Path:
    return TenantRegistry().path


def apply_cloud_forge_profile_update(
    tenant_id: str,
    cloud_forge: dict[str, Any],
) -> tuple[bool, str, str]:
    """
    Update optional cloud_forge block for one tenant when URG_GOVERNANCE_APPLY=1.

    Returns (ok, message, after_digest).
    """
    path = _tenants_path()
    if not path.exists():
        return False, "tenants.json missing", ""
    normalized = normalize_tenant_id(tenant_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    tenants = dict(payload.get("tenants") or {})
    spec = dict(tenants.get(normalized) or {})
    if not spec:
        return False, f"unknown tenant {normalized}", ""
    spec["cloud_forge"] = dict(cloud_forge or {})
    tenants[normalized] = spec
    payload["tenants"] = tenants
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.write_text(serialized, encoding="utf-8")
    after_digest = sha256(path.read_bytes()).hexdigest()
    return True, f"cloud_forge profile updated for {normalized}", after_digest
