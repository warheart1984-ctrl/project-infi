"""Story Forge Launcher Organ — read-only standalone Story Forge launcher posture."""

# Mythic: Story Forge Launcher Organ
# Engineering: StoryForgeLauncherPosture
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-SFLR-01"
ORGAN_VERSION = "story_forge_launcher_organ.v1"


def build_story_forge_launcher_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    launcher = root / "external/story_forge/src/story_forge/launcher.py"
    genome = root / "governance/subsystem_genomes/story_forge_launcher_organ.genome.v1.json"
    present = launcher.is_file()
    summary = f"launcher={int(present)};front_door=0;operator_gated=1"[:128]
    return {
        "story_forge_launcher_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "launcher_module_present": present,
        "parent_genome_present": genome.is_file(),
        "front_door_active": False,
        "operator_gated": True,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
