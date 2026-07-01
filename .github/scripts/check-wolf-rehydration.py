#!/usr/bin/env python3
"""Wolf rehydration harness gate (INV-1 asserted lane)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate INV-1 rehydration harness.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    print("[wolf-rehydration-gate] running harness tests")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_wolf_rehydration_harness.py", "-q"],
        cwd=str(repo_root),
        check=False,
    )
    if proc.returncode != 0:
        print("[wolf-rehydration-gate] FAIL")
        return proc.returncode
    print("[wolf-rehydration-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
