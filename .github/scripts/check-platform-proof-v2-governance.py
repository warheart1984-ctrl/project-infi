#!/usr/bin/env python3
"""Governance gate for Platform Membrane v25–v28 (proof federation v2)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/proof/signing.py",
    "platform/proof/runners.py",
    "platform/proof/quorum.py",
    "docs/subsystems/platform/PROOF_FEDERATION_PROTOCOL.md",
    "docs/proof/platform/PLATFORM_V25_V28_PROOF_BUNDLE.md",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    quorum = (ROOT / "platform/proof/quorum.py").read_text(encoding="utf-8")
    if "disputed" not in quorum or "hash_mismatch" not in quorum:
        print("FAIL: dispute drift wiring missing in quorum")
        sys.exit(1)
    replay = (ROOT / "platform/replay.py").read_text(encoding="utf-8")
    if "runner_reports" not in replay:
        print("FAIL: replay v2 missing")
        sys.exit(1)
    print("OK: platform proof v2 governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
