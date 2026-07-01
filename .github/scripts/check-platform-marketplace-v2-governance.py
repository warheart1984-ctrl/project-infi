#!/usr/bin/env python3
"""Governance gate for Platform Membrane v23–v24 (marketplace v2)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/marketplace/lifecycle.py",
    "platform/marketplace/analytics.py",
    "docs/subsystems/platform/WORKFLOW_MARKETPLACE_SCHEMA.md",
    "docs/proof/platform/PLATFORM_V23_V24_PROOF_BUNDLE.md",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    listing = (ROOT / "platform/schemas/workflow_listing.v1.json").read_text(encoding="utf-8")
    if "approval_status" not in listing:
        print("FAIL: workflow_listing missing approval_status")
        sys.exit(1)
    print("OK: platform marketplace v2 governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
