#!/usr/bin/env python3
"""One-shot bootstrap for Alt-14 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt14-summon-wave-2026-06"

ORGANS = [
    {
        "gene": "document_vision_organ",
        "display": "Document Vision Organ",
        "module_id": "AAIS-DVO-01",
        "order": 1,
        "parents": ["capability_service_bridge", "narrative_trust_pack_organ"],
        "purpose": "Read-only document OCR posture; env-gated via AAIS_ENABLE_DOCUMENT_VISION.",
        "wraps": "src/document_vision.py",
        "api": "GET /api/jarvis/document-vision/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "ui_vision_organ",
        "display": "UI Vision Organ",
        "module_id": "AAIS-UVO-01",
        "order": 2,
        "parents": ["document_vision_organ"],
        "purpose": "Read-only UI/screenshot vision posture; env-gated via AAIS_ENABLE_UI_VISION.",
        "wraps": "src/ui_vision.py",
        "api": "GET /api/jarvis/ui-vision/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "perception_gateway_organ",
        "display": "Perception Gateway Organ",
        "module_id": "AAIS-PGO-01",
        "order": 3,
        "parents": ["ui_vision_organ", "capability_module_organ"],
        "purpose": "Read-only capability bridge perception catalog posture (vision env + bridge-safe flags).",
        "wraps": "src/capability_service_bridge.py",
        "api": "GET /api/jarvis/perception-gateway/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "spatial_reasoning_organ",
        "display": "Spatial Reasoning Organ",
        "module_id": "AAIS-SRO-01",
        "order": 4,
        "parents": ["perception_gateway_organ"],
        "purpose": "Read-only spatial reasoning plug posture over bridge spatial capability.",
        "wraps": "src/Spatial_reasoning.py",
        "api": "GET /api/jarvis/spatial-reasoning/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "mystic_engine_organ",
        "display": "Mystic Engine Organ",
        "module_id": "AAIS-MEO-01",
        "order": 5,
        "parents": ["spatial_reasoning_organ"],
        "purpose": "Read-only deterministic mystic symbolic reading posture over bridge mystic capability.",
        "wraps": "src/mystic_engine.py",
        "api": "GET /api/jarvis/mystic-engine/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "perception_lane_organ",
        "display": "Perception Lane Organ",
        "module_id": "AAIS-PLO-01",
        "order": 6,
        "parents": ["mystic_engine_organ", "spatial_reasoning_organ"],
        "purpose": "Read-only spatial/mystic lane chain posture (bridge-safe, operator-gated).",
        "wraps": "src/capability_service_bridge.py",
        "api": "GET /api/jarvis/perception-lane/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "route_choice_organ",
        "display": "Route Choice Organ",
        "module_id": "AAIS-RCO-01",
        "order": 7,
        "parents": ["perception_lane_organ", "orchestration_spine_organ"],
        "purpose": "Read-only turn-level model route posture over MODEL_ROUTES; advisory only.",
        "wraps": "src/model_routing.py",
        "api": "GET /api/jarvis/route-choice/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "specialist_route_organ",
        "display": "Specialist Route Organ",
        "module_id": "AAIS-SRO-02",
        "order": 8,
        "parents": ["route_choice_organ"],
        "purpose": "Read-only specialist selection contract posture over specialist_registry.",
        "wraps": "src/specialist_registry.py",
        "api": "GET /api/jarvis/specialist-route/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "provider_route_organ",
        "display": "Provider Route Organ",
        "module_id": "AAIS-PRO-01",
        "order": 9,
        "parents": ["specialist_route_organ", "cognitive_bridge_organ"],
        "purpose": "Read-only provider mind routing posture; advisory only, no execution authority.",
        "wraps": "src/provider_mind.py",
        "api": "GET /api/jarvis/provider-route/status",
        "proof_subdir": "platform",
    },
]


def schema_for(gene: str) -> dict:
    version_field = f"{gene}_version"
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{gene}.v1",
        "title": f"{gene} v1",
        "type": "object",
        "required": [
            version_field,
            "module_id",
            "cisiv_stage",
            "claim_label",
        ],
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
    upper = gene.upper()
    return f"""# {o['display']}

CISIV stage: **concept**

Status: pending — Alt-14 summon wave `{BATCH}`.

