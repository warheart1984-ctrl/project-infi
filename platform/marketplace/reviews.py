"""Listing reviews (v33)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.common import new_id
from platform.store import PlatformStore


def add_review(
    *,
    store: PlatformStore,
    listing_id: str,
    org_id: str,
    principal_id: str,
    rating: int,
    comment: str = "",
) -> dict[str, Any]:
    if rating < 1 or rating > 5:
        raise ValueError("rating must be 1-5")
    rec = {
        "review_id": new_id("rev"),
        "listing_id": listing_id,
        "org_id": org_id,
        "principal_id": principal_id,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now(UTC).isoformat(),
    }
    return store.upsert_listing_review(rec)


def review_stats(*, store: PlatformStore, listing_id: str) -> dict[str, Any]:
    reviews = store.list_listing_reviews(listing_id=listing_id)
    if not reviews:
        return {"review_count": 0, "average_rating": 0.0}
    total = sum(int(r.get("rating") or 0) for r in reviews)
    return {"review_count": len(reviews), "average_rating": round(total / len(reviews), 2)}
