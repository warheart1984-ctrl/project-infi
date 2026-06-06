"""MCP plug bridge — observe/assist modes for v1."""

from __future__ import annotations

from typing import Any

from src.plug_discovery import discover_plugs


def list_mcp_plugs(*, repo_root=None) -> list[dict[str, Any]]:
    return [plug for plug in discover_plugs(repo_root=repo_root) if plug.get("plug_class") == "mcp"]


def invoke_mcp_plug(plug_id: str, *, args: dict[str, Any] | None = None, dry_run: bool = True) -> dict[str, Any]:
    return {
        "plug_id": plug_id,
        "outcome": "dry_run" if dry_run else "simulated",
        "result": {"args": dict(args or {})},
        "receipt_required": True,
    }
