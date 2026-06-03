#!/usr/bin/env python3
"""Sync parent/child lineage for Alt-14 genomes."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENES = (
    "document_vision_organ",
    "ui_vision_organ",
    "perception_gateway_organ",
    "spatial_reasoning_organ",
    "mystic_engine_organ",
    "perception_lane_organ",
    "route_choice_organ",
    "specialist_route_organ",
    "provider_route_organ",
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
        identity = child.setdefault("identity", {})
        if identity.get("stage") == "concept":
            child.setdefault("runtime", {})["surface"] = []
        for parent in (child.get("lineage") or {}).get("parents") or []:
            parent_data = registry.get(parent)
            if not parent_data:
                continue
            children = list((parent_data.get("lineage") or {}).get("children") or [])
            if gene not in children:
                children.append(gene)
                parent_data.setdefault("lineage", {})["children"] = sorted(children)

    for gene, data in registry.items():
        (genomes_dir / f"{gene}.genome.v1.json").write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )
    print("[alt14-lineage] synced parent children and reset concept surfaces")


if __name__ == "__main__":
    main()
