#!/usr/bin/env python3
"""Governance gate for Sovereign Runtime (v49–v50)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/sovereign/profile.py",
    "platform/sovereign/export_pack.py",
    "docs/subsystems/platform/SOVEREIGN_RUNTIME_CONTRACT.md",
    "docs/proof/platform/PLATFORM_V49_V50_PROOF_BUNDLE.md",
    "platform/schemas/sovereign_profile.v1.json",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    console = (ROOT / "frontend/src/pages/PlatformConsole.jsx").read_text(encoding="utf-8")
    if "sovereign" not in console.lower():
        print("FAIL: PlatformConsole missing sovereign panel")
        sys.exit(1)
    print("OK: platform sovereign runtime governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
