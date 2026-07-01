#!/usr/bin/env python3
"""Governance gate for Platform Membrane v5 spec pack (Sixth arc)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "docs/runtime/PLATFORM_MEMBRANE_V5_SPEC.md",
    "docs/subsystems/platform/AUTONOMOUS_ORG_MESH_CONTRACT.md",
    "docs/subsystems/platform/GLOBAL_PROOF_NETWORK_CONTRACT.md",
    "docs/subsystems/platform/INTER_MEMBRANE_EXCHANGE_PROTOCOL.md",
    "docs/subsystems/platform/PLATFORM_LEDGER_V2_CONTRACT.md",
    "docs/subsystems/platform/SOVEREIGN_RUNTIME_CONTRACT.md",
    "platform/schemas/routing_policy.v1.json",
    "platform/schemas/proof_witness.v1.json",
    "platform/schemas/membrane_envelope.v1.json",
    "platform/schemas/platform_ledger_entry.v1.json",
    "platform/schemas/sovereign_profile.v1.json",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    api = (ROOT / "docs/subsystems/platform/PLATFORM_API_CONTRACT.md").read_text(encoding="utf-8")
    if "v5" not in api[:150].lower() and "Sixth" not in api:
        print("FAIL: API contract missing v5 sixth arc")
        sys.exit(1)
    print("OK: platform v5 spec pack governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
