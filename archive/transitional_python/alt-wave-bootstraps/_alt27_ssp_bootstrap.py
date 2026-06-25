#!/usr/bin/env python3
"""One-shot bootstrap for Release 27 SSP concept artifacts (Wave 18 CISIV early ideas)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt27-summon-wave-2026-06"

CONTRACTS = [
    "docs/contracts/AAIS_SSP_PROTOCOL.md",
    "docs/contracts/AAIS_SSP_PROMOTION_PROTOCOL.md",
    "docs/contracts/AAIS_SUBSYSTEM_GENOME.md",
    "docs/contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md",
    "docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md",
    "docs/runtime/AAIS_RUNTIME_GUIDE.md",
]

ORGANS = [
    {
        "api": "GET /api/jarvis/ul-lineage-console/status",
        "display": "CISIV Operator Lineage Console",
        "gene": "cisiv_operator_lineage_console",
        "module_id": "AAIS-COLC-01",
        "order": 1,
        "parents": ["operator_cognition_coherence_fabric", "governance_layer_organ"],
        "proof_subdir": "aais-ul",
        "purpose": "Read-only CISIV operator lineage graph posture (UL lineage console).",
        "wraps": "src/ul_lineage.py",
        "concept_file": "CISIV_OPERATOR_LINEAGE_CONSOLE.md",
    },
    {
        "api": "GET /api/jarvis/forensic-triangulation/status",
        "display": "Forensic Triangulation Ledger",
        "gene": "forensic_triangulation",
        "module_id": "AAIS-FTL-01",
        "order": 2,
        "parents": ["cisiv_operator_lineage_console", "scorpion_bridge_organ"],
        "proof_subdir": "forensics",
        "purpose": "Read-only forensic triangulation correlate posture.",
        "wraps": "triangulation/",
        "concept_file": "FORENSIC_TRIANGULATION.md",
    },
    {
        "api": "GET /api/jarvis/capability-bridge/status",
        "display": "Capability Service Bridge",
        "gene": "capability_service_bridge",
        "module_id": "AAIS-CSB-01",
        "order": 3,
        "parents": ["governance_layer_organ", "operator_cognition_coherence_fabric"],
        "proof_subdir": "platform",
        "purpose": "Read-only governed capability service-lane bridge posture.",
        "wraps": "src/capability_service_bridge.py",
        "concept_file": "CAPABILITY_SERVICE_BRIDGE.md",
    },
    {
        "api": "GET /api/jarvis/memory/board",
        "display": "Jarvis Memory Board",
        "gene": "jarvis_memory_board",
        "module_id": "AAIS-JMB-01",
        "order": 4,
        "parents": ["capability_service_bridge", "cisiv_operator_lineage_console"],
        "proof_subdir": "platform",
        "purpose": "Read-only Jarvis memory board layout and module card posture.",
        "wraps": "src/jarvis_memory_board.py",
        "concept_file": "JARVIS_MEMORY_BOARD.md",
    },
    {
        "api": "GET /api/jarvis/pipeline/{turn_id}",
        "display": "Governed Direct Pipeline",
        "gene": "governed_direct_pipeline",
        "module_id": "AAIS-GDP-01",
        "order": 5,
        "parents": ["capability_service_bridge", "jarvis_memory_board"],
        "proof_subdir": "platform",
        "purpose": "Read-only governed direct turn pipeline trace posture.",
        "wraps": "src/governed_direct_pipeline.py",
        "concept_file": "GOVERNED_DIRECT_PIPELINE.md",
    },
    {
        "api": "GET /api/jarvis/recipe-module/status",
        "display": "Recipe Module",
        "gene": "recipe_module",
        "module_id": "AAIS-RM-01",
        "order": 6,
        "parents": ["capability_service_bridge", "module_governance_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only recipe module workflow template posture.",
        "wraps": "src/recipe_module.py",
        "concept_file": "RECIPE_MODULE.md",
    },
    {
        "api": "GET /api/jarvis/imagine-generator/status",
        "display": "Imagine Generator",
        "gene": "imagine_generator",
        "module_id": "AAIS-IG-01",
        "order": 7,
        "parents": ["recipe_module", "capability_service_bridge"],
        "proof_subdir": "storyforge",
        "purpose": "Read-only imagine generator pattern emission posture.",
        "wraps": "src/imagine_generator.py",
        "concept_file": "IMAGINE_GENERATOR.md",
    },
    {
        "api": "GET /api/jarvis/narrative-trust-pack/status",
        "display": "Narrative Trust Pack",
        "gene": "narrative_trust_pack",
        "module_id": "AAIS-NTP-01",
        "order": 8,
        "parents": ["imagine_generator", "story_forge_lane_organ"],
        "proof_subdir": "storyforge",
        "purpose": "Read-only narrative trust pack chain posture.",
        "wraps": "src/narrative_trust_pack_organ.py",
        "concept_file": "NARRATIVE_TRUST_PACK.md",
    },
    {
        "api": "GET /api/jarvis/human-voice-extraction/status",
        "display": "Human Voice Extraction",
        "gene": "human_voice_extraction",
        "module_id": "AAIS-HVE-01",
        "order": 9,
        "parents": ["narrative_trust_pack", "speakers_lane_organ"],
        "proof_subdir": "speakers",
        "purpose": "Read-only HVE retention and operator signoff posture.",
        "wraps": "src/human_voice_extraction.py",
        "concept_file": "HUMAN_VOICE_EXTRACTION.md",
    },
]

LINEAGE_CHILDREN: dict[str, list[str]] = {
    "operator_cognition_coherence_fabric": [
        "cisiv_operator_lineage_console",
        "capability_service_bridge",
    ],
    "cisiv_operator_lineage_console": ["forensic_triangulation"],
    "capability_service_bridge": [
        "jarvis_memory_board",
        "governed_direct_pipeline",
        "recipe_module",
    ],
    "jarvis_memory_board": ["governed_direct_pipeline"],
    "recipe_module": ["imagine_generator"],
    "imagine_generator": ["narrative_trust_pack"],
    "narrative_trust_pack": ["human_voice_extraction"],
    "governance_layer_organ": ["cisiv_operator_lineage_console", "capability_service_bridge"],
}


def _concept_basename(o: dict) -> str:
    return o.get("concept_file") or f"{o['gene'].upper()}.md"


def _mvp_basename(o: dict) -> str:
    base = _concept_basename(o).removesuffix(".md")
    return f"{base}_MVP_PLAN.md"


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
    concept = _concept_basename(o)
    return f"""# {o['display']}

