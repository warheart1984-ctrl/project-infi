#!/usr/bin/env python3
"""beatbox_lane_organ governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_beatbox_lane_organ.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[beatbox-lane-organ-gate] FAIL")
        return 1
    print("[beatbox-lane-organ-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
