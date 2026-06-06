#!/usr/bin/env python3
"""Workflow-family organ registry governance gate (structure layer)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

REQUIRED_FAMILY_IDS = (
    "knowledge_work",
    "business_workflows",
    "creative_workflows",
    "data_workflows",
    "operational_workflows",
    "personal_workflows",
)

REQUIRED_DOCS = [
    "governance/workflow_family_registry.v1.json",
    "governance/workflow_plugin_bundles.v1.json",
    "docs/runtime/AAIS_ANATOMICAL_LAYERS.md",
    "docs/proof/platform/WORKFLOW_FAMILY_ORGANS_V1_PROOF.md",
]


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_DOCS:
        if not (REPO / rel).is_file():
            errors.append(f"missing:{rel}")

    registry_path = REPO / "governance/workflow_family_registry.v1.json"
    bundles_path = REPO / "governance/workflow_plugin_bundles.v1.json"

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    bundles_doc = json.loads(bundles_path.read_text(encoding="utf-8"))

    if registry.get("workflow_family_registry_version") != "workflow_family_registry.v1":
        errors.append("registry:invalid version")

    bundle_ids = {
        str(item.get("workflow_id"))
        for item in (bundles_doc.get("bundles") or [])
        if item.get("workflow_id")
    }

    families = list(registry.get("families") or [])
    seen: set[str] = set()

    for family in families:
        identity = family.get("identity") or {}
        family_id = str(identity.get("family_id") or "")
        if not family_id:
            errors.append("family:missing family_id")
            continue
        if family_id in seen:
            errors.append(f"family:duplicate:{family_id}")
        seen.add(family_id)

        abilities = list(family.get("abilities") or [])
        chains = list(family.get("chains") or [])
        if not abilities:
            errors.append(f"family:{family_id}:missing abilities")
        if not chains:
            errors.append(f"family:{family_id}:missing chains")

        for chain in chains:
            bundle_id = str(chain.get("workflow_bundle_id") or chain.get("chain_id") or "")
            if bundle_id and bundle_id not in bundle_ids:
                errors.append(f"family:{family_id}:unknown bundle:{bundle_id}")

        routing = family.get("routing") or {}
        if not routing.get("intent_signals"):
            errors.append(f"family:{family_id}:missing intent_signals")

    missing_families = [fid for fid in REQUIRED_FAMILY_IDS if fid not in seen]
    if missing_families:
        errors.append(f"families:missing required ids: {', '.join(missing_families)}")

    if len(seen) != 6:
        errors.append(f"families:expected 6 organs, got {len(seen)}")

    if errors:
        print("[workflow-family-gate] FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[workflow-family-gate] PASS (families={len(seen)}, bundles={len(bundle_ids)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
