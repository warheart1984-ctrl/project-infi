#!/usr/bin/env python3
"""Governance gate for Platform Membrane v29–v30 (sovereign control plane)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/sovereign/exports.py",
    "platform/sovereign/tenant.py",
    "docs/proof/platform/PLATFORM_V29_V30_PROOF_BUNDLE.md",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    routes = (ROOT / "platform/v2130_routes.py").read_text(encoding="utf-8")
    if "/exports/audit" not in routes or "/tenants/" not in routes:
        print("FAIL: sovereign routes missing")
        sys.exit(1)
    print("OK: platform sovereign governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
