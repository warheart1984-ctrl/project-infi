"""UI Vision Organ — read-only screenshot/UI vision posture."""

# Mythic: Ui Vision Organ
# Engineering: UiVisionEngine
from __future__ import annotations

from typing import Any

from src.ui_vision import UI_VISION_ENV, ui_vision

MODULE_ID = "AAIS-UVO-01"
ORGAN_VERSION = "ui_vision_organ.v1"


def build_ui_vision_status() -> dict[str, Any]:
    enabled = ui_vision.is_enabled()
    summary = f"enabled={int(enabled)};read_only=1"[:128]
    return {
        "ui_vision_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "ui_vision_enabled": enabled,
        "env_var": UI_VISION_ENV,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
