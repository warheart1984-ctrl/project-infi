"""API Gateway Organ — bounded api.py ingress posture."""

# Mythic: Api Gateway Organ
# Engineering: ApiGatewayGate
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-AGW-01"
ORGAN_VERSION = "api_gateway_organ.v1"


def build_api_gateway_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    api_path = root / "src" / "api.py"
    route_count = 0
    if api_path.is_file():
        text = api_path.read_text(encoding="utf-8", errors="replace")
        route_count = text.count("@app.route(")
    return {
        "api_gateway_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"routes={route_count};ingress_read_only=1"[:128],
        "api_module_present": api_path.is_file(),
        "route_decorator_count": route_count,
        "ingress_read_only": True,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
