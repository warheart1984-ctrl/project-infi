#!/usr/bin/env python3
"""Governance gate for UGR Ledger Bridge v1."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "docs/subsystems/ugr/UGR_LEDGER_BRIDGE_SPEC.md",
    "src/ugr/ledger_bridge/bridge.py",
    "src/ugr/ledger_bridge/invariants.py",
    "platform/ledger/ugr_bridge.py",
    "docs/proof/ugr/UGR_LEDGER_BRIDGE_V1_PROOF_BUNDLE.md",
    "tests/test_ugr_ledger_bridge.py",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    bridge = (ROOT / "src/ugr/ledger_bridge/bridge.py").read_text(encoding="utf-8")
    if "traverse" not in bridge or "query_trace" not in bridge:
        print("FAIL: LedgerBridge contract incomplete")
        sys.exit(1)
    organ = (ROOT / "src/ugr/trust_bundle/organ.py").read_text(encoding="utf-8")
    if "receive_claim" not in organ:
        print("FAIL: TrustBundleOrgan missing receive_claim")
        sys.exit(1)
    print("OK: ugr ledger bridge v1 governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
