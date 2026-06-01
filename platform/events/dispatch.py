"""Webhook delivery with HMAC signing (v32)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.common import new_id
from platform.store import PlatformStore

MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (1, 4, 16)


def sign_payload(*, secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def deliver_webhook(
    *,
    store: PlatformStore,
    subscription: dict[str, Any],
    event_type: str,
    payload: dict[str, Any],
    secret: str = "",
) -> dict[str, Any]:
    body = json.dumps(
        {"event_type": event_type, "org_id": subscription.get("org_id"), "payload": payload},
        sort_keys=True,
    ).encode()
    sig = sign_payload(secret=secret or subscription.get("secret", ""), body=body)
    delivery_id = new_id("whd")
    record: dict[str, Any] = {
        "delivery_id": delivery_id,
        "org_id": subscription.get("org_id"),
        "subscription_id": subscription.get("subscription_id"),
        "event_type": event_type,
        "status": "pending",
        "attempt": 0,
        "created_at": datetime.now(UTC).isoformat(),
    }
    url = str(subscription.get("url") or "")
    for attempt in range(1, MAX_ATTEMPTS + 1):
        record["attempt"] = attempt
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Platform-Signature": f"sha256={sig}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                record["response_code"] = resp.status
            record["status"] = "delivered"
            store.record_webhook_delivery(record)
            from platform.ledger.hooks import ledger_webhook_delivery

            ledger_webhook_delivery(store=store, delivery=record)
            return record
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            record["error"] = str(exc)
            record["status"] = "failed" if attempt >= MAX_ATTEMPTS else "retry"
            if attempt < MAX_ATTEMPTS:
                time.sleep(BACKOFF_SECONDS[attempt - 1])
    store.record_webhook_delivery(record)
    from platform.ledger.hooks import ledger_webhook_delivery

    ledger_webhook_delivery(store=store, delivery=record)
    return record


def emit_org_event(
    *,
    store: PlatformStore,
    org_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    if event_type not in {"job.status", "proof.status", "mesh.event", "mesh.autopilot"}:
        return []
    results: list[dict[str, Any]] = []
    for sub in store.list_webhook_subscriptions(org_id=org_id):
        if not sub.get("enabled", True):
            continue
        if event_type not in (sub.get("event_types") or []):
            continue
        results.append(
            deliver_webhook(
                store=store,
                subscription=sub,
                event_type=event_type,
                payload=payload,
            )
        )
    return results
