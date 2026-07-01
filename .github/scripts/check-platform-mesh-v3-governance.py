#!/usr/bin/env python3
"""Governance gate for Operator Mesh v3 (v37–v38)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/mesh/retention.py",
    "platform/mesh/queue.py",
    "docs/proof/platform/PLATFORM_V37_V38_PROOF_BUNDLE.md",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    mesh = (ROOT / "docs/subsystems/platform/OPERATOR_MESH_CONTRACT.md").read_text(encoding="utf-8")
    if "v3" not in mesh or "assignment_queue" not in mesh:
        print("FAIL: mesh v3 contract section missing")
        sys.exit(1)
    print("OK: platform mesh v3 governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
