#!/usr/bin/env python3
"""Imagine Generator governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable

    print("[imagine-generator-gate] running unit tests")
    result = subprocess.run(
        [
            python,
            "-m",
            "pytest",
            "tests/test_imagine_generator.py",
            "tests/test_imagine_grok.py",
            "tests/test_capability_bridge_alt3.py",
            "tests/test_alt3_lineage.py",
            "-q",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        return 1

    print("[imagine-generator-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
