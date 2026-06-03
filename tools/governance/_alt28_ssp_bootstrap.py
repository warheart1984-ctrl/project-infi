#!/usr/bin/env python3
"""One-shot bootstrap for Release 28 SSP concept artifacts (Wave 19 Story Forge expansion)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt28-summon-wave-2026-06"

CONTRACTS = [
    "docs/contracts/AAIS_SSP_PROTOCOL.md",
    "docs/contracts/AAIS_SSP_PROMOTION_PROTOCOL.md",
    "docs/contracts/AAIS_SUBSYSTEM_GENOME.md",
    "docs/contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md",
    "docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md",
    "docs/runtime/AAIS_RUNTIME_GUIDE.md",
    "docs/subsystems/storyforge/STORYFORGE_CANONICAL.md",
]

ORGANS = [
    {
        "api": "GET /api/jarvis/story-forge-launcher/status",
        "display": "Story Forge Launcher",
        "gene": "story_forge_launcher_organ",
        "module_id": "AAIS-SFLR-01",
        "order": 1,
        "parents": ["story_forge_lane_organ"],
        "proof_subdir": "storyforge",
        "purpose": "Read-only standalone Story Forge launcher posture (not AAIS launcher_organ).",
        "wraps": "external/story_forge/src/story_forge/launcher.py",
        "concept_file": "STORY_FORGE_LAUNCHER_ORGAN.md",
    },
    {
        "api": "GET /api/jarvis/movie-renderer-lane/status",
        "display": "Movie Renderer Lane",
        "gene": "movie_renderer_lane_organ",
        "module_id": "AAIS-MRL-01",
        "order": 2,
        "parents": ["story_forge_lane_organ", "story_forge_launcher_organ"],
        "proof_subdir": "storyforge",
        "purpose": "Read-only movie renderer direct operator lane posture.",
        "wraps": "external/story_forge/src/story_forge/movie_renderer.py",
        "concept_file": "MOVIE_RENDERER_LANE_ORGAN.md",
    },
    {
        "api": "GET /api/jarvis/text-game-to-video/status",
        "display": "Text-Game-to-Video Front Door",
        "gene": "text_game_to_video_organ",
        "module_id": "AAIS-TGTV-01",
        "order": 3,
        "parents": [
            "story_forge_lane_organ",
            "story_forge_launcher_organ",
            "movie_renderer_lane_organ",
        ],
        "proof_subdir": "storyforge",
        "purpose": "Read-only /pipeline movie front-door posture.",
        "wraps": "external/story_forge/src/story_forge/engine.py",
        "concept_file": "TEXT_GAME_TO_VIDEO_ORGAN.md",
    },
    {
        "api": "GET /api/jarvis/game-front-door/status",
        "display": "Game Front Door",
        "gene": "game_front_door_organ",
        "module_id": "AAIS-GFD-01",
        "order": 4,
        "parents": [
            "story_forge_lane_organ",
            "story_forge_launcher_organ",
            "text_game_to_video_organ",
        ],
        "proof_subdir": "storyforge",
        "purpose": "Read-only /pipeline game front-door posture.",
        "wraps": "external/story_forge/src/story_forge/engine.py",
        "concept_file": "GAME_FRONT_DOOR_ORGAN.md",
    },
    {
        "api": "GET /api/jarvis/text-to-3d-world-lane/status",
        "display": "Text-to-3D World Lane",
        "gene": "text_to_3d_world_lane_organ",
        "module_id": "AAIS-TT3D-01",
        "order": 5,
        "parents": ["story_forge_lane_organ", "movie_renderer_lane_organ"],
        "proof_subdir": "storyforge",
        "purpose": "Read-only text-to-3D world lane as AAIS live lane posture.",
        "wraps": "external/story_forge/src/story_forge/text_to_3d_world_lane.py",
        "concept_file": "TEXT_TO_3D_WORLD_LANE_ORGAN.md",
    },
    {
        "api": "GET /api/jarvis/world-pack-lane/status",
        "display": "World Pack Lane",
        "gene": "world_pack_lane_organ",
        "module_id": "AAIS-WPL-01",
        "order": 6,
        "parents": ["text_to_3d_world_lane_organ", "story_forge_lane_organ"],
        "proof_subdir": "storyforge",
        "purpose": "Read-only world pack registry and manifest lane posture.",
        "wraps": "external/story_forge/src/story_forge/worldpacks/",
        "concept_file": "WORLD_PACK_LANE_ORGAN.md",
    },
]

LINEAGE_CHILDREN: dict[str, list[str]] = {
    "story_forge_lane_organ": [
        "story_forge_launcher_organ",
        "movie_renderer_lane_organ",
        "text_game_to_video_organ",
        "game_front_door_organ",
        "text_to_3d_world_lane_organ",
        "world_pack_lane_organ",
    ],
    "story_forge_launcher_organ": [
        "movie_renderer_lane_organ",
        "text_game_to_video_organ",
        "game_front_door_organ",
    ],
    "movie_renderer_lane_organ": ["text_game_to_video_organ", "text_to_3d_world_lane_organ"],
    "text_game_to_video_organ": ["game_front_door_organ"],
    "text_to_3d_world_lane_organ": ["world_pack_lane_organ"],
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

Status: pending — Release 28 (`{BATCH}`).

## 1. Purpose

{o['purpose']}

Wraps: [`{o['wraps']}`](../../{o['wraps']}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only subsystem surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths beyond governed boundary
- No broad direct provider use outside capability_service_bridge

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

- [STORYFORGE_CANONICAL.md](../../subsystems/storyforge/STORYFORGE_CANONICAL.md) §7
- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)

## 10. Activation Order

**Release:** `{BATCH}` — order **{o['order']}**

**Depends on:** {', '.join(f'`{p}`' for p in o['parents'])}
"""


def mvp_md(o: dict) -> str:
    return f"""# {o['display']} — MVP Plan

CISIV stage: **structure**

Release: `{BATCH}`

## MVP Surface

| Kind | Path |
|------|------|
| module | `src/{o['gene']}.py` |
| api | `{o['api']}` |

## Proof

`docs/proof/{o['proof_subdir']}/{o['gene'].upper()}_V1_PROOF.md`

## Promotion

`concept → prototype → mvp` via `tools/governance/alt28_promote_mvp.py`.
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
        "governance": {
            "contracts": CONTRACTS,
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
            "notes": f"Release 28 wave {o['order']}",
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
        f"Release 28 — `{BATCH}`.\n\n"
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
    bundle_proof = ROOT / "docs/proof/storyforge/STORYFORGE_EXPANSION_BUNDLE_V1_PROOF.md"
    if not bundle_proof.is_file():
        bundle_proof.write_text(
            "# Story Forge Expansion Bundle v1 Proof\n\n"
            f"Release 28.2 closure packet for Wave 19 Story Forge expansion "
            f"layers on Coherence Layer v1.23.\n\n"
            f"Batch: `{BATCH}`.\n",
            encoding="utf-8",
        )
    print(f"[alt28-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
