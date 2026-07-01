#!/usr/bin/env python3
"""Governance gate for Global Proof Network (v43–v44)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/proof/witnesses.py",
    "docs/subsystems/platform/GLOBAL_PROOF_NETWORK_CONTRACT.md",
    "docs/proof/platform/PLATFORM_V43_V44_PROOF_BUNDLE.md",
    "platform/schemas/proof_witness.v1.json",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    q = (ROOT / "platform/proof/quorum.py").read_text(encoding="utf-8")
    w = (ROOT / "platform/proof/witnesses.py").read_text(encoding="utf-8")
    if "witness_policy_satisfied" not in q:
        print("FAIL: quorum missing witness_policy_satisfied")
        sys.exit(1)
    if "effective_witness_quorum" not in w:
        print("FAIL: witnesses missing effective_witness_quorum")
        sys.exit(1)
    print("OK: platform proof network governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
