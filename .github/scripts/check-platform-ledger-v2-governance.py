#!/usr/bin/env python3
"""Governance gate for Platform Ledger v2 (v47–v48)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "platform/ledger/writer.py",
    "platform/ledger/hooks.py",
    "platform/ledger/ugr_bridge.py",
    "docs/subsystems/platform/PLATFORM_LEDGER_V2_CONTRACT.md",
    "docs/proof/platform/PLATFORM_V47_V48_PROOF_BUNDLE.md",
    "platform/schemas/platform_ledger_entry.v1.json",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    main_py = (ROOT / "platform/__main__.py").read_text(encoding="utf-8")
    if "ledger" not in main_py or "export" not in main_py:
        print("FAIL: platform CLI missing ledger export")
        sys.exit(1)
    print("OK: platform ledger v2 governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
