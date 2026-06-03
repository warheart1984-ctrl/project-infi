#!/usr/bin/env python3
"""Sync parent/child lineage for Alt-16 genomes."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENES = (
    "ai_factory_organ",
    "cogos_runtime_bridge_organ",
    "wolf_rehydration_organ",
    "forge_contractor_organ",
    "forge_eval_organ",
    "evolve_engine_organ",
    "slingshot_organ",
    "operator_workbench_organ",
    "workflow_shell_organ",
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

    for gene, data in registry.items():
        (genomes_dir / f"{gene}.genome.v1.json").write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )
    print("[alt16-lineage] synced parent children")


if __name__ == "__main__":
    main()
