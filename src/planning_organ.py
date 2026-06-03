"""Planning Organ — read-only cognitive.planning lobe posture."""

# Mythic: Planning Organ
# Engineering: PlanningEngine
from __future__ import annotations

from typing import Any

from src.cog_runtime.planning import PLANNING_RUNTIME_ID, planning_runtime_spec

MODULE_ID = "AAIS-PLO-02"
ORGAN_VERSION = "planning_organ.v1"


def build_planning_status() -> dict[str, Any]:
    spec = planning_runtime_spec()
    return {
        "planning_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "runtime_id": spec.get("runtime_id") or PLANNING_RUNTIME_ID,
        "runtime_version": str(spec.get("version") or ""),
        "stages": list(spec.get("stages") or ()),
        "summary": str(spec.get("summary") or "")[:128],
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
