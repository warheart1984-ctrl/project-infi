"""Discover plug descriptors from library registry patterns."""

# Mythic: Plug Discovery
# Engineering: PlugDiscoveryEngine
from __future__ import annotations

import re
from typing import Any

from src.library_registry import list_libraries


def _pattern_to_plug_id(pattern: str) -> str:
    return str(pattern or "").strip().rstrip(".*")


def discover_plugs(*, repo_root=None) -> list[dict[str, Any]]:
    plugs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for library in list_libraries(repo_root=repo_root):
        identity = dict(library.get("identity") or {})
        mount = dict(library.get("mount") or {})
        library_class = str(identity.get("library_class") or "native_capability")
        library_id = str(identity.get("library_id") or "")
        for pattern in list(mount.get("plug_patterns") or []):
            plug_id = _pattern_to_plug_id(str(pattern))
            if not plug_id or plug_id in seen:
                continue
            seen.add(plug_id)
            authority = "observe"
            ladder = list((library.get("family") or {}).get("authority_ladder") or [])
            if ladder:
                authority = str(ladder[-1])
            plugs.append(
                {
                    "plug_adapter_version": "plug_adapter.v1",
                    "plug_id": plug_id,
                    "display_name": plug_id.replace(".", " / "),
                    "plug_class": library_class,
                    "authority_level": authority,
                    "enabled": False,
                    "cisiv_stage": "structure",
                    "library_id": library_id,
                    "pattern": str(pattern),
                    "provenance": {"adapter_module": mount.get("adapter_module")},
                }
            )
    return plugs


def match_plug_pattern(plug_id: str, pattern: str) -> bool:
    pat = str(pattern or "").strip()
    if pat.endswith(".*"):
        prefix = pat[:-2]
        return plug_id == prefix or plug_id.startswith(prefix + ".")
    return plug_id == pat
