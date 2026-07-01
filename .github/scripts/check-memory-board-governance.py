#!/usr/bin/env python3
"""Jarvis Memory Board governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_jarvis_memory_board.py",
            "tests/test_memory_board_enforcer.py",
            "-q",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[memory-board-gate] FAIL")
        return 1
    print("[memory-board-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
