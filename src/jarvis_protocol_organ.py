"""Jarvis Protocol Organ — read-only message/tool protocol posture."""

from __future__ import annotations

from typing import Any

from src.jarvis_protocol import PROTOCOL_ID, PROTOCOL_VERSION, SUPPORTED_CHANNELS, SUPPORTED_ROLES

MODULE_ID = "AAIS-JPO-01"
ORGAN_VERSION = "jarvis_protocol_organ.v1"


def build_jarvis_protocol_status() -> dict[str, Any]:
    summary = (
        f"protocol={PROTOCOL_ID};roles={len(SUPPORTED_ROLES)};"
        f"channels={len(SUPPORTED_CHANNELS)};read_only=1"
    )[:128]
    return {
        "jarvis_protocol_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "supported_roles": list(SUPPORTED_ROLES),
        "supported_channels_count": len(SUPPORTED_CHANNELS),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
