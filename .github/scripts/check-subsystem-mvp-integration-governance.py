#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_subsystem_mvp_integration.py", "-q"],
        cwd=root,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
