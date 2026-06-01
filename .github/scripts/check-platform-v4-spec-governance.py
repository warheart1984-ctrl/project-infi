#!/usr/bin/env python3
"""Governance gate for Platform Membrane v4 spec pack."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "docs/runtime/PLATFORM_MEMBRANE_V4_SPEC.md",
    "docs/subsystems/platform/PLATFORM_EVENT_MEMBRANE_CONTRACT.md",
    "docs/subsystems/platform/OPERATOR_MESH_CONTRACT.md",
    "docs/subsystems/platform/WORKFLOW_MARKETPLACE_SCHEMA.md",
    "docs/subsystems/platform/PROOF_FEDERATION_PROTOCOL.md",
    "docs/subsystems/platform/PLATFORM_API_CONTRACT.md",
    "platform/schemas/webhook_subscription.v1.json",
    "platform/schemas/proof_attestation_bundle.v1.json",
    "docs/proof/platform/PLATFORM_V21_V22_PROOF_BUNDLE.md",
    "docs/proof/platform/PLATFORM_V29_V30_PROOF_BUNDLE.md",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    api = (ROOT / "docs/subsystems/platform/PLATFORM_API_CONTRACT.md").read_text(encoding="utf-8")
    if "v4" not in api[:200].lower() and "v5" not in api[:200].lower():
        print("FAIL: API contract missing v4/v5 lineage")
        sys.exit(1)
    if "v5" in api[:200].lower() and "v4 routes" not in api.lower():
        print("FAIL: v5 API contract must include v4 route lineage")
        sys.exit(1)
    proof = (ROOT / "docs/subsystems/platform/PROOF_FEDERATION_PROTOCOL.md").read_text(encoding="utf-8")
    if "v3" not in proof or "ed25519" not in proof:
        print("FAIL: proof federation v3 section missing")
        sys.exit(1)
    print("OK: platform v4 spec pack governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
