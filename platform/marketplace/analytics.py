"""Marketplace analytics (v24)."""

from __future__ import annotations

from typing import Any

from platform.marketplace.reviews import review_stats
from platform.store import PlatformStore


def marketplace_analytics(*, store: PlatformStore, org_id: str) -> dict[str, Any]:
    listings = [l for l in store.list_listings() if l.get("org_id") == org_id]
    usage = store.list_usage(org_id=org_id)
    installs = sum(int(u.get("marketplace_installs") or 0) for u in usage)
    runs = sum(int(u.get("workflow_runs_from_listing") or 0) for u in usage)
    by_listing: dict[str, int] = {}
    for u in usage:
        meta = u.get("metadata") or {}
        for lid, cnt in (meta.get("listing_installs_by_id") or {}).items():
            by_listing[str(lid)] = by_listing.get(str(lid), 0) + int(cnt)
    by_status: dict[str, int] = {}
    review_totals = 0
    rating_sum = 0.0
    for l in listings:
        st = str(l.get("approval_status") or "published")
        by_status[st] = by_status.get(st, 0) + 1
        stats = review_stats(store=store, listing_id=str(l["listing_id"]))
        review_totals += stats["review_count"]
        rating_sum += stats["average_rating"] * stats["review_count"]
    return {
        "org_id": org_id,
        "listing_count": len(listings),
        "by_approval_status": by_status,
        "marketplace_installs": installs,
        "workflow_runs_from_listing": runs,
        "listing_installs_by_id": by_listing,
        "review_count": review_totals,
        "average_rating": round(rating_sum / review_totals, 2) if review_totals else 0.0,
    }
