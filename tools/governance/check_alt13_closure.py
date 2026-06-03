#!/usr/bin/env python3
"""Alt-13.2 creative chain and constitutional closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
STORY_PROOF = _ROOT / "docs/proof/storyforge/STORY_CHAIN_V1_PROOF.md"
CREATIVE_PROOF = _ROOT / "docs/proof/platform/CONSTITUTIONAL_CREATIVE_V1_PROOF.md"
MODULE_PROOF = _ROOT / "docs/proof/platform/MODULE_GOVERNANCE_ORGAN_V1_PROOF.md"


def main() -> int:
    errors: list[str] = []
    for proof in (STORY_PROOF, CREATIVE_PROOF, MODULE_PROOF):
        if not proof.is_file():
            errors.append(f"missing proof: {proof.relative_to(_ROOT)}")

    if errors:
        for err in errors:
            print(f"[alt13-closure-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_story_forge_lane_organ.py",
            "tests/test_beatbox_lane_organ.py",
            "tests/test_speakers_lane_organ.py",
            "tests/test_narrative_trust_pack_organ.py",
            "tests/test_human_voice_extraction_organ.py",
            "tests/test_module_governance_organ.py",
            "-q",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        print("[alt13-closure-gate] FAIL: pytest")
        return 1
    print("[alt13-closure-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
