"""Marketplace catalog and listing visibility (v17 + v34)."""

from __future__ import annotations

from typing import Any

from platform.marketplace.visibility import can_view_listing
from platform.store import PlatformStore


def list_visible_listings(
    *,
    store: PlatformStore,
    org_id: str,
    ugr_tenant_id: str,
    is_platform_admin: bool,
    visibility_filter: str = "",
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for listing in store.list_listings():
        if visibility_filter and listing.get("visibility") != visibility_filter:
            continue
        if not can_view_listing(
            listing=listing,
            org_id=org_id,
            ugr_tenant_id=ugr_tenant_id,
            is_platform_admin=is_platform_admin,
        ):
            continue
        out.append(listing)
    return out


def search_catalog(
    *,
    store: PlatformStore,
    org_id: str,
    ugr_tenant_id: str,
    is_platform_admin: bool,
    query: str = "",
) -> list[dict[str, Any]]:
    q = query.strip().lower()
    out: list[dict[str, Any]] = []
    for listing in store.list_listings():
        if listing.get("approval_status") not in {None, "", "published"}:
            if listing.get("approval_status") != "published":
                continue
        if not can_view_listing(
            listing=listing,
            org_id=org_id,
            ugr_tenant_id=ugr_tenant_id,
            is_platform_admin=is_platform_admin,
        ):
            continue
        name = str(listing.get("name") or "").lower()
        if q and q not in name:
            continue
        out.append(listing)
    return out


def bump_listing_version(
    *,
    store: PlatformStore,
    listing: dict[str, Any],
    semver: str,
    breaking: bool = False,
) -> dict[str, Any]:
    listing = dict(listing)
    listing["semver"] = semver
    listing["breaking_change"] = breaking
    if breaking:
        listing["approval_status"] = "pending"
    store.upsert_listing(listing)
    return listing
