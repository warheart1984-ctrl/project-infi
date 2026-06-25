#!/usr/bin/env python3
"""Sync parent/child lineage for Alt-13 genomes."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENES = (
    "ul_lineage_console_organ",
    "module_governance_organ",
    "recipe_module_organ",
    "imagine_generator_organ",
    "story_forge_lane_organ",
    "beatbox_lane_organ",
    "speakers_lane_organ",
    "human_voice_extraction_organ",
    "narrative_trust_pack_organ",
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
    print("[alt13-lineage] synced parent children and reset concept surfaces")


if __name__ == "__main__":
    main()
