#!/usr/bin/env python3
"""Nova Cortex lobe capability governance gate for CI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Nova Cortex lobe capability justification.")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from src.cog_runtime import nova_cortex_spec
    from src.cog_runtime.capability_governance import (
        CORTEX_MODULE_CAPABILITY_MATRIX,
        NOVA_LOBE_CAPABILITY_MATRIX,
        validate_nova_cortex_capability_governance,
    )
    from src.cog_runtime.formal.output_type_governance import validate_cortex_output_typing

    print("[nova-cortex-gate] building live family spec")
    spec = nova_cortex_spec()
    result = validate_nova_cortex_capability_governance(spec)
    if not result["valid"]:
        print("[nova-cortex-gate] FAIL: capability governance invalid")
        print(json.dumps(result, indent=2))
        return 1

    typing = validate_cortex_output_typing(spec)
    if not typing["valid"]:
        print("[nova-cortex-gate] FAIL: Theorem 5.1 output typing violation")
        print(json.dumps(typing, indent=2))
        return 1
    print("[nova-cortex-gate] OK: Theorem 5.1 artifact-only lobe outputs")

    print(
        "[nova-cortex-gate] OK: "
        f"{result['runtime_count']} runtimes, "
        f"{result['cortex_module_count']} cortex modules, "
        f"{len(NOVA_LOBE_CAPABILITY_MATRIX)} matrix lobes"
    )

    manifest = repo_root / "docs/runtime/cognitive_runtime_family.v1.json"
    wolf_manifest = repo_root / "wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json"

    for path in (manifest, wolf_manifest):
        if not path.is_file():
            print(f"[nova-cortex-gate] FAIL: missing manifest {path}")
            return 1
        payload = json.loads(path.read_text(encoding="utf-8"))
        exported = validate_nova_cortex_capability_governance(payload)
        if not exported["valid"]:
            print(f"[nova-cortex-gate] FAIL: manifest capability drift at {path}")
            print(json.dumps(exported, indent=2))
            print("[nova-cortex-gate] hint: run python -c \"from src.cog_runtime import export_family_json; export_family_json(); export_family_json('wolf-cog-os/payload/opt/cogos/config/cognitive_runtime_family.json')\"")
            return 1
        print(f"[nova-cortex-gate] OK: {path} matches capability contract")

    for module_id in sorted(CORTEX_MODULE_CAPABILITY_MATRIX):
        entry = CORTEX_MODULE_CAPABILITY_MATRIX[module_id]
        print(f"[nova-cortex-gate] module {module_id}: evidence={entry['evidence_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
