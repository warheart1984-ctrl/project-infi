#!/usr/bin/env python3
"""One-shot bootstrap for Alt-13 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt13-summon-wave-2026-06"

ORGANS = [
    {
        "gene": "ul_lineage_console_organ",
        "display": "UL Lineage Console Organ",
        "module_id": "AAIS-ULC-01",
        "order": 1,
        "parents": ["cisiv_operator_lineage_console", "operator_profile_organ"],
        "purpose": "Read-only UL lineage console posture over CISIV operator lineage graph surfaces.",
        "wraps": "src/cisiv.py",
        "api": "GET /api/jarvis/ul-lineage-console/status",
        "proof_subdir": "aais-ul",
    },
    {
        "gene": "module_governance_organ",
        "display": "Module Governance Organ",
        "module_id": "AAIS-MGO-01",
        "order": 2,
        "parents": ["ul_lineage_console_organ", "safety_envelope_organ"],
        "purpose": "Read-only module governance controller posture; fail-closed on major violations.",
        "wraps": "src/module_governance.py",
        "api": "GET /api/jarvis/module-governance/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "recipe_module_organ",
        "display": "Recipe Module Organ",
        "module_id": "AAIS-RMO-01",
        "order": 3,
        "parents": ["module_governance_organ", "recipe_module"],
        "purpose": "Read-only recipe module workflow template posture beside governed recipe_module genome.",
        "wraps": "src/recipe_module.py",
        "api": "GET /api/jarvis/recipe-module/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "imagine_generator_organ",
        "display": "Imagine Generator Organ",
        "module_id": "AAIS-IGO-01",
        "order": 4,
        "parents": ["recipe_module_organ", "imagine_generator"],
        "purpose": "Read-only imagine generator pattern emission posture; bridge-safe creative lane.",
        "wraps": "src/imagine_generator.py",
        "api": "GET /api/jarvis/imagine-generator/status",
        "proof_subdir": "storyforge",
    },
    {
        "gene": "story_forge_lane_organ",
        "display": "Story Forge Lane Organ",
        "module_id": "AAIS-SFL-01",
        "order": 5,
        "parents": ["imagine_generator_organ", "capability_service_bridge"],
        "purpose": "Read-only Story Forge audio/movie capability lane posture over story_forge_audio admission.",
        "wraps": "src/capabilities/story_forge_audio.py",
        "api": "GET /api/jarvis/story-forge-lane/status",
        "proof_subdir": "storyforge",
    },
    {
        "gene": "beatbox_lane_organ",
        "display": "Beatbox Lane Organ",
        "module_id": "AAIS-BBL-01",
        "order": 6,
        "parents": ["story_forge_lane_organ"],
        "purpose": "Read-only Beatbox downstream score lane posture between Story Forge and Speakers.",
        "wraps": "external/beatbox_speakers/src/beatbox/",
        "api": "GET /api/jarvis/beatbox-lane/status",
        "proof_subdir": "storyforge",
    },
    {
        "gene": "speakers_lane_organ",
        "display": "Speakers Lane Organ",
        "module_id": "AAIS-SPL-01",
        "order": 7,
        "parents": ["beatbox_lane_organ"],
        "purpose": "Read-only Speakers mix and voice assembly lane posture.",
        "wraps": "external/beatbox_speakers/src/speakers/",
        "api": "GET /api/jarvis/speakers-lane/status",
        "proof_subdir": "speakers",
    },
    {
        "gene": "human_voice_extraction_organ",
        "display": "Human Voice Extraction Organ",
        "module_id": "AAIS-HVEO-01",
        "order": 8,
        "parents": ["speakers_lane_organ", "human_voice_extraction"],
        "purpose": "Read-only HVE retention and operator signoff posture beside governed HVE genome.",
        "wraps": "src/human_voice_extraction.py",
        "api": "GET /api/jarvis/human-voice-extraction/status",
        "proof_subdir": "speakers",
    },
    {
        "gene": "narrative_trust_pack_organ",
        "display": "Narrative Trust Pack Organ",
        "module_id": "AAIS-NTPO-01",
        "order": 9,
        "parents": [
            "human_voice_extraction_organ",
            "narrative_trust_pack",
            "story_forge_lane_organ",
        ],
        "purpose": "Read-only NTP pack/verify/signoff chain posture; no auto-publish without signoff.",
        "wraps": "src/capabilities/narrative_trust_pack.py",
        "api": "GET /api/jarvis/narrative-trust-pack/status",
        "proof_subdir": "storyforge",
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

Status: pending — Alt-13 summon wave `{BATCH}`.

## 1. Purpose

{o['purpose']}

Wraps: [`{o['wraps']}`](../../{o['wraps']}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous escalation or repo mutation
- No replacement of underlying governed subsystems
- No full Story Forge front door, game lane, or text-to-3D activation

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

`concept → prototype → mvp` via `tools/governance/alt13_promote_mvp.py`.
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
            "notes": f"Alt-13 wave {o['order']}",
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

    print(f"[alt13-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
