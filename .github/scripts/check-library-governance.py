#!/usr/bin/env python3
"""AAIS library registry governance gate (structure layer)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

REQUIRED_DOCS = [
    "docs/contracts/AAIS_LIBRARY_ADMISSION_PROTOCOL.md",
    "docs/contracts/PLUGIN_GOVERNANCE_CONTRACT.md",
    "governance/aais_library_registry.v1.json",
    "governance/workflow_plugin_bundles.v1.json",
]

LIBRARY_CLASSES = {
    "mcp",
    "cursor_skill",
    "hf_agent_skill",
    "native_capability",
    "workflow",
}

EXPECTED_PREFIX_COUNTS = {
    "lib_skill_": 5,
    "lib_hf_": 10,
    "lib_workflow_": 27,
}


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_DOCS:
        if not (REPO / rel).is_file():
            errors.append(f"missing:{rel}")

    registry_path = REPO / "governance/aais_library_registry.v1.json"
    bundles_path = REPO / "governance/workflow_plugin_bundles.v1.json"

    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[library-gate] FAIL: cannot parse registry ({exc})")
        return 1

    try:
        bundles_doc = json.loads(bundles_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[library-gate] FAIL: cannot parse workflow bundles ({exc})")
        return 1

    if registry.get("aais_library_registry_version") != "aais_library_registry.v1":
        errors.append("registry:invalid version")

    bundle_ids = {
        str(item.get("workflow_id"))
        for item in (bundles_doc.get("bundles") or [])
        if item.get("workflow_id")
    }
    if len(bundle_ids) != 27:
        errors.append(f"bundles:expected 27 workflow_id entries, got {len(bundle_ids)}")

    libraries = list(registry.get("libraries") or [])
    if not libraries:
        errors.append("registry:no libraries")

    seen_ids: set[str] = set()
    prefix_counts: dict[str, int] = {key: 0 for key in EXPECTED_PREFIX_COUNTS}

    for entry in libraries:
        identity = entry.get("identity") or {}
        library_id = str(identity.get("library_id") or "")
        library_class = str(identity.get("library_class") or "")

        if not library_id:
            errors.append("library:missing library_id")
            continue
        if library_id in seen_ids:
            errors.append(f"library:duplicate library_id:{library_id}")
        seen_ids.add(library_id)

        if library_class not in LIBRARY_CLASSES:
            errors.append(f"library:{library_id}:invalid class:{library_class}")

        mount = entry.get("mount") or {}
        if not mount.get("plug_patterns"):
            errors.append(f"library:{library_id}:missing mount.plug_patterns")

        governance = entry.get("governance") or {}
        cisiv = list(governance.get("cisiv_path") or [])
        if cisiv and cisiv[-1] != "verification":
            errors.append(f"library:{library_id}:cisiv_path must end with verification")

        for prefix in prefix_counts:
            if library_id.startswith(prefix):
                prefix_counts[prefix] += 1

        if library_class == "workflow":
            routing = entry.get("routing") or {}
            category = str(routing.get("workflow_catalog_category") or "")
            if not category:
                errors.append(f"library:{library_id}:workflow missing catalog category")

    for prefix, expected in EXPECTED_PREFIX_COUNTS.items():
        actual = prefix_counts[prefix]
        if actual != expected:
            errors.append(f"count:{prefix} expected {expected}, got {actual}")

    if errors:
        print("[library-gate] FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(
        "[library-gate] PASS "
        f"(libraries={len(libraries)}, bundles={len(bundle_ids)}, "
        f"skills={prefix_counts['lib_skill_']}, hf={prefix_counts['lib_hf_']}, "
        f"workflows={prefix_counts['lib_workflow_']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
