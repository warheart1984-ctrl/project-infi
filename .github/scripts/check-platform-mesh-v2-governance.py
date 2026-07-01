#!/usr/bin/env python3
"""Governance gate for Platform Membrane v21–v22 (mesh v2)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/mesh/stream.py",
    "platform/mesh/policy.py",
    "platform/v2130_routes.py",
    "docs/proof/platform/PLATFORM_V21_V22_PROOF_BUNDLE.md",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    text = (ROOT / "platform/v2130_routes.py").read_text(encoding="utf-8")
    if "mesh/events/stream" not in text:
        print("FAIL: mesh SSE route missing")
        sys.exit(1)
    print("OK: platform mesh v2 governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
