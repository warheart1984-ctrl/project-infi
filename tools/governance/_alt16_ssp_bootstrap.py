#!/usr/bin/env python3
"""One-shot bootstrap for Alt-16 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt16-summon-wave-2026-06"

ORGANS = [
    {
        "gene": "ai_factory_organ",
        "display": "AI Factory Organ",
        "module_id": "AAIS-AFO-01",
        "order": 1,
        "parents": [
            "capability_service_bridge",
            "operator_cognition_coherence_fabric",
            "nova_face_organ",
        ],
        "purpose": "Read-only AI Factory build/receipt posture; observes governed mind fabrication without deploy authority via organ surface.",
        "wraps": "ai_factory/",
        "api": "GET /api/jarvis/ai-factory/status",
        "proof_subdir": "ai_factory",
    },
    {
        "gene": "cogos_runtime_bridge_organ",
        "display": "CoGOS Runtime Bridge Organ",
        "module_id": "AAIS-CRB-01",
        "order": 2,
        "parents": ["ai_factory_organ", "capability_service_bridge"],
        "purpose": "Read-only CoG OS cognitive runtime family bridge posture (family spec, rehydrate paths).",
        "wraps": "src/cogos_runtime_bridge.py",
        "api": "GET /api/jarvis/cogos-runtime-bridge/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "wolf_rehydration_organ",
        "display": "Wolf Rehydration Organ",
        "module_id": "AAIS-WRO-01",
        "order": 3,
        "parents": ["cogos_runtime_bridge_organ", "memory_runtime_organ"],
        "purpose": "Read-only Wolf metal reboot rehydration harness posture (narrative/intent store continuity).",
        "wraps": "src/cog_runtime/wolf_rehydration_harness.py",
        "api": "GET /api/jarvis/wolf-rehydration/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "forge_contractor_organ",
        "display": "Forge Contractor Organ",
        "module_id": "AAIS-FCO-01",
        "order": 4,
        "parents": [
            "capability_service_bridge",
            "patchforge_organ",
            "operator_cognition_coherence_fabric",
        ],
        "purpose": "Read-only isolated Forge contractor lane posture (HTTP health, review-gated).",
        "wraps": "src/forge_client.py",
        "api": "GET /api/jarvis/forge-contractor/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "forge_eval_organ",
        "display": "ForgeEval Organ",
        "module_id": "AAIS-FEO-01",
        "order": 5,
        "parents": ["forge_contractor_organ"],
        "purpose": "Read-only ForgeEval evaluator lane posture (external service reachability).",
        "wraps": "src/forge_eval_client.py",
        "api": "GET /api/jarvis/forge-eval/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "evolve_engine_organ",
        "display": "Evolve Engine Organ",
        "module_id": "AAIS-EEO-01",
        "order": 6,
        "parents": ["forge_eval_organ", "forge_contractor_organ"],
        "purpose": "Read-only EvolveEngine bounded mutation lane posture; special-review, no direct patch authority.",
        "wraps": "src/evolve_client.py",
        "api": "GET /api/jarvis/evolve-engine/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "slingshot_organ",
        "display": "Slingshot Organ",
        "module_id": "AAIS-SLO-01",
        "order": 7,
        "parents": [
            "mechanic_handoff_organ",
            "forensic_triangulation_organ",
            "route_choice_organ",
        ],
        "purpose": "Read-only AI Slingshot kinetic accelerator posture (launch_blocked, MA-13 frame/packet).",
        "wraps": "slingshot/",
        "api": "GET /api/jarvis/slingshot/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "operator_workbench_organ",
        "display": "Operator Workbench Organ",
        "module_id": "AAIS-OWO-01",
        "order": 8,
        "parents": ["change_scope_organ", "patchforge_organ"],
        "purpose": "Read-only evolving workbench workspace intel posture; proposal-only coding context.",
        "wraps": "src/evolving_workbench.py",
        "api": "GET /api/jarvis/operator-workbench/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "workflow_shell_organ",
        "display": "Workflow Shell Organ",
        "module_id": "AAIS-WSO-01",
        "order": 9,
        "parents": ["operator_workbench_organ", "capability_service_bridge"],
        "purpose": "Read-only FastAPI workflow/onboarding shell posture under Project Infi bridge.",
        "wraps": "app/workflow_runtime.py",
        "api": "GET /api/jarvis/workflow-shell/status",
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

Status: pending — Alt-16 summon wave `{BATCH}`.

## 1. Purpose

{o['purpose']}

Wraps: [`{o['wraps']}`](../../{o['wraps']}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of Jarvis executive or contractor POST contract expansion
- No autonomous patch apply or Slingshot launch bypass via organ API
- No cross-machine replay claims at concept stage

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
- [AI_FACTORY.md](../../runtime/AI_FACTORY.md)
- [AI_SLINGSHOT.md](../../runtime/AI_SLINGSHOT.md)

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
| gate | `make {gate}-organ-gate` |

## Proof

`docs/proof/{o['proof_subdir']}/{gene.upper()}_V1_PROOF.md`

## Promotion

`concept → prototype → mvp` via `tools/governance/alt16_promote_mvp.py`.
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
                "docs/runtime/AAIS_RUNTIME_GUIDE.md",
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
            "notes": f"Alt-16 wave {o['order']}",
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

    print(f"[alt16-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
