#!/usr/bin/env python3
"""Narrative Trust Pack governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable

    print("[narrative-gate] running unit tests")
    result = subprocess.run(
        [python, "-m", "pytest", "tests/test_narrative_trust_pack.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[narrative-gate] FAIL: pytest")
        return 1

    print("[narrative-gate] running bridge tests")
    bridge = subprocess.run(
        [python, "-m", "pytest", "tests/test_capability_bridge_alt3.py::TestCapabilityBridgeAlt3::test_narrative_trust_pack_pack_verify_signoff_via_bridge", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if bridge.returncode != 0:
        print(bridge.stdout)
        print(bridge.stderr)
        print("[narrative-gate] FAIL: bridge pytest")
        return 1

    print("[narrative-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
