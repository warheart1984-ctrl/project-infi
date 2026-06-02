#!/usr/bin/env python3
"""Reflection Runtime Organ governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable
    result = subprocess.run(
        [python, "-m", "pytest", "tests/test_reflection_runtime_organ.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[reflection-runtime-gate] FAIL")
        return 1
    print("[reflection-runtime-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
