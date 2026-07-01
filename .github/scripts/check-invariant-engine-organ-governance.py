#!/usr/bin/env python3
"""Invariant Engine Organ governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable
    result = subprocess.run(
        [python, "-m", "pytest", "tests/test_invariant_engine_organ.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[invariant-engine-organ-gate] FAIL")
        return 1
    print("[invariant-engine-organ-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
