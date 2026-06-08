"""Peer substrate client — outbound observe against federated peer AAIS instances."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def peer_base_urls() -> list[str]:
    raw = os.getenv("AAIS_PEER_BASE_URLS", "")
    return [part.strip().rstrip("/") for part in raw.split(",") if part.strip()]


def trust_bundle_pin() -> str | None:
    pin = os.getenv("AAIS_PEER_TRUST_BUNDLE_PIN", "").strip()
    return pin or None


def observe_peer_diplomacy(base_url: str, *, timeout_s: float = 10.0) -> dict[str, Any]:
    url = f"{base_url}/api/operator/diplomacy/observe"
    body = json.dumps({"session_id": "peer-observe", "window_days": 7}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    pin = trust_bundle_pin()
    if pin:
        headers["X-AAIS-Trust-Bundle-Pin"] = pin
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return {"ok": True, "base_url": base_url, "observation": payload}
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")[:500]
        return {"ok": False, "base_url": base_url, "status": exc.code, "error": text}
    except Exception as exc:
        return {"ok": False, "base_url": base_url, "error": str(exc)}


def observe_all_peers(*, timeout_s: float = 10.0) -> list[dict[str, Any]]:
    return [observe_peer_diplomacy(url, timeout_s=timeout_s) for url in peer_base_urls()]
