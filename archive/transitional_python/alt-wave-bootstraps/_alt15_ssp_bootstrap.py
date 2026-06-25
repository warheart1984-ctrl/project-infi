#!/usr/bin/env python3
"""One-shot bootstrap for Alt-15 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt15-summon-wave-2026-06"

ORGANS = [
    {
        "gene": "reasoning_executive_organ",
        "display": "Reasoning Executive Organ",
        "module_id": "AAIS-REO-01",
        "order": 1,
        "parents": [
            "operator_profile_organ",
            "safety_envelope_organ",
            "operator_cognition_coherence_fabric",
        ],
        "purpose": "Read-only Jarvis OODA / jarvis.reasoning executive posture; observes routing packet completeness without usurping authority.",
        "wraps": "src/jarvis_reasoning_protocol.py",
        "api": "GET /api/jarvis/reasoning-executive/status",
        "proof_subdir": "cognitive_runtime",
    },
    {
        "gene": "attention_organ",
        "display": "Attention Organ",
        "module_id": "AAIS-ATO-01",
        "order": 2,
        "parents": ["reasoning_executive_organ", "reflection_runtime_organ"],
        "purpose": "Read-only cognitive.attention lobe posture (focus_artifact stages).",
        "wraps": "src/cog_runtime/attention.py",
        "api": "GET /api/jarvis/attention/status",
        "proof_subdir": "cognitive_runtime",
    },
    {
        "gene": "coherence_projection_organ",
        "display": "Coherence Projection Organ",
        "module_id": "AAIS-CPO-01",
        "order": 3,
        "parents": [
            "attention_organ",
            "narrative_continuity_organ",
            "intent_agency_organ",
        ],
        "purpose": "Read-only mind-to-voice coherence projection posture; exports bounded state, not chain-of-thought.",
        "wraps": "src/cog_runtime/coherence_projection.py",
        "api": "GET /api/jarvis/coherence-projection/status",
        "proof_subdir": "cognitive_runtime",
    },
    {
        "gene": "deliberation_organ",
        "display": "Deliberation Organ",
        "module_id": "AAIS-DLO-01",
        "order": 4,
        "parents": ["coherence_projection_organ", "route_choice_organ"],
        "purpose": "Read-only cognitive.deliberation lobe posture (decision frames, criteria scores).",
        "wraps": "src/cog_runtime/deliberation.py",
        "api": "GET /api/jarvis/deliberation/status",
        "proof_subdir": "cognitive_runtime",
    },
    {
        "gene": "planning_organ",
        "display": "Planning Organ",
        "module_id": "AAIS-PLO-02",
        "order": 5,
        "parents": ["deliberation_organ", "reflection_runtime_organ"],
        "purpose": "Read-only cognitive.planning lobe posture (step chains, next_action).",
        "wraps": "src/cog_runtime/planning.py",
        "api": "GET /api/jarvis/planning/status",
        "proof_subdir": "cognitive_runtime",
    },
    {
        "gene": "cortex_arcs_organ",
        "display": "Cortex Arcs Organ",
        "module_id": "AAIS-CAO-01",
        "order": 6,
        "parents": ["planning_organ", "continuity_witness_organ"],
        "purpose": "Read-only cortex.arcs module posture (goal hierarchy, open threads).",
        "wraps": "src/cog_runtime/arcs.py",
        "api": "GET /api/jarvis/cortex-arcs/status",
        "proof_subdir": "cognitive_runtime",
    },
    {
        "gene": "cognitive_execution_organ",
        "display": "Cognitive Execution Organ",
        "module_id": "AAIS-CEO-01",
        "order": 7,
        "parents": ["cortex_arcs_organ", "planning_organ"],
        "purpose": "Read-only cognitive.execution lobe posture (bind/verify/recover/rollback); not patch execution depth.",
        "wraps": "src/cog_runtime/execution.py",
        "api": "GET /api/jarvis/cognitive-execution/status",
        "proof_subdir": "cognitive_runtime",
    },
    {
        "gene": "speaking_runtime_organ",
        "display": "Speaking Runtime Organ",
        "module_id": "AAIS-SRO-02",
        "order": 8,
        "parents": ["cognitive_execution_organ", "coherence_projection_organ"],
        "purpose": "Read-only speaking.runtime posture (listen/frame/plan/speak/check stages).",
        "wraps": "src/speaking_runtime/",
        "api": "GET /api/jarvis/speaking-runtime/status",
        "proof_subdir": "cognitive_runtime",
    },
    {
        "gene": "nova_face_organ",
        "display": "Nova Face Organ",
        "module_id": "AAIS-NFO-01",
        "order": 9,
        "parents": ["speaking_runtime_organ", "operator_profile_organ"],
        "purpose": "Read-only Nova companion surface binding posture under Jarvis authority.",
        "wraps": "src/cog_runtime/nova_face.py",
        "api": "GET /api/jarvis/nova-face/status",
        "proof_subdir": "cognitive_runtime",
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

Status: pending — Alt-15 summon wave `{BATCH}`.

## 1. Purpose

{o['purpose']}

Wraps: [`{o['wraps']}`](../../{o['wraps']}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of Jarvis executive or Nova cognitive turn configuration
- No lobe activation or routing override via organ API
- No Dreamspace or Super Nova autonomous escalation

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
- [NOVA_COHERENCE_PROJECTION.md](../../runtime/NOVA_COHERENCE_PROJECTION.md)

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

`concept → prototype → mvp` via `tools/governance/alt15_promote_mvp.py`.
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
                "docs/runtime/NOVA_CORTEX.md",
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
            "notes": f"Alt-15 wave {o['order']}",
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

    print(f"[alt15-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
