"""Client for standalone ARIS service with embedded fallback."""

# Mythic: Aris Service Client
# Engineering: ArisServiceClientEngine
from __future__ import annotations

import os
from typing import Any

from src.aris_integration import ARIS_CONTRACT_VERSION, ARIS_RUNTIME_PROFILE, build_aris_enforcement


ARIS_MODES = frozenset({"embedded", "standalone", "dual"})


def _aris_mode() -> str:
    mode = os.getenv("ARIS_MODE", "embedded").strip().lower()
    return mode if mode in ARIS_MODES else "embedded"


def _service_base_url() -> str:
    return os.getenv("ARIS_SERVICE_URL", "http://127.0.0.1:8791").rstrip("/")


def aris_standalone_enabled() -> bool:
    return _aris_mode() in {"standalone", "dual"}


def evaluate_aris_admission(
    packet: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Route admission through standalone service when configured, else embedded."""
    if packet is None and kwargs:
        return build_aris_enforcement(**kwargs)
    mode = _aris_mode()
    if packet is None:
        packet = {}
    if mode in {"standalone", "dual"}:
        try:
            return _evaluate_via_service(packet)
        except Exception as exc:
            if mode == "standalone":
                return {
                    "decision": "BLOCK",
                    "reason": f"ARIS standalone unavailable: {exc}",
                    "runtime_profile": ARIS_RUNTIME_PROFILE,
                    "mode": mode,
                }
    return build_aris_enforcement(
        details=packet.get("payload") if isinstance(packet.get("payload"), dict) else packet,
        runtime_context=str(packet.get("runtime_context") or "live_runtime"),
        effectful=bool(packet.get("effectful")),
        source=packet.get("source"),
        packet_type=packet.get("type") or packet.get("packet_type"),
    )


def _evaluate_via_service(packet: dict[str, Any]) -> dict[str, Any]:
    import urllib.error
    import urllib.request
    import json

    url = f"{_service_base_url()}/v1/admit"
    body = json.dumps({"packet": packet}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc)) from exc
    payload.setdefault("runtime_profile", ARIS_RUNTIME_PROFILE)
    payload.setdefault("contract_version", ARIS_CONTRACT_VERSION)
    payload["mode"] = _aris_mode()
    payload["standalone_service"] = True
    return payload


def build_aris_client_status() -> dict[str, Any]:
    return {
        "aris_client_version": "aris_service_client.v1",
        "mode": _aris_mode(),
        "standalone_enabled": aris_standalone_enabled(),
        "service_url": _service_base_url() if aris_standalone_enabled() else None,
        "embedded_profile": ARIS_RUNTIME_PROFILE,
        "fallback_to_embedded": _aris_mode() == "dual",
    }
