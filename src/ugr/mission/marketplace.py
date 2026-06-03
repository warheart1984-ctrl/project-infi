"""Governed provider organ marketplace — query and catalog."""

from __future__ import annotations

from typing import Any

from src.ugr.mission.provider_organ import ORGAN_STATUS_ADMITTED, ProviderOrganRegistry
from src.ugr.platform.tenant_registry import normalize_tenant_id


def _public_organ_tuple(organ: Any) -> dict[str, Any]:
    return {
        "organ_id": organ.organ_id,
        "provider": organ.provider,
        "tier": organ.tier,
        "status": organ.status,
        "tenant_scope": organ.tenant_scope,
        "governance_tier": organ.governance_tier,
        "trust_score": organ.trust_score,
        "label": str(organ.identity.get("label") or organ.organ_id),
        "allowed_regions": list(organ.contract.get("allowed_regions") or []),
        "admissible_rails": list(organ.contract.get("admissible_rails") or []),
    }


def query_organs(*, tenant_id: str | None = None, include_suspended: bool = False) -> dict[str, Any]:
    """Public catalog — no secrets."""
    tenant_norm = normalize_tenant_id(tenant_id or "global")
    registry = ProviderOrganRegistry(tenant_id=tenant_norm)
    organs = registry.list_organs(include_suspended=include_suspended)
    return {
        "tenant_id": tenant_norm,
        "organ_count": len(organs),
        "organs": [_public_organ_tuple(o) for o in organs if o.status != "evicted"],
    }


def apply_provider_organ_mutation(
    *,
    tenant_id: str,
    mutation_op: str,
    organ_spec: dict[str, Any] | None = None,
    organ_id: str | None = None,
) -> tuple[bool, str, str]:
    """
    Apply organ_admit / organ_suspend / organ_evict to tenant overlay.

    Returns (ok, message, after_digest).
    """
    import os

    if os.getenv("URG_GOVERNANCE_APPLY", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return False, "URG_GOVERNANCE_APPLY not enabled", ""

    from hashlib import sha256

    tenant_norm = normalize_tenant_id(tenant_id)
    registry = ProviderOrganRegistry(tenant_id=tenant_norm)
    op = str(mutation_op or "").strip().lower()
    oid = str(organ_id or (organ_spec or {}).get("organ_id") or "").strip()

    if op == "organ_admit":
        if not organ_spec or not oid:
            return False, "organ_admit requires organ_spec with organ_id", ""
        spec = dict(organ_spec)
        spec.setdefault("tenant_scope", tenant_norm)
        spec.setdefault("status", ORGAN_STATUS_ADMITTED)
        spec.setdefault("admission_receipt_id", spec.get("admission_receipt_id"))
        registry.upsert_organ(oid, spec)
    elif op == "organ_suspend":
        if not oid:
            return False, "organ_suspend requires organ_id", ""
        existing = registry.get(oid)
        if not existing:
            return False, f"organ {oid} not found", ""
        registry.upsert_organ(oid, {**existing.to_dict(), "status": "suspended"})
    elif op == "organ_evict":
        if not oid:
            return False, "organ_evict requires organ_id", ""
        existing = registry.get(oid)
        if not existing:
            return False, f"organ {oid} not found", ""
        registry.upsert_organ(oid, {**existing.to_dict(), "status": "evicted"})
    else:
        return False, f"unsupported mutation_op {op!r}", ""

    path = registry.save_tenant_overlay()
    after_digest = sha256(path.read_bytes()).hexdigest()
    return True, f"{op} applied for {oid}", after_digest