## 1. Purpose

{o['purpose']}

Wraps: [`{o['wraps']}`](../../{o['wraps']}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous route mutation or execution expansion
- No bypass of perception env gates
- No Super Nova or Dreamspace activation

## 4. Organ Contract

Schema: [schemas/{gene}.v1.json](./schemas/{gene}.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `{o['module_id']}` |
| `status_summary` | Bounded organ snapshot |

## 5. Runtime (Proposed)

- `{o['api']}` — read-only status
- `src/{gene}.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required organ fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/{o['proof_subdir']}/{upper}_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/{gene}.py` |
| Implementation | API route + gate |
| Verification | V1 proof + organ gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Batch:** `{BATCH}` — order **{o['order']}**

**Depends on:** {', '.join(f'`{p}`' for p in o['parents'])}

**Minimal invariants:**

- Read-only v1
- `module_id` frozen to `{o['module_id']}`
"""


def mvp_md(o: dict) -> str:
    gene = o["gene"]
    gate = gene.replace("_", "-")
    return f"""# {o['display']} — MVP Plan

CISIV stage: **structure**

Batch: `{BATCH}`

## MVP Surface

| Kind | Path |
|------|------|
| module | `src/{gene}.py` |
| api | `{o['api']}` |
| gate | `make {gate}-gate` |

## Proof

`docs/proof/{o['proof_subdir']}/{gene.upper()}_V1_PROOF.md`

## Promotion

`concept → prototype → mvp` via `tools/governance/alt14_promote_mvp.py`.
"""


def genome_for(o: dict) -> dict:
    gene = o["gene"]
    return {
        "subsystem_genome_version": "subsystem_genome.v1",
        "identity": {
            "gene": gene,
            "version": "0.1.0-concept",
            "stage": "concept",
            "display_name": o["display"],
        },
        "governance": {
            "contracts": [
                "docs/contracts/AAIS_SSP_PROTOCOL.md",
                "docs/contracts/AAIS_SSP_PROMOTION_PROTOCOL.md",
                "docs/contracts/AAIS_SUBSYSTEM_GENOME.md",
                "docs/contracts/AAIS_SUBSYSTEM_MUTATION_PATH.md",
                "docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md",
            ],
            "invariants": [
                "Read-only v1 — organ does not mutate upstream authority",
                f"module_id frozen to {o['module_id']}",
            ],
        },
        "schema": {"ref": f"schemas/{gene}.v1.json", "frozen": False},
        "runtime": {"surface": []},
        "proof": {
            "bundles": [],
            "posture": "asserted",
            "target_bundles": [
                f"docs/proof/{o['proof_subdir']}/{gene.upper()}_V1_PROOF.md"
            ],
        },
        "lineage": {"parents": o["parents"], "children": []},
        "activation": {
            "order": o["order"],
            "batch_id": BATCH,
            "notes": f"Alt-14 wave {o['order']}",
        },
        "retirement": {
            "path": "docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md"
        },
        "mutation": {"history": []},
        "ssp": {
            "concept_spec": f"docs/_future/ideas_pending/{gene.upper()}.md",
            "mvp_plan": f"docs/_future/ideas_pending/{gene.upper()}_MVP_PLAN.md",
            "summon_eligible": True,
        },
    }


def main() -> None:
    ideas = ROOT / "docs/_future/ideas_pending"
    schemas_dir = ROOT / "schemas"
    ideas_schemas = ideas / "schemas"
    genomes = ROOT / "governance/subsystem_genomes"

    for o in ORGANS:
        gene = o["gene"]
        spec_name = f"{gene.upper()}.md"
        schema = schema_for(gene)
        for path in (
            schemas_dir / f"{gene}.v1.json",
            ideas_schemas / f"{gene}.v1.json",
        ):
            path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        (ideas / spec_name).write_text(concept_md(o), encoding="utf-8")
        (ideas / f"{gene.upper()}_MVP_PLAN.md").write_text(mvp_md(o), encoding="utf-8")
        genome_path = genomes / f"{gene}.genome.v1.json"
        genome_path.write_text(
            json.dumps(genome_for(o), indent=2) + "\n", encoding="utf-8"
        )

    print(f"[alt14-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
