"""Listing approval lifecycle (v23)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.store import PlatformStore


def default_approval_status(*, visibility: str, is_platform_admin: bool) -> str:
    if visibility == "public":
        return "pending"
    if is_platform_admin:
        return "published"
    return "draft"


def approve_listing(
    *,
    store: PlatformStore,
    listing: dict[str, Any],
    approved_by: str,
) -> dict[str, Any]:
    listing = dict(listing)
    listing["approval_status"] = "published"
    listing["approved_by"] = approved_by
    listing["published_at"] = datetime.now(UTC).isoformat()
    store.upsert_listing(listing)
    return listing


def deprecate_listing(*, store: PlatformStore, listing: dict[str, Any]) -> dict[str, Any]:
    listing = dict(listing)
    listing["approval_status"] = "deprecated"
    listing["deprecated_at"] = datetime.now(UTC).isoformat()
    store.upsert_listing(listing)
    return listing


def listing_installable(listing: dict[str, Any]) -> tuple[bool, str]:
    status = str(listing.get("approval_status") or "published")
    if status == "deprecated":
        return False, "listing deprecated"
    if status not in {"published"}:
        return False, f"listing not published (status={status})"
    return True, "ok"
