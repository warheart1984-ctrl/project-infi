#!/usr/bin/env python3
"""patch_execution_preview_organ governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_patch_execution_preview_organ.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[patch-execution-preview-organ-gate] FAIL")
        return 1
    print("[patch-execution-preview-organ-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
