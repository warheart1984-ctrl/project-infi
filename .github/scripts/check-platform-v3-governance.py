#!/usr/bin/env python3
"""Umbrella governance gate for Platform Membrane v3 (v15–v20)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = [
    "check-platform-v3-spec-governance.py",
    "check-platform-mesh-governance.py",
    "check-platform-marketplace-governance.py",
    "check-platform-proof-federation-governance.py",
    "check-platform-v8-v14-governance.py",
]


def main() -> None:
    for name in SCRIPTS:
        path = ROOT / ".github/scripts" / name
        if not path.is_file():
            print(f"FAIL: missing {name}")
            sys.exit(1)
        subprocess.run([sys.executable, str(path)], check=True, cwd=ROOT)
    print("OK: platform v3 governance umbrella")
    sys.exit(0)


if __name__ == "__main__":
    main()
