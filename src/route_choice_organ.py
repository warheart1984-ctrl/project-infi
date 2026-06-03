"""Route Choice Organ — read-only model route posture (advisory only)."""

# Mythic: Route Choice Organ
# Engineering: RouteChoiceInterface
from __future__ import annotations

from typing import Any

from src.model_routing import MODEL_ROUTES

MODULE_ID = "AAIS-RCO-01"
ORGAN_VERSION = "route_choice_organ.v1"


def build_route_choice_status() -> dict[str, Any]:
    route_ids = sorted(MODEL_ROUTES.keys())
    default_route = route_ids[0] if route_ids else "tiny_companion"
    summary = f"routes={len(route_ids)};advisory=1;read_only=1"[:128]
    return {
        "route_choice_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "model_route_count": len(route_ids),
        "model_routes": route_ids[:12],
        "default_route": default_route,
        "routing_read_only": True,
        "advisory_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
