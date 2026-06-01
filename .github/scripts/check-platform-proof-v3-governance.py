#!/usr/bin/env python3
"""Governance gate for Proof Federation v3 (v35–v36)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/proof/bundles.py",
    "platform/schemas/proof_attestation_bundle.v1.json",
    "docs/proof/platform/PLATFORM_V35_V36_PROOF_BUNDLE.md",
    "docs/proof/platform/cross_machine/REPLAY_MANIFEST.v3.template.json",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    signing = (ROOT / "platform/proof/signing.py").read_text(encoding="utf-8")
    if "ed25519" not in signing or "post_replay_attestations" not in (ROOT / "platform/replay.py").read_text(encoding="utf-8"):
        print("FAIL: proof v3 implementation incomplete")
        sys.exit(1)
    print("OK: platform proof v3 governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
