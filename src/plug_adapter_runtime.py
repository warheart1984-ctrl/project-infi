"""Plug adapter runtime — registry, enable/disable, governed execute."""

# Mythic: Plug Adapter
# Engineering: PlugAdapterRuntimeEngine
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.library_registry import list_libraries
from src.mcp_bridge import invoke_mcp_plug
from src.plug_discovery import discover_plugs, match_plug_pattern
from src.workflow_plugin_catalog import list_workflow_bundles

MODULE_ID = "AAIS-PAR-01"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


class PlugAdapterRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root
        self._lock = threading.Lock()
        self._state_path = self._runtime_dir / "plug_adapter" / "enabled_plugs.json"

    def _load_enabled(self) -> dict[str, bool]:
        if not self._state_path.is_file():
            return {}
        try:
            return dict(json.loads(self._state_path.read_text(encoding="utf-8")).get("enabled") or {})
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_enabled(self, enabled: dict[str, bool]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated_at": _utc_now_iso(), "enabled": enabled}
        self._state_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def rescan(self) -> dict[str, Any]:
        plugs = discover_plugs(repo_root=self._repo_root)
        return {"plug_count": len(plugs), "rescanned_at": _utc_now_iso()}

    def registry_snapshot(self) -> dict[str, Any]:
        enabled = self._load_enabled()
        plugs = []
        for plug in discover_plugs(repo_root=self._repo_root):
            row = dict(plug)
            row["enabled"] = bool(enabled.get(row["plug_id"], False))
            plugs.append(row)
        return {
            "plug_adapter_version": "plug_adapter.v1",
            "module_id": MODULE_ID,
            "plug_count": len(plugs),
            "enabled_count": sum(1 for p in plugs if p.get("enabled")),
            "plugs": plugs,
        }

    def list_libraries(self) -> list[dict[str, Any]]:
        return list_libraries(repo_root=self._repo_root)

    def list_workflows(self) -> list[dict[str, Any]]:
        return list_workflow_bundles(repo_root=self._repo_root)

    def set_plug_enabled(self, plug_id: str, enabled: bool) -> dict[str, Any] | None:
        plugs = {p["plug_id"]: p for p in discover_plugs(repo_root=self._repo_root)}
        if plug_id not in plugs:
            return None
        with self._lock:
            state = self._load_enabled()
            state[plug_id] = bool(enabled)
            self._save_enabled(state)
        row = dict(plugs[plug_id])
        row["enabled"] = bool(enabled)
        return row

    def execute_plug(
        self,
        plug_id: str,
        *,
        args: dict[str, Any] | None = None,
        dry_run: bool = True,
        operator_approved: bool = False,
    ) -> dict[str, Any]:
        plugs = {p["plug_id"]: p for p in discover_plugs(repo_root=self._repo_root)}
        plug = plugs.get(plug_id)
        if not plug:
            return {"outcome": "not_found", "plug_id": plug_id}
        enabled = self._load_enabled()
        if not enabled.get(plug_id, False):
            return {"outcome": "blocked", "reason": "plug disabled", "plug_id": plug_id}
        authority = str(plug.get("authority_level") or "observe")
        if authority in {"execute", "admin"} and not operator_approved and not dry_run:
            return {"outcome": "blocked", "reason": "operator_approved required", "plug_id": plug_id}
        if plug.get("plug_class") == "mcp":
            result = invoke_mcp_plug(plug_id, args=args, dry_run=dry_run or authority == "observe")
        else:
            result = {
                "plug_id": plug_id,
                "outcome": "dry_run" if dry_run else "simulated",
                "result": {"args": dict(args or {})},
            }
        receipt_id = f"plug_{uuid4().hex[:12]}"
        return {
            "execution_id": receipt_id,
            "plug_id": plug_id,
            "authority_level": authority,
            "dry_run": bool(dry_run),
            "result": result,
            "recorded_at": _utc_now_iso(),
        }


plug_adapter_runtime = PlugAdapterRuntime()
