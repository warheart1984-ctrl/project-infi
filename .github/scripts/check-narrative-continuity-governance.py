#!/usr/bin/env python3
"""Narrative Continuity Organ governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable
    organ = subprocess.run(
        [python, "-m", "pytest", "tests/test_narrative_continuity_organ.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if organ.returncode != 0:
        print(organ.stdout)
        print(organ.stderr)
        print("[narrative-continuity-gate] FAIL: organ tests")
        return 1
    nova = subprocess.run(
        [python, ".github/scripts/check-nova-narrative-continuity.py"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if nova.returncode != 0:
        print(nova.stdout)
        print(nova.stderr)
        print("[narrative-continuity-gate] FAIL: nova continuity proof")
        return 1
    print("[narrative-continuity-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
