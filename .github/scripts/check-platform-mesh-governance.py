#!/usr/bin/env python3
"""Governance gate for Platform Operator Mesh v15–v16."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required = [
        "platform/mesh/presence.py",
        "platform/mesh/assignment.py",
        "platform/mesh/handoff.py",
        "platform/mesh/on_call.py",
        "frontend/src/pages/PlatformMesh.jsx",
        "docs/proof/platform/PLATFORM_V15_V16_PROOF_BUNDLE.md",
    ]
    for rel in required:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    for mod in (ROOT / "platform/mesh").glob("*.py"):
        if mod.name == "__init__.py":
            continue
        text = mod.read_text(encoding="utf-8")
        if "JobRegistry" in text or "from src.api" in text:
            print(f"FAIL: MA-13 violation in {mod}")
            sys.exit(1)
    print("OK: platform mesh governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
