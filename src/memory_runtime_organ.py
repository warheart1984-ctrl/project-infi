"""Memory Runtime Organ — read-only Nova memory lobe snapshot."""

from __future__ import annotations

from typing import Any

from src.cog_runtime.memory import MEMORY_RUNTIME_ID, memory_runtime_spec


def build_memory_runtime_status() -> dict[str, Any]:
    spec = memory_runtime_spec()
    stages = list(spec.get("stages") or ())
    return {
        "memory_runtime_organ_version": "memory_runtime_organ.v1",
        "runtime_id": spec.get("runtime_id") or MEMORY_RUNTIME_ID,
        "runtime_version": str(spec.get("version") or ""),
        "stages": stages,
        "summary": str(spec.get("summary") or ""),
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
        "invariant_count": len(spec.get("invariants") or ()),
    }
