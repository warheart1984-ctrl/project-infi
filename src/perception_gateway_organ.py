"""Perception Gateway Organ — read-only bridge perception catalog posture."""

# Mythic: Perception Gateway Organ
# Engineering: PerceptionGatewayGate
from __future__ import annotations

from typing import Any

from src.document_vision_organ import build_document_vision_status
from src.ui_vision_organ import build_ui_vision_status

MODULE_ID = "AAIS-PGO-01"
ORGAN_VERSION = "perception_gateway_organ.v1"

PERCEPTION_CAPABILITIES = ("document_vision", "ui_vision", "spatial", "mystic")
PERCEPTION_ENTRY_KINDS = ("document_vision", "ui_vision", "spatial", "mystic")


def route_perception_entry(
    kind: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Single router helper for document/ui vision and bridge perception caps."""
    normalized = str(kind or "").strip().lower().replace("-", "_")
    data = dict(payload or {})
    if normalized == "document_vision":
        from src.document_vision import DocumentVisionUnavailable, document_vision

        image = data.get("image")
        if image is None:
            return {"ok": False, "kind": normalized, "error": "image required"}
        try:
            result = document_vision.extract_document_text(image)
            return {"ok": True, "kind": normalized, "result": result}
        except DocumentVisionUnavailable as exc:
            return {"ok": False, "kind": normalized, "error": str(exc)}
    if normalized == "ui_vision":
        from src.ui_vision import UIVisionUnavailable, ui_vision

        image = data.get("image")
        if image is None:
            return {"ok": False, "kind": normalized, "error": "image required"}
        try:
            result = ui_vision.analyze_ui(
                image,
                include_operator_assist=bool(data.get("include_operator_assist")),
            )
            return {"ok": True, "kind": normalized, "result": result}
        except UIVisionUnavailable as exc:
            return {"ok": False, "kind": normalized, "error": str(exc)}
    if normalized in PERCEPTION_CAPABILITIES:
        return {
            "ok": True,
            "kind": normalized,
            "bridge_capability": normalized,
            "routed": True,
            "claim_label": "asserted",
        }
    return {"ok": False, "kind": normalized, "error": "unsupported perception entry"}


def build_perception_gateway_status() -> dict[str, Any]:
    doc = build_document_vision_status()
    ui = build_ui_vision_status()
    vision_any = bool(doc.get("document_vision_enabled") or ui.get("ui_vision_enabled"))
    bridge_caps = list(PERCEPTION_CAPABILITIES)
    summary = f"vision={int(vision_any)};caps={len(bridge_caps)};router=1;read_only=1"[:128]
    return {
        "perception_gateway_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "document_vision_enabled": doc.get("document_vision_enabled"),
        "ui_vision_enabled": ui.get("ui_vision_enabled"),
        "bridge_capabilities": bridge_caps,
        "perception_router_present": True,
        "perception_entry_kinds": list(PERCEPTION_ENTRY_KINDS),
        "bridge_safe": True,
        "operator_gated": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
