"""Cursor and HF skill catalog adapters."""

from __future__ import annotations

from typing import Any

from src.plug_discovery import discover_plugs


def list_skill_plugs(*, repo_root=None) -> list[dict[str, Any]]:
    return [
        plug
        for plug in discover_plugs(repo_root=repo_root)
        if plug.get("plug_class") in {"cursor_skill", "hf_agent_skill"}
    ]
