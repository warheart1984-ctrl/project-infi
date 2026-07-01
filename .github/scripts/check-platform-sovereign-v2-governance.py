#!/usr/bin/env python3
"""Governance gate for Sovereign control plane v2 (v39–v40)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "docs/proof/platform/PLATFORM_V39_V40_PROOF_BUNDLE.md",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    routes = (ROOT / "platform/v3140_routes.py").read_text(encoding="utf-8")
    if "compliance/policy" not in routes or "exports/usage" not in routes:
        print("FAIL: sovereign v2 routes missing")
        sys.exit(1)
    tenant = (ROOT / "platform/sovereign/tenant.py").read_text(encoding="utf-8")
    if "webhook_delivery_failures" not in tenant:
        print("FAIL: tenant summary webhook failures missing")
        sys.exit(1)
    print("OK: platform sovereign v2 governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
