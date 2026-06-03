#!/usr/bin/env python3
"""Release 28.2 Story Forge Expansion Bundle closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (_ROOT / "docs/proof/storyforge/STORYFORGE_EXPANSION_BUNDLE_V1_PROOF.md",)
ORGAN_TESTS = (
    "tests/test_story_forge_launcher_organ.py",
    "tests/test_movie_renderer_lane_organ.py",
    "tests/test_text_game_to_video_organ.py",
    "tests/test_game_front_door_organ.py",
    "tests/test_text_to_3d_world_lane_organ.py",
    "tests/test_world_pack_lane_organ.py",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt28-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    tests = list(ORGAN_TESTS) + [
        "tests/test_operator_cognition_coherence_fabric.py::test_alt28_story_forge_expansion_layers_at_v123",
    ]
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *tests, "-q"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        return 1
    schema = _ROOT / "schemas/operator_cognition_coherence_fabric.v1.23.json"
    if not schema.is_file():
        print("[alt28-closure-gate] FAIL: missing coherence v1.23 schema")
        return 1
    print("[alt28-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
