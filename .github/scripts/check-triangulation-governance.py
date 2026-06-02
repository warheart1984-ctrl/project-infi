#!/usr/bin/env python3
"""Triangulation governance gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable
    case_id = "tri-demo-001"
    tri_root = root / ".runtime" / "triangulation" / "ci-gate"

    print("[triangulation-gate] running unit tests")
    result = subprocess.run(
        [python, "-m", "pytest", "tests/test_triangulation.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        return 1

    print("[triangulation-gate] running correlate on fixture")
    correlate = subprocess.run(
        [
            python,
            "-m",
            "triangulation",
            "correlate",
            "--case-id",
            case_id,
            "--fixture",
            "tri-demo-001",
            "--triangulation-root",
            str(tri_root),
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if correlate.returncode != 0:
        print(correlate.stdout)
        print(correlate.stderr)
        return 1

    artifact = tri_root / case_id / "triangulation.v1.json"
    if not artifact.is_file():
        print("[triangulation-gate] FAIL: artifact missing")
        return 1
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    if not payload.get("correlation_edges"):
        print("[triangulation-gate] FAIL: no correlation edges")
        return 1
    proven = any(
        edge.get("claim_label") == "proven"
        for edge in payload.get("correlation_edges") or []
    )
    if not proven:
        print("[triangulation-gate] FAIL: no proven edge")
        return 1

    print("[triangulation-gate] running bridge tests")
    bridge = subprocess.run(
        [python, "-m", "pytest", "tests/test_capability_bridge_alt3.py::TestCapabilityBridgeAlt3::test_forensic_triangulation_correlate_via_bridge", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if bridge.returncode != 0:
        print(bridge.stdout)
        print(bridge.stderr)
        return 1

    print("[triangulation-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
