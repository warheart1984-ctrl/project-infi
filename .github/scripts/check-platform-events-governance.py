#!/usr/bin/env python3
"""Governance gate for Platform Event Membrane (v31–v32)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/events/subscriptions.py",
    "platform/events/dispatch.py",
    "docs/subsystems/platform/PLATFORM_EVENT_MEMBRANE_CONTRACT.md",
    "docs/proof/platform/PLATFORM_V31_V32_PROOF_BUNDLE.md",
    "platform/schemas/webhook_subscription.v1.json",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    print("OK: platform events governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
