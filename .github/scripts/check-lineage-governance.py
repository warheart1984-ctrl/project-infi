#!/usr/bin/env python3
"""Lineage governance gate — pytest + lineage graph smoke."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable
    fixture = root / "tools" / "ul" / "fixtures" / "lineage_multi_hop.json"

    print("[lineage-gate] running unit tests")
    result = subprocess.run(
        [python, "-m", "pytest", "tests/test_ul_lineage.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[lineage-gate] FAIL: pytest")
        return 1

    print("[lineage-gate] running lineage graph smoke")
    smoke = subprocess.run(
        [python, "-m", "tools.ul.smoke", "--lineage-graph", str(fixture), "--no-pytest"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if smoke.returncode != 0:
        print(smoke.stdout)
        print(smoke.stderr)
        print("[lineage-gate] FAIL: lineage smoke")
        return 1

    drift = subprocess.run(
        [python, "-m", "tools.ul.drift", "--lane", "lineage"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if drift.returncode != 0:
        print(drift.stdout)
        print(drift.stderr)
        print("[lineage-gate] FAIL: lineage drift lane")
        return 1

    print("[lineage-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
