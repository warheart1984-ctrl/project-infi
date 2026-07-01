#!/usr/bin/env python3
"""Platform v1.1 governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

REQUIRED = [
    "docs/subsystems/platform/ONBOARDING.md",
    "platform/schemas/platform_role_binding.v1.json",
    "platform/policy/engine.py",
    "platform/jobs/graph.py",
    "platform/extra_routes.py",
    "frontend/src/pages/PlatformJobDetail.jsx",
]


def main() -> int:
    errors = [f"missing:{r}" for r in REQUIRED if not (REPO / r).is_file()]
    if errors:
        for e in errors:
            print(e)
        return 1
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_platform_schemas.py", "tests/test_platform_api_smoke.py",
         "tests/test_platform_v11.py", "tests/test_platform_onboarding.py", "tests/test_platform_graph.py", "-q"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        return proc.returncode
    print("platform-v1-1-gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
