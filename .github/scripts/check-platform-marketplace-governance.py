#!/usr/bin/env python3
"""Governance gate for Platform Workflow Marketplace v17–v18."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required = [
        "platform/marketplace/publish.py",
        "platform/marketplace/catalog.py",
        "platform/marketplace/install.py",
        "platform/marketplace/visibility.py",
        "platform/schemas/workflow_listing.v1.json",
        "frontend/src/pages/PlatformMarketplace.jsx",
        "docs/proof/platform/PLATFORM_V17_V18_PROOF_BUNDLE.md",
    ]
    for rel in required:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    print("OK: platform marketplace governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
