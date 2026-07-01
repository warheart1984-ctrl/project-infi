#!/usr/bin/env python3
"""Slingshot governance gate — preload fixture + unit tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable
    case_id = "slingshot-ci-gate"
    fixture = root / "mechanic" / "fixtures" / "sample-customer-repo-v2"
    trace = fixture / "traces" / "session.ndjson"

    print("[slingshot-gate] running unit tests")
    result = subprocess.run(
        [python, "-m", "pytest", "tests/test_slingshot.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[slingshot-gate] FAIL: pytest")
        return 1

    print("[slingshot-gate] running preload on sample-customer-repo-v2")
    preload = subprocess.run(
        [
            python,
            "-m",
            "slingshot",
            "preload",
            "--case-id",
            case_id,
            "--repo",
            str(fixture),
            "--trace-path",
            str(trace),
            "--output",
            str(root / ".runtime" / "slingshot" / f"{case_id}-preload.json"),
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if preload.returncode not in {0, 1}:
        print(preload.stdout)
        print(preload.stderr)
        print("[slingshot-gate] FAIL: preload command error")
        return 1

    frame_file = root / ".runtime" / "slingshot" / case_id / "SLINGSHOT_FRAME.v1.json"
    if not frame_file.is_file():
        print("[slingshot-gate] FAIL: SLINGSHOT_FRAME missing")
        return 1
    frame = json.loads(frame_file.read_text(encoding="utf-8"))
    if not frame.get("launch_blocked"):
        print("[slingshot-gate] FAIL: v2 fixture should block launch (Class III / signoff)")
        return 1
    if int(frame.get("drift_count") or 0) < 1:
        print("[slingshot-gate] FAIL: expected drifts on v2 fixture")
        return 1

    print("[slingshot-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
