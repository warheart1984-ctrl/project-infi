#!/usr/bin/env python3
"""Intent Agency Organ governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable
    organ = subprocess.run(
        [python, "-m", "pytest", "tests/test_intent_agency_organ.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if organ.returncode != 0:
        print(organ.stdout)
        print(organ.stderr)
        print("[intent-agency-gate] FAIL: organ tests")
        return 1
    nova = subprocess.run(
        [python, ".github/scripts/check-nova-intent-agency.py"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if nova.returncode != 0:
        print(nova.stdout)
        print(nova.stderr)
        print("[intent-agency-gate] FAIL: nova intent agency proof")
        return 1
    print("[intent-agency-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
