#!/usr/bin/env python3
"""Governance gate for Autonomous Org Mesh v4 (v41–v42)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/mesh/autopilot.py",
    "docs/subsystems/platform/AUTONOMOUS_ORG_MESH_CONTRACT.md",
    "docs/proof/platform/PLATFORM_V41_V42_PROOF_BUNDLE.md",
    "platform/v4150_routes.py",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    text = (ROOT / "platform/mesh/autopilot.py").read_text(encoding="utf-8")
    if "dry_run" not in text or "apply" not in text:
        print("FAIL: autopilot missing dry_run/apply modes")
        sys.exit(1)
    print("OK: platform mesh v4 (autonomous) governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
