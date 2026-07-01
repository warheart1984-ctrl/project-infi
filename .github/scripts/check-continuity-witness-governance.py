#!/usr/bin/env python3
"""Continuity Witness Organ governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable
    result = subprocess.run(
        [python, "-m", "pytest", "tests/test_continuity_witness_organ.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[continuity-witness-gate] FAIL")
        return 1
    print("[continuity-witness-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
