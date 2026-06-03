"""Tenant manifold — frozen tenant scope for URG missions."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import time
from typing import Any

from src.ugr.platform.tenant_registry import TenantRegistry, TenantSpec, normalize_tenant_id


TENANT_MANIFOLD_VERSION = "1.0"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def tenant_path_slug(tenant_id: str) -> str:
    """Filesystem-safe slug for tenant partition paths."""
    return normalize_tenant_id(tenant_id).replace(":", "-")


def compute_tenant_manifold_digest(
    *,
    tenant_id: str,
    allowed_regions: list[str],
    allowed_providers: list[str],
    cost_ceiling: dict[str, Any],
    invariant_profile: str,
    receipt_key_id: str,
) -> str:
    payload = {
        "tenant_id": normalize_tenant_id(tenant_id),
        "allowed_regions": sorted(allowed_regions),
        "allowed_providers": sorted(allowed_providers),
        "cost_ceiling": dict(cost_ceiling or {}),
        "invariant_profile": str(invariant_profile or "default"),
        "receipt_key_id": str(receipt_key_id or ""),
        "version": TENANT_MANIFOLD_VERSION,
    }
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TenantManifoldState:
    tenant_id: str
    tenant_manifold_digest: str
    allowed_regions: tuple[str, ...]
    allowed_providers: tuple[str, ...]
    cost_ceiling: dict[str, Any]
    invariant_profile: str
    receipt_key_id: str
    federation_grants: tuple[dict[str, Any], ...]
    stamped_at: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_manifold_version": TENANT_MANIFOLD_VERSION,
            "tenant_id": self.tenant_id,
            "tenant_normalized_id": self.tenant_id,
            "tenant_manifold_digest": self.tenant_manifold_digest,
            "allowed_regions": list(self.allowed_regions),
            "allowed_providers": list(self.allowed_providers),
            "cost_ceiling": dict(self.cost_ceiling),
            "invariant_profile": self.invariant_profile,
            "receipt_key_id": self.receipt_key_id,
            "federation_grants": list(self.federation_grants),
            "tenant_stamped_at": self.stamped_at,
        }


def build_tenant_manifold(tenant_spec: TenantSpec) -> TenantManifoldState:
    digest = compute_tenant_manifold_digest(
        tenant_id=tenant_spec.tenant_id,
        allowed_regions=list(tenant_spec.allowed_regions),
        allowed_providers=list(tenant_spec.allowed_providers),
        cost_ceiling=dict(tenant_spec.cost_ceiling),
        invariant_profile=tenant_spec.invariant_profile,
        receipt_key_id=tenant_spec.receipt_key_id,
    )
    return TenantManifoldState(
        tenant_id=tenant_spec.tenant_id,
        tenant_manifold_digest=digest,
        allowed_regions=tuple(tenant_spec.allowed_regions),
        allowed_providers=tuple(tenant_spec.allowed_providers),
        cost_ceiling=dict(tenant_spec.cost_ceiling),
        invariant_profile=tenant_spec.invariant_profile,
        receipt_key_id=tenant_spec.receipt_key_id,
        federation_grants=tuple(tenant_spec.federation_grants),
        stamped_at=int(time.time()),
    )


def validate_tenant_for_mission(
    request: dict[str, Any],
    *,
    registry: TenantRegistry | None = None,
) -> tuple[TenantManifoldState | None, list[dict[str, Any]]]:
    """
    Resolve tenant spec and build manifold.

    Returns (manifold, invariant_results). manifold is None on hard_fail.
    """
    from src.ugr.invariants.cloud_invariants import _invariant, has_hard_fail

    reg = registry or TenantRegistry()
    raw_tenant = str(request.get("tenant_id") or "global").strip() or "global"
    normalized = normalize_tenant_id(raw_tenant)
    spec = reg.get(normalized)
    results: list[dict[str, Any]] = []

    if spec is None:
        results.append(_invariant("cloud_tenant_boundary", "hard_fail", f"unknown tenant {normalized!r}"))
        return None, results
    if not spec.enabled:
        results.append(_invariant("cloud_tenant_boundary", "hard_fail", f"tenant {normalized} disabled"))
        return None, results

    manifold = build_tenant_manifold(spec)
    results.extend(check_tenant_boundary(request, manifold))
    results.extend(check_tenant_federation(request, manifold))
    if has_hard_fail(results):
        return None, results
    results.append(_invariant("cloud_tenant_boundary", "pass", normalized))
    return manifold, results


def check_tenant_boundary(
    request: dict[str, Any],
    manifold: TenantManifoldState,
) -> list[dict[str, Any]]:
    from src.ugr.invariants.cloud_invariants import _invariant

    results: list[dict[str, Any]] = []
    region_id = str(request.get("region_id") or "").strip()
    if region_id and manifold.allowed_regions and region_id not in manifold.allowed_regions:
        results.append(
            _invariant(
                "cloud_tenant_boundary",
                "hard_fail",
                f"region {region_id} not in tenant allowlist",
            )
        )
    constraints = dict(request.get("constraints") or {})
    required_region = str(constraints.get("required_region") or "").strip()
    if required_region and manifold.allowed_regions and required_region not in manifold.allowed_regions:
        results.append(
            _invariant(
                "cloud_tenant_boundary",
                "hard_fail",
                f"required_region {required_region} not in tenant allowlist",
            )
        )
    return results


def check_tenant_federation(
    request: dict[str, Any],
    manifold: TenantManifoldState,
) -> list[dict[str, Any]]:
    from src.ugr.invariants.cloud_invariants import _invariant

    results: list[dict[str, Any]] = []
    target = str(request.get("federation_target_tenant") or "").strip()
    if not target:
        return results
    grant_id = str(request.get("federation_grant_id") or "").strip()
    target_norm = normalize_tenant_id(target)
    if target_norm == manifold.tenant_id:
        results.append(_invariant("cloud_tenant_federation", "pass", "same tenant"))
        return results
    now = int(time.time())
    matched = False
    for grant in manifold.federation_grants:
        if normalize_tenant_id(grant.get("target_tenant") or "") != target_norm:
            continue
        if grant_id and str(grant.get("grant_id") or "") != grant_id:
            continue
        expires = grant.get("expires_at")
        if expires is not None and int(expires) < now:
            continue
        matched = True
        break
    if not matched:
        results.append(
            _invariant(
                "cloud_tenant_federation",
                "hard_fail",
                f"no federation grant for {target_norm}",
            )
        )
    else:
        results.append(_invariant("cloud_tenant_federation", "pass", target_norm))
    return results


def tenant_hard_ceil(manifold: TenantManifoldState | None) -> float | None:
    if not manifold:
        return None
    ceiling = dict(manifold.cost_ceiling or {})
    raw = ceiling.get("hard_ceil")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None
