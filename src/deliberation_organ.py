"""Deliberation Organ — read-only cognitive.deliberation lobe posture."""

# Mythic: Deliberation Organ
# Engineering: DeliberationEngine
from __future__ import annotations

from typing import Any

from src.cog_runtime.deliberation import DELIBERATION_RUNTIME_ID, deliberation_runtime_spec

MODULE_ID = "AAIS-DLO-01"
ORGAN_VERSION = "deliberation_organ.v1"


def build_deliberation_status() -> dict[str, Any]:
    spec = deliberation_runtime_spec()
    return {
        "deliberation_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "runtime_id": spec.get("runtime_id") or DELIBERATION_RUNTIME_ID,
        "runtime_version": str(spec.get("version") or ""),
        "stages": list(spec.get("stages") or ()),
        "summary": str(spec.get("summary") or "")[:128],
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
