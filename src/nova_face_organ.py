"""Nova Face Organ — read-only Nova companion surface binding posture."""

# Mythic: Nova Face Organ
# Engineering: NovaFaceEngine
from __future__ import annotations

from typing import Any

from src.cog_runtime.nova_face import (
    TRI_CORE_AUTHORITY,
    NOVA_FACE_BRIDGE_ID,
    NOVA_FACE_BRIDGE_VERSION,
)

MODULE_ID = "AAIS-NFO-01"
ORGAN_VERSION = "nova_face_organ.v1"


def build_nova_face_status() -> dict[str, Any]:
    return {
        "nova_face_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "bridge_id": NOVA_FACE_BRIDGE_ID,
        "bridge_version": NOVA_FACE_BRIDGE_VERSION,
        "authority_lane": TRI_CORE_AUTHORITY,
        "surface_priority": "delegated_surface",
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
