#!/usr/bin/env python3
"""Governance gate for Inter-Membrane Exchange (v45–v46)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/exchange/envelope.py",
    "platform/exchange/intra_tenant.py",
    "platform/exchange/peer.py",
    "docs/subsystems/platform/INTER_MEMBRANE_EXCHANGE_PROTOCOL.md",
    "docs/proof/platform/PLATFORM_V45_V46_PROOF_BUNDLE.md",
    "platform/schemas/membrane_envelope.v1.json",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    print("OK: platform exchange governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
