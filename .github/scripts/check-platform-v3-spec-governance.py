#!/usr/bin/env python3
"""Governance gate for Platform Membrane v3 spec pack."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "docs/runtime/PLATFORM_MEMBRANE_V3_SPEC.md",
    "docs/subsystems/platform/OPERATOR_MESH_CONTRACT.md",
    "docs/subsystems/platform/WORKFLOW_MARKETPLACE_SCHEMA.md",
    "docs/subsystems/platform/PROOF_FEDERATION_PROTOCOL.md",
    "docs/subsystems/platform/PLATFORM_API_CONTRACT.md",
    "platform/schemas/operator_presence.v1.json",
    "platform/schemas/job_assignment.v1.json",
    "platform/schemas/mesh_event.v1.json",
    "platform/schemas/on_call_schedule.v1.json",
    "platform/schemas/handoff_bundle.v1.json",
    "platform/schemas/workflow_listing_step.v1.json",
    "platform/schemas/workflow_listing.v1.json",
    "platform/schemas/proof_attestation.v1.json",
]


def main() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            print(f"FAIL: missing {rel}")
            sys.exit(1)
    contract = (ROOT / "docs/subsystems/platform/PLATFORM_API_CONTRACT.md").read_text(encoding="utf-8")
    if "API Contract v1" in contract and "v3" not in contract[:200]:
        print("FAIL: API contract not v3")
        sys.exit(1)
    print("OK: platform v3 spec pack governance")
    sys.exit(0)


if __name__ == "__main__":
    main()
