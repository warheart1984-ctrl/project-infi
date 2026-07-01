#!/usr/bin/env python3
"""Umbrella governance gate for Platform Membrane v6 (v41–v50, Sixth arc)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = [
    "check-platform-v5-governance.py",
    "check-platform-v5-spec-governance.py",
    "check-platform-ledger-v2-governance.py",
    "check-platform-proof-network-governance.py",
    "check-platform-exchange-governance.py",
    "check-platform-mesh-v4-governance.py",
    "check-platform-sovereign-runtime-governance.py",
]


def main() -> None:
    for name in SCRIPTS:
        subprocess.run([sys.executable, str(ROOT / ".github/scripts" / name)], check=True, cwd=ROOT)
    print("OK: platform v6 governance umbrella")
    sys.exit(0)


if __name__ == "__main__":
    main()
