"""Listing visibility: org | tenant | public (curated)."""

from __future__ import annotations

from typing import Any

ListingVisibility = str  # org | tenant | public


def can_view_listing(
    *,
    listing: dict[str, Any],
    org_id: str,
    ugr_tenant_id: str,
    is_platform_admin: bool,
) -> bool:
    vis = str(listing.get("visibility") or "org")
    if vis == "org":
        return listing.get("org_id") == org_id
    if vis == "tenant":
        return str(listing.get("ugr_tenant_id") or "") == ugr_tenant_id
    if vis == "public":
        return bool(listing.get("curated")) or is_platform_admin
    return False


def can_publish_visibility(
    *,
    visibility: str,
    is_platform_admin: bool,
    curated: bool = False,
) -> tuple[bool, str]:
    if visibility == "public":
        if not is_platform_admin or not curated:
            return False, "public curated listings require platform_admin"
    if visibility not in {"org", "tenant", "public"}:
        return False, f"invalid visibility {visibility}"
    return True, "ok"
