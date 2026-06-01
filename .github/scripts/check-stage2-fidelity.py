#!/usr/bin/env python3
"""Stage 2 fidelity metrics gate (INV-6)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage 2 fidelity metric fixtures.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    print("[stage2-fidelity-gate] running unit tests")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_stage2_fidelity_metrics.py", "-q"],
        cwd=str(repo_root),
        check=False,
    )
    if proc.returncode != 0:
        print("[stage2-fidelity-gate] FAIL")
        return proc.returncode
    print("[stage2-fidelity-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
