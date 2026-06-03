"""Specialist Route Organ — read-only specialist selection posture."""

# Mythic: Specialist Route Organ
# Engineering: SpecialistRouteInterface
from __future__ import annotations

from typing import Any

from src.specialist_registry import (
    MAX_REQUESTED_SPECIALISTS,
    SPECIALIST_DEFINITIONS,
    SUPPORTED_RESPONSE_MODES,
)

MODULE_ID = "AAIS-SRO-02"
ORGAN_VERSION = "specialist_route_organ.v1"


def build_specialist_route_status() -> dict[str, Any]:
    specialist_ids = sorted(SPECIALIST_DEFINITIONS.keys())
    modes = sorted(SUPPORTED_RESPONSE_MODES)
    summary = f"specialists={len(specialist_ids)};modes={len(modes)};read_only=1"[:128]
    return {
        "specialist_route_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "specialist_count": len(specialist_ids),
        "supported_response_modes": modes,
        "max_requested_specialists": MAX_REQUESTED_SPECIALISTS,
        "routing_read_only": True,
        "advisory_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
