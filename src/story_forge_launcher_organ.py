"""Story Forge Launcher Organ — read-only standalone Story Forge launcher posture."""

# Mythic: Story Forge Launcher Organ
# Engineering: StoryForgeLauncherPosture
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-SFLR-01"
ORGAN_VERSION = "story_forge_launcher_organ.v1"


def execute_story_forge_launcher_intake(
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    from src.capabilities.story_forge_organs import execute_story_forge_launcher_intake as _run

    return _run(args, root=root)


def build_story_forge_launcher_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    launcher = root / "external/story_forge/src/story_forge/launcher.py"
    genome = root / "governance/subsystem_genomes/story_forge_launcher_organ.genome.v1.json"
    proof = root / "docs/proof/storyforge/STORY_FORGE_LAUNCHER_ORGAN_EXECUTION_V1_PROOF.md"
    present = launcher.is_file()
    execution_ready = present and proof.is_file()
    summary = (
        f"launcher={int(present)};exec={int(execution_ready)};operator_gated=1"
    )[:128]
    return {
        "story_forge_launcher_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "launcher_module_present": present,
        "parent_genome_present": genome.is_file(),
        "execution_path_ready": execution_ready,
        "front_door_active": execution_ready,
        "operator_gated": True,
        "bridge_safe": True,
        "proposal_only": not execution_ready,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
