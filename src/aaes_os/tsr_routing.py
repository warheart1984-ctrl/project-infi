"""TSR routing — trace store ownership and connector state (Nexus control plane)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_online_runtime_dir() -> Path:
    configured = os.getenv("AAIS_ONLINE_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return _repo_root() / ".runtime" / "online"


def routing_path() -> Path:
    configured = os.getenv("TSR_ROUTING_PATH")
    if configured:
        return Path(configured).expanduser()
    return default_online_runtime_dir() / "tsr-routing.json"


def default_routing() -> dict[str, Any]:
    online = default_online_runtime_dir()
    return {
        "version": "1",
        "tsr_owner": "nexus",
        "trace_store_path": str(online / "aaes_traces.jsonl"),
        "control_plane_url": os.getenv("NEXUS_OPS_CONSOLE_URL", "http://127.0.0.1:4000"),
        "daniel_runtime_enabled": False,
        "connectors": {
            "daniel": {"status": "disconnected"},
            "nexus": {"status": "active"},
        },
    }


def load_routing() -> dict[str, Any]:
    path = routing_path()
    if not path.is_file():
        return default_routing()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"TSR routing file must be a JSON object: {path}")
    return payload


def is_daniel_runtime_enabled() -> bool:
    return bool(load_routing().get("daniel_runtime_enabled", False))


def trace_store_path() -> Path:
    routing = load_routing()
    configured = routing.get("trace_store_path")
    if configured:
        return Path(str(configured)).expanduser()
    return Path(default_routing()["trace_store_path"])


def tsr_owner() -> str:
    return str(load_routing().get("tsr_owner") or "nexus")


def connector_status(connector_id: str) -> str:
    connectors = load_routing().get("connectors")
    if not isinstance(connectors, dict):
        return "unknown"
    entry = connectors.get(connector_id)
    if not isinstance(entry, dict):
        return "unknown"
    return str(entry.get("status") or "unknown")


def write_routing(payload: dict[str, Any]) -> Path:
    path = routing_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def apply_nexus_takeover(*, reason: str = "operator_handoff") -> dict[str, Any]:
    """Disconnect Daniel, assign TSR to Nexus, persist routing artifact."""
    online = default_online_runtime_dir()
    online.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload = default_routing()
    payload.update(
        {
            "updated_at": now,
            "handoff_reason": reason,
            "daniel_runtime_enabled": False,
            "connectors": {
                "daniel": {
                    "status": "disconnected",
                    "disconnected_at": now,
                    "reason": reason,
                },
                "nexus": {
                    "status": "active",
                    "owner_of": "tsr",
                    "activated_at": now,
                    "control_plane_url": payload["control_plane_url"],
                },
            },
        }
    )
    write_routing(payload)
    trace_store_path().touch(exist_ok=True)
    return payload
