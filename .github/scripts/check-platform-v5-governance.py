#!/usr/bin/env python3
"""Umbrella governance gate for Platform Membrane v5 (v31–v40)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = [
    "check-platform-v5-spec-governance.py",
    "check-platform-v4-governance.py",
    "check-platform-events-governance.py",
    "check-platform-marketplace-v3-governance.py",
    "check-platform-proof-v3-governance.py",
    "check-platform-mesh-v3-governance.py",
    "check-platform-sovereign-v2-governance.py",
]


def main() -> None:
    for name in SCRIPTS:
        subprocess.run([sys.executable, str(ROOT / ".github/scripts" / name)], check=True, cwd=ROOT)
    print("OK: platform v5 governance umbrella")
    sys.exit(0)


if __name__ == "__main__":
    main()
