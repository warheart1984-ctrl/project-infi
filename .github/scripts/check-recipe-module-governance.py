#!/usr/bin/env python3
"""Recipe Module governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable

    print("[recipe-module-gate] running unit tests")
    result = subprocess.run(
        [python, "-m", "pytest", "tests/test_recipe_module.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[recipe-module-gate] FAIL: pytest")
        return 1

    print("[recipe-module-gate] inspecting fixture pack")
    inspect = subprocess.run(
        [python, "-m", "tools.recipe", "--recipe-id", "onboarding-v1", "--signoff-ack"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if inspect.returncode != 0:
        print(inspect.stdout)
        print(inspect.stderr)
        print("[recipe-module-gate] FAIL: inspect")
        return 1

    print("[recipe-module-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
