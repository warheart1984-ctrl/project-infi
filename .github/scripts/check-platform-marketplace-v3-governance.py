#!/usr/bin/env python3
"""Governance gate for Marketplace v3 (v33–v34)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/marketplace/reviews.py",
    "platform/marketplace/catalog.py",
    "docs/proof/platform/PLATFORM_V33_V34_PROOF_BUNDLE.md",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    routes = (ROOT / "platform/v3140_routes.py").read_text(encoding="utf-8")
    if "/marketplace/catalog" not in routes:
        print("FAIL: catalog route missing")
        sys.exit(1)
    print("OK: platform marketplace v3 governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
