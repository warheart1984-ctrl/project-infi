"""Broken lineage failure demo."""

from __future__ import annotations

from typing import Any


def run() -> dict[str, Any]:
    lineage = [{"id": "e1", "parent": "missing"}]
    reconstructible = all(
        any(node.get("id") == edge.get("parent") for node in lineage)
        for edge in lineage
        if edge.get("parent") not in (None, "")
    )
    return {
        "question": "Does reconstruction fail when CLG-1 lineage is broken?",
        "passed": not reconstructible,
        "lineage": lineage,
    }
