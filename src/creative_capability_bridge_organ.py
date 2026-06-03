"""Creative Capability Bridge Subsystem — v9/v10 bridge provider posture."""

# Mythic: Creative Capability Bridge Organ
# Engineering: CreativeCapabilityBridgeBridge
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-CCB-01"
ORGAN_VERSION = "creative_capability_bridge_organ.v1"


def build_creative_capability_bridge_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    bridge = root / "src" / "capability_service_bridge.py"
    text = bridge.read_text(encoding="utf-8") if bridge.is_file() else ""
    v9 = 'provider_name="v9_runtime"' in text
    v10 = 'provider_name="v10_runtime"' in text
    return {
        "creative_capability_bridge_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"v9_provider={int(v9)};v10_provider={int(v10)}"[:128],
        "v9_runtime_provider_present": v9,
        "v10_runtime_provider_present": v10,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
