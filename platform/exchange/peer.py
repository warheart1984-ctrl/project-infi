"""Peer membrane exchange (v46)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from platform.exchange.envelope import verify_envelope
from platform.store import PlatformStore


def upsert_peer(
    *,
    store: PlatformStore,
    peer_id: str,
    base_url: str,
    public_key: str = "",
) -> dict[str, Any]:
    return store.upsert_platform_peer(
        {
            "peer_id": peer_id,
            "base_url": base_url.rstrip("/"),
            "public_key": public_key,
            "status": "active",
        }
    )


def push_outbound(*, store: PlatformStore, envelope: dict[str, Any], peer_id: str) -> dict[str, Any]:
    peer = store.get_platform_peer(peer_id)
    if not peer:
        raise ValueError("peer not found")
    if not verify_envelope(envelope):
        raise PermissionError("invalid envelope")
    url = f"{peer['base_url']}/v1/exchange/inbound"
    data = json.dumps(envelope).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"status": resp.status, "peer_id": peer_id}
    except urllib.error.URLError as exc:
        return {"status": "error", "error": str(exc), "peer_id": peer_id}


def apply_inbound(*, store: PlatformStore, envelope: dict[str, Any]) -> dict[str, Any]:
    if not verify_envelope(envelope):
        raise PermissionError("invalid envelope")
    if envelope.get("dual_consent") and not envelope.get("consent_id"):
        raise PermissionError("dual_consent required")
    return {"status": "accepted", "envelope": envelope, "claim_label": "asserted"}
