"""Story Forge Lane Organ — read-only story_forge_audio capability lane posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.capabilities.story_forge_audio import (
    CAPABILITY_NAME,
    CAPABILITY_VERSION,
    STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID,
)

MODULE_ID = "AAIS-SFL-01"
ORGAN_VERSION = "story_forge_lane_organ.v1"


def build_story_forge_lane_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    capability_present = (root / "src/capabilities/story_forge_audio.py").is_file()
    external_present = (root / "external/story_forge/src/story_forge").is_dir()
    summary = (
        f"cap={CAPABILITY_NAME}:{CAPABILITY_VERSION};"
        f"component={STORY_FORGE_AUDIO_CAPABILITY_COMPONENT_ID};bridge_safe=1"
    )[:128]
    return {
        "story_forge_lane_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "capability_present": capability_present,
        "external_story_forge_present": external_present,
        "bridge_safe": True,
        "proposal_only": True,
        "front_door_active": False,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
