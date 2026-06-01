"""Webhook subscriptions (v31)."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.common import new_id
from platform.store import PlatformStore

SUBSCRIPTION_VERSION = "platform.webhook_subscription.v1"
ALLOWED_EVENT_TYPES = frozenset({"job.status", "proof.status", "mesh.event", "mesh.autopilot"})


def create_subscription(
    *,
    store: PlatformStore,
    org_id: str,
    url: str,
    event_types: list[str],
) -> dict[str, Any]:
    types = [t for t in event_types if t in ALLOWED_EVENT_TYPES]
    if not types:
        raise ValueError("at least one valid event_type required")
    secret = secrets.token_urlsafe(32)
    rec = {
        "subscription_version": SUBSCRIPTION_VERSION,
        "subscription_id": new_id("wh"),
        "org_id": org_id,
        "url": url,
        "event_types": types,
        "secret_hash": hashlib.sha256(secret.encode()).hexdigest(),
        "secret": secret,
        "enabled": True,
        "created_at": datetime.now(UTC).isoformat(),
    }
    store.upsert_webhook_subscription(rec)
    return rec


def list_subscriptions(*, store: PlatformStore, org_id: str) -> list[dict[str, Any]]:
    items = []
    for sub in store.list_webhook_subscriptions(org_id=org_id):
        out = dict(sub)
        out.pop("secret_hash", None)
        out.pop("secret", None)
        items.append(out)
    return items
