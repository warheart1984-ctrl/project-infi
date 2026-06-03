#!/usr/bin/env python3
"""Alt-12.2 OTEM and predictive lane closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
OTEM_PROOF = _ROOT / "docs/proof/platform/OTEM_BOUNDED_V1_PROOF.md"
PREDICTIVE_PROOF = _ROOT / "docs/proof/platform/PREDICTIVE_LANE_V1_PROOF.md"
EXECUTION_PROOF = _ROOT / "docs/proof/platform/EXECUTION_DEPTH_V1_PROOF.md"


def main() -> int:
    errors: list[str] = []
    for proof in (OTEM_PROOF, PREDICTIVE_PROOF, EXECUTION_PROOF):
        if not proof.is_file():
            errors.append(f"missing proof: {proof.relative_to(_ROOT)}")

    if errors:
        for err in errors:
            print(f"[alt12-closure-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_otem_bounded_organ.py",
            "tests/test_governed_realtime_lane_organ.py",
            "tests/test_patch_apply_organ.py",
            "tests/test_run_ledger_organ.py",
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
        print("[alt12-closure-gate] FAIL: pytest")
        return 1
    print("[alt12-closure-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
