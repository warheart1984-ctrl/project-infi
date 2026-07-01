#!/usr/bin/env python3
"""Umbrella governance gate for Platform Membrane v4 (v21–v30 + v3 spec)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = [
    "check-platform-v4-spec-governance.py",
    "check-platform-v3-governance.py",
    "check-platform-mesh-v2-governance.py",
    "check-platform-marketplace-v2-governance.py",
    "check-platform-proof-v2-governance.py",
    "check-platform-sovereign-governance.py",
]


def main() -> None:
    for name in SCRIPTS:
        path = ROOT / ".github/scripts" / name
        subprocess.run([sys.executable, str(path)], check=True, cwd=ROOT)
    print("OK: platform v4 governance umbrella")
    sys.exit(0)


if __name__ == "__main__":
    main()
