#!/usr/bin/env python3
"""Alt-14.2 route choice and perception closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PERCEPTION_PROOF = _ROOT / "docs/proof/platform/PERCEPTION_GATEWAY_V1_PROOF.md"
ROUTE_PROOF = _ROOT / "docs/proof/platform/ROUTE_CHOICE_V1_PROOF.md"
SPATIAL_PROOF = _ROOT / "docs/proof/platform/SPATIAL_SYMBOLIC_V1_PROOF.md"


def main() -> int:
    errors: list[str] = []
    for proof in (PERCEPTION_PROOF, ROUTE_PROOF, SPATIAL_PROOF):
        if not proof.is_file():
            errors.append(f"missing proof: {proof.relative_to(_ROOT)}")

    if errors:
        for err in errors:
            print(f"[alt14-closure-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_document_vision_organ.py",
            "tests/test_ui_vision_organ.py",
            "tests/test_perception_gateway_organ.py",
            "tests/test_spatial_reasoning_organ.py",
            "tests/test_mystic_engine_organ.py",
            "tests/test_perception_lane_organ.py",
            "tests/test_route_choice_organ.py",
            "tests/test_specialist_route_organ.py",
            "tests/test_provider_route_organ.py",
            "-q",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        print("[alt14-closure-gate] FAIL: pytest")
        return 1
    print("[alt14-closure-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
