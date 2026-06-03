"""Perception Gateway Organ — read-only bridge perception catalog posture."""

# Mythic: Perception Gateway Organ
# Engineering: PerceptionGatewayGate
from __future__ import annotations

from typing import Any

from src.document_vision_organ import build_document_vision_status
from src.ui_vision_organ import build_ui_vision_status

MODULE_ID = "AAIS-PGO-01"
ORGAN_VERSION = "perception_gateway_organ.v1"

PERCEPTION_CAPABILITIES = ("spatial", "mystic")


def build_perception_gateway_status() -> dict[str, Any]:
    doc = build_document_vision_status()
    ui = build_ui_vision_status()
    vision_any = bool(doc.get("document_vision_enabled") or ui.get("ui_vision_enabled"))
    bridge_caps = list(PERCEPTION_CAPABILITIES)
    summary = f"vision={int(vision_any)};caps={len(bridge_caps)};read_only=1"[:128]
    return {
        "perception_gateway_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "document_vision_enabled": doc.get("document_vision_enabled"),
        "ui_vision_enabled": ui.get("ui_vision_enabled"),
        "bridge_capabilities": bridge_caps,
        "bridge_safe": True,
        "operator_gated": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