CISIV stage: **concept**

Status: pending — Release 27 (`{BATCH}`).

## 1. Purpose

{o['purpose']}

Wraps: [`{o['wraps']}`](../../{o['wraps']}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only subsystem surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths
- No autonomous law or patch authority via subsystem API

## 4. Subsystem Contract

Schema: [schemas/{gene}.v1.json](./schemas/{gene}.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `{o['module_id']}` |
| `status_summary` | Bounded subsystem snapshot |

## 5. Runtime (Proposed)

- `{o['api']}` — read-only status
- Runtime module per MVP plan

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required subsystem fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/{o['proof_subdir']}/{gene.upper()}_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | Runtime status surface |
| Implementation | API route + gate |
| Verification | V1 proof + subsystem gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [AAIS_META_LINGUISTIC_GOVERNANCE.md](../../contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md)

## 10. Activation Order

**Release:** `{BATCH}` — order **{o['order']}**

**Depends on:** {', '.join(f'`{p}`' for p in o['parents'])}
"""


def mvp_md(o: dict) -> str:
    mvp = _mvp_basename(o)
    return f"""# {o['display']} — MVP Plan

CISIV stage: **structure**

Release: `{BATCH}`

## MVP Surface

| Kind | Path |
|------|------|
| module | `{o['wraps']}` |
| api | `{o['api']}` |

## Proof

`docs/proof/{o['proof_subdir']}/{o['gene'].upper()}_V1_PROOF.md`

## Promotion

`concept → prototype → mvp` via `tools/governance/alt27_promote_mvp.py`.
"""


def genome_for(o: dict) -> dict:
    gene = o["gene"]
    concept = _concept_basename(o)
    mvp = _mvp_basename(o)
    return {
        "subsystem_genome_version": "subsystem_genome.v1",
        "identity": {
            "gene": gene,
            "version": "0.1.0-concept",
            "stage": "concept",
            "display_name": o["display"],
        },
        "governance": {"contracts": CONTRACTS, "invariants": []},
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
            "notes": f"Release 27 wave {o['order']}",
        },
        "retirement": {
            "path": "docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md"
        },
        "mutation": {"history": []},
        "ssp": {
            "concept_spec": f"docs/_future/ideas_pending/{concept}",
            "mvp_plan": f"docs/_future/ideas_pending/{mvp}",
            "summon_eligible": True,
        },
    }


def _merge_genome(existing: dict, template: dict) -> dict:
    merged = dict(template)
    for key in ("identity", "runtime", "proof", "ssp", "lineage", "governance"):
        if key in existing:
            base = dict(merged.get(key) or {})
            overlay = dict(existing[key])
            base.update(overlay)
            merged[key] = base
    stage = (existing.get("identity") or {}).get("stage")
    if stage in {"mvp", "governed"}:
        merged.setdefault("identity", {})["stage"] = stage
        version = (existing.get("identity") or {}).get("version")
        if version:
            merged.setdefault("identity", {})["version"] = version
    if stage == "governed":
        merged.setdefault("proof", {})["posture"] = "governed"
        merged.setdefault("schema", {})["frozen"] = True
    elif stage == "mvp":
        merged.setdefault("proof", {})["posture"] = "asserted"
    merged.setdefault("activation", {})["batch_id"] = BATCH
    merged["activation"]["order"] = template["activation"]["order"]
    merged["activation"]["notes"] = template["activation"]["notes"]
    return merged


def _sync_lineage_children(genomes: Path) -> None:
    for parent, kids in LINEAGE_CHILDREN.items():
        path = genomes / f"{parent}.genome.v1.json"
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        children = list(data.get("lineage", {}).get("children") or [])
        for child in kids:
            if child not in children:
                children.append(child)
        data.setdefault("lineage", {})["children"] = sorted(children)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _proof_md(o: dict) -> str:
    gene = o["gene"]
    return (
        f"# {o['display']} — V1 Proof\n\n"
        f"Release 27 — `{BATCH}`.\n\n"
        f"- Status API: `{o['api']}`\n"
        f"- Gene: `{gene}`\n"
    )


def main() -> None:
    ideas = ROOT / "docs/_future/ideas_pending"
    schemas_dir = ROOT / "schemas"
    ideas_schemas = ideas / "schemas"
    genomes = ROOT / "governance/subsystem_genomes"

    for o in ORGANS:
        gene = o["gene"]
        schema = schema_for(gene)
        for path in (
            schemas_dir / f"{gene}.v1.json",
            ideas_schemas / f"{gene}.v1.json",
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        (ideas / _concept_basename(o)).write_text(concept_md(o), encoding="utf-8")
        (ideas / _mvp_basename(o)).write_text(mvp_md(o), encoding="utf-8")
        genome_path = genomes / f"{gene}.genome.v1.json"
        template = genome_for(o)
        if genome_path.is_file():
            existing = json.loads(genome_path.read_text(encoding="utf-8"))
            genome_data = _merge_genome(existing, template)
        else:
            genome_data = template
        genome_path.write_text(json.dumps(genome_data, indent=2) + "\n", encoding="utf-8")
        proof = ROOT / "docs/proof" / o["proof_subdir"] / f"{gene.upper()}_V1_PROOF.md"
        proof.parent.mkdir(parents=True, exist_ok=True)
        if not proof.is_file():
            proof.write_text(_proof_md(o), encoding="utf-8")

    _sync_lineage_children(genomes)
    print(f"[alt27-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
