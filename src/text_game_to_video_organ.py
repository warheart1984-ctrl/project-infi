"""Text-Game-to-Video Organ — read-only /pipeline movie front-door posture."""

# Mythic: Text-Game-to-Video Organ
# Engineering: TextGameToVideoFrontDoor
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-TGTV-01"
ORGAN_VERSION = "text_game_to_video_organ.v1"


def build_text_game_to_video_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = root / "external/story_forge/src/story_forge/engine.py"
    genome = root / "governance/subsystem_genomes/text_game_to_video_organ.genome.v1.json"
    present = engine.is_file()
    summary = f"pipeline_movie=0;engine={int(present)};operator_gated=1"[:128]
    return {
        "text_game_to_video_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "engine_module_present": present,
        "parent_genome_present": genome.is_file(),
        "front_door_active": False,
        "operator_gated": True,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
