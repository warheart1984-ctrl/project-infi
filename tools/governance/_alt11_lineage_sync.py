#!/usr/bin/env python3
"""Sync parent/child lineage for Alt-11 genomes."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENES = (
    "cognitive_bridge_organ",
    "governed_event_chain_organ",
    "tracing_spine_organ",
    "mission_board_organ",
    "aris_boundary_organ",
    "capability_module_organ",
    "patchforge_organ",
    "change_scope_organ",
    "patch_verification_organ",
)


def main() -> None:
    genomes_dir = ROOT / "governance/subsystem_genomes"
    registry: dict[str, dict] = {}
    for path in genomes_dir.glob("*.genome.v1.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        gene = (data.get("identity") or {}).get("gene")
        if gene:
            registry[gene] = data

    for gene in GENES:
        child = registry.get(gene)
        if not child:
            continue
        for parent in (child.get("lineage") or {}).get("parents") or []:
            parent_data = registry.get(parent)
            if not parent_data:
                continue
            children = list((parent_data.get("lineage") or {}).get("children") or [])
            if gene not in children:
                children.append(gene)
                parent_data.setdefault("lineage", {})["children"] = sorted(children)

    for gene in GENES:
        data = registry.get(gene)
        if data:
            (genomes_dir / f"{gene}.genome.v1.json").write_text(
                json.dumps(data, indent=2) + "\n", encoding="utf-8"
            )
    for gene, data in registry.items():
        if gene not in GENES:
            (genomes_dir / f"{gene}.genome.v1.json").write_text(
                json.dumps(data, indent=2) + "\n", encoding="utf-8"
            )
    print("[alt11-lineage] synced parent children")


if __name__ == "__main__":
    main()
