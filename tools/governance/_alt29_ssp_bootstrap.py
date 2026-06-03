#!/usr/bin/env python3
"""Bootstrap Release 29 media processor bridge organ (concept → genome scaffold)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt29-summon-wave-2026-06"
GENE = "media_processor_bridge_organ"


def main() -> int:
    schema_src = ROOT / "schemas/media_processor_bridge_organ.v1.json"
    schema_dst = (
        ROOT / "docs/_future/ideas_pending/schemas/media_processor_bridge_organ.v1.json"
    )
    schema_dst.parent.mkdir(parents=True, exist_ok=True)
    if schema_src.is_file():
        schema_dst.write_text(schema_src.read_text(encoding="utf-8"), encoding="utf-8")

    genome_path = ROOT / f"governance/subsystem_genomes/{GENE}.genome.v1.json"
    if not genome_path.is_file():
        genome = {
            "subsystem_genome_version": "subsystem_genome.v1",
            "identity": {
                "gene": GENE,
                "version": "0.1.0-concept",
                "stage": "concept",
                "display_name": "Media Processor Bridge Organ",
            },
            "governance": {
                "contracts": [
                    "docs/contracts/AAIS_SSP_PROTOCOL.md",
                    "docs/contracts/AAIS_SUBSYSTEM_GENOME.md",
                ],
                "invariants": [
                    "Proposal-only bridge over barebones processors",
                    "module_id frozen to AAIS-MPB-01",
                ],
            },
            "schema": {
                "ref": "schemas/media_processor_bridge_organ.v1.json",
                "frozen": True,
            },
            "runtime": {
                "surface": [
                    {"kind": "module", "path": "src/media_processor_bridge_organ.py"},
                    {
                        "kind": "api",
                        "path": "GET /api/jarvis/media-processor-bridge/status",
                    },
                ]
            },
            "proof": {
                "bundles": [
                    "docs/proof/platform/MEDIA_PROCESSOR_BRIDGE_ORGAN_V1_PROOF.md"
                ],
                "posture": "concept",
            },
            "lineage": {
                "parents": ["capability_service_bridge", "capability_module_organ"],
                "children": [],
            },
            "activation": {"order": 1, "batch_id": BATCH, "notes": "Alt-29 media bridge"},
            "ssp": {
                "concept_spec": (
                    "docs/_future/ideas_pending/MEDIA_PROCESSOR_BRIDGE_ORGAN.md"
                ),
                "mvp_plan": (
                    "docs/_future/ideas_pending/MEDIA_PROCESSOR_BRIDGE_ORGAN_MVP_PLAN.md"
                ),
                "summon_eligible": True,
                "active_doc": "docs/subsystems/platform/MEDIA_PROCESSOR_BRIDGE_ORGAN.md",
            },
        }
        genome_path.write_text(json.dumps(genome, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {genome_path}")

    concept = ROOT / "docs/_future/ideas_pending/MEDIA_PROCESSOR_BRIDGE_ORGAN.md"
    if not concept.is_file():
        concept.write_text(
            "# Media Processor Bridge Organ\n\n"
            "Governed bridge over barebones media processors in `src/`.\n",
            encoding="utf-8",
        )
    mvp = ROOT / "docs/_future/ideas_pending/MEDIA_PROCESSOR_BRIDGE_ORGAN_MVP_PLAN.md"
    if not mvp.is_file():
        mvp.write_text(
            "# Media Processor Bridge Organ — MVP Plan\n\n"
            "| Surface | Path |\n| module | `src/media_processor_bridge_organ.py` |\n",
            encoding="utf-8",
        )
    active = ROOT / "docs/subsystems/platform/MEDIA_PROCESSOR_BRIDGE_ORGAN.md"
    if not active.is_file():
        active.parent.mkdir(parents=True, exist_ok=True)
        active.write_text(
            "# Media Processor Bridge Organ\n\n"
            "Gene: `media_processor_bridge_organ`\n",
            encoding="utf-8",
        )
    proof = ROOT / "docs/proof/platform/MEDIA_PROCESSOR_BRIDGE_ORGAN_V1_PROOF.md"
    if not proof.is_file():
        proof.parent.mkdir(parents=True, exist_ok=True)
        proof.write_text(
            f"# Media Processor Bridge Organ — V1 Proof\n\nBatch: `{BATCH}`.\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
