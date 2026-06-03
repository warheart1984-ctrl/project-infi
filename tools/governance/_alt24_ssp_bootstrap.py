#!/usr/bin/env python3
"""One-shot bootstrap for Release 24 SSP concept artifacts (Wave 14 organs)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt24-summon-wave-2026-06"

ORGANS = [
    {
        "api": "GET /api/jarvis/linguistic-forecast-calibration/status",
        "display": "Linguistic Forecast Calibration Subsystem",
        "gene": "linguistic_forecast_calibration_organ",
        "module_id": "AAIS-LFC-02",
        "order": 1,
        "parents": [
            "linguistic_drift_forecast_organ",
            "meta_linguistic_governance_organ",
        ],
        "proof_subdir": "platform",
        "purpose": "Read-only forecast-vs-reality calibration posture (Wave 13).",
        "wraps": "src/governance_organs/linguistic_forecast_calibration_engine.py",
    },
    {
        "api": "GET /api/jarvis/linguistic-governance-queue/status",
        "display": "Linguistic Governance Queue Subsystem",
        "gene": "linguistic_governance_queue_organ",
        "module_id": "AAIS-LGQ-01",
        "order": 2,
        "parents": ["linguistic_forecast_calibration_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only prescriptive queue and work-order posture (Wave 13–14).",
        "wraps": "src/governance_organs/linguistic_governance_queue_engine.py",
    },
    {
        "api": "GET /api/jarvis/linguistic-full-governance-cycle/status",
        "display": "Linguistic Full Governance Cycle Subsystem",
        "gene": "linguistic_full_governance_cycle_organ",
        "module_id": "AAIS-LFG-01",
        "order": 3,
        "parents": [
            "linguistic_forecast_calibration_organ",
            "linguistic_governance_queue_organ",
            "linguistic_predictive_governance_organ",
            "linguistic_governance_cycle_organ",
        ],
        "proof_subdir": "platform",
        "purpose": "Read-only full calibrate→predict→react→queue→attest cycle posture.",
        "wraps": "src/governance_organs/linguistic_full_governance_cycle_engine.py",
    },
    {
        "api": "GET /api/jarvis/linguistic-governance-attestation/status",
        "display": "Linguistic Governance Attestation Subsystem",
        "gene": "linguistic_governance_attestation_organ",
        "module_id": "AAIS-LGA-01",
        "order": 4,
        "parents": [
            "linguistic_full_governance_cycle_organ",
            "linguistic_closed_loop_fabric_organ",
        ],
        "proof_subdir": "platform",
        "purpose": "Read-only unified attestation digest and closed_loop_score (Wave 14).",
        "wraps": "src/governance_organs/linguistic_governance_attestation_engine.py",
    },
]


def schema_for(gene: str) -> dict:
    version_field = f"{gene}_version"
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{gene}.v1",
        "title": f"{gene} v1",
        "type": "object",
        "required": [version_field, "module_id", "cisiv_stage", "claim_label"],
        "properties": {
            version_field: {"const": f"{gene}.v1"},
            "module_id": {"type": "string", "minLength": 1},
            "status_summary": {"type": "string"},
            "cisiv_stage": {
                "enum": [
                    "concept",
                    "identity",
                    "structure",
                    "implementation",
                    "verification",
                ]
            },
            "claim_label": {"enum": ["asserted", "proven", "rejected"]},
            "read_only": {"type": "boolean"},
        },
        "additionalProperties": True,
    }


def concept_md(o: dict) -> str:
    gene = o["gene"]
    return f"""# {o['display']}

CISIV stage: **concept**

Status: Release 24 (`{BATCH}`).

## Purpose

{o['purpose']}

Wraps: `{o['wraps']}`.

## API

`{o['api']}`

## Related

- AAIS_META_LINGUISTIC_GOVERNANCE.md (Wave 14)
- AAIS_SSP_PROTOCOL.md Release 24
"""


def main() -> None:
    ideas = ROOT / "docs/_future/ideas_pending"
    schemas_dir = ROOT / "schemas"
    ideas_schemas = ideas / "schemas"
    genomes = ROOT / "governance/subsystem_genomes"
    proof_dir = ROOT / "docs/proof/platform"

    for o in ORGANS:
        gene = o["gene"]
        schema = schema_for(gene)
        for path in (schemas_dir / f"{gene}.v1.json", ideas_schemas / f"{gene}.v1.json"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        (ideas / f"{gene.upper()}.md").write_text(concept_md(o), encoding="utf-8")
        genome_path = genomes / f"{gene}.genome.v1.json"
        genome_path.write_text(
            json.dumps(
                {
                    "subsystem_genome_version": "subsystem_genome.v1",
                    "identity": {
                        "gene": gene,
                        "version": "0.1.0-mvp",
                        "stage": "mvp",
                        "display_name": o["display"],
                    },
                    "governance": {"contracts": [], "invariants": ["Read-only v1"]},
                    "schema": {"ref": f"schemas/{gene}.v1.json", "frozen": False},
                    "lineage": {"parents": o["parents"], "children": []},
                    "activation": {"order": o["order"], "batch_id": BATCH},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        proof = proof_dir / f"{gene.upper()}_V1_PROOF.md"
        proof.parent.mkdir(parents=True, exist_ok=True)
        if not proof.is_file():
            proof.write_text(
                f"# {o['display']} — V1 Proof\n\n"
                f"Release 24 — `{BATCH}`.\n\n"
                f"- Status API: `{o['api']}`\n"
                f"- Gate: `make {gene.replace('_', '-')}-organ-gate`\n",
                encoding="utf-8",
            )

    print(f"[alt24-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
