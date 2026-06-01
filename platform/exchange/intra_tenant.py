"""Intra-tenant listing transfer (v45)."""

from __future__ import annotations

from typing import Any

from platform.exchange.envelope import build_envelope, verify_envelope
from platform.marketplace.visibility import can_view_listing
from platform.store import PlatformStore


def transfer_listing(
    *,
    store: PlatformStore,
    tenant_id: str,
    listing_id: str,
    source_org_id: str,
    target_org_id: str,
    consent_by: str,
) -> dict[str, Any]:
    listing = store.get_listing(listing_id)
    if not listing:
        raise ValueError("listing not found")
    src = store.get_org(source_org_id) or {}
    tgt = store.get_org(target_org_id) or {}
    if str(src.get("ugr_tenant_id") or "") != tenant_id or str(tgt.get("ugr_tenant_id") or "") != tenant_id:
        raise PermissionError("orgs must share tenant_id")
    if not can_view_listing(
        listing=listing,
        org_id=source_org_id,
        ugr_tenant_id=tenant_id,
        is_platform_admin=False,
    ):
        raise PermissionError("listing not visible to source org")
    envelope = build_envelope(
        tenant_id=tenant_id,
        source_org_id=source_org_id,
        target_org_id=target_org_id,
        kind="listing.transfer",
        body={"listing_id": listing_id, "name": listing.get("name")},
        consent_by=consent_by,
    )
    if not verify_envelope(envelope):
        raise PermissionError("envelope signature invalid")
    meta = dict(listing)
    meta["transferred_from_org"] = source_org_id
    meta["org_id"] = target_org_id
    meta["transfer_consent_id"] = envelope["consent_id"]
    store.upsert_listing(meta)
    return {"envelope": envelope, "listing": meta}
