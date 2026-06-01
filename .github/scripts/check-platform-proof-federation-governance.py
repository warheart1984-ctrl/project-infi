#!/usr/bin/env python3
"""Governance gate for Platform Proof Federation v19–v20."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required = [
        "platform/proof/federation.py",
        "platform/proof/quorum.py",
        "platform/schemas/proof_attestation.v1.json",
        "docs/proof/platform/cross_machine/REPLAY_MANIFEST.v2.template.json",
        "docs/proof/platform/PLATFORM_V19_V20_PROOF_BUNDLE.md",
    ]
    for rel in required:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    print("OK: platform proof federation governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
