#!/usr/bin/env python3
"""One-shot bootstrap for Alt-17 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt17-summon-wave-2026-06"

ORGANS = [
    {
        "gene": "jarvis_protocol_organ",
        "display": "Jarvis Protocol Organ",
        "module_id": "AAIS-JPO-01",
        "order": 1,
        "parents": [
            "operator_cognition_coherence_fabric",
            "capability_service_bridge",
            "governed_direct_pipeline",
        ],
        "purpose": "Read-only Jarvis message/tool protocol posture (roles, channels, packet contract).",
        "wraps": "src/jarvis_protocol.py",
        "api": "GET /api/jarvis/jarvis-protocol/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "reasoning_contract_organ",
        "display": "Reasoning Contract Organ",
        "module_id": "AAIS-RCO-01",
        "order": 2,
        "parents": ["jarvis_protocol_organ", "reasoning_executive_organ"],
        "purpose": "Read-only reasoning_types contract posture (objective kinds, factors); not OODA executive.",
        "wraps": "src/reasoning_types.py",
        "api": "GET /api/jarvis/reasoning-contract/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "jarvis_reasoning_lane_organ",
        "display": "Jarvis Reasoning Lane Organ",
        "module_id": "AAIS-JRL-01",
        "order": 3,
        "parents": ["jarvis_protocol_organ", "reasoning_contract_organ"],
        "purpose": "Read-only jarvis.reasoning lane catalog posture (objectives/stages); excludes executive usurpation.",
        "wraps": "src/jarvis_reasoning_protocol.py",
        "api": "GET /api/jarvis/jarvis-reasoning-lane/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "conversation_memory_organ",
        "display": "Conversation Memory Organ",
        "module_id": "AAIS-CMO-01",
        "order": 4,
        "parents": ["jarvis_memory_board", "jarvis_protocol_organ"],
        "purpose": "Read-only conversation memory and persona lane posture.",
        "wraps": "src/conversation_memory.py",
        "api": "GET /api/jarvis/conversation-memory/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "continuity_substrate_organ",
        "display": "Continuity Substrate Organ",
        "module_id": "AAIS-CSO-01",
        "order": 5,
        "parents": ["conversation_memory_organ", "continuity_witness_organ"],
        "purpose": "Read-only continuity_profile and preference_profile substrate posture.",
        "wraps": "src/continuity_profile.py",
        "api": "GET /api/jarvis/continuity-substrate/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "jarvis_operator_organ",
        "display": "Jarvis Operator Organ",
        "module_id": "AAIS-JOO-01",
        "order": 6,
        "parents": [
            "jarvis_protocol_organ",
            "safety_envelope_organ",
            "workflow_shell_organ",
        ],
        "purpose": "Read-only Jarvis authority shell posture; observes operator without new execute authority.",
        "wraps": "src/jarvis_operator.py",
        "api": "GET /api/jarvis/jarvis-operator/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "anti_drift_organ",
        "display": "Anti-Drift Organ",
        "module_id": "AAIS-ADO-01",
        "order": 7,
        "parents": ["safety_envelope_organ", "jarvis_operator_organ"],
        "purpose": "Read-only anti-drift and thread contract posture for final replies.",
        "wraps": "src/anti_drift.py",
        "api": "GET /api/jarvis/anti-drift/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "prompt_assembly_organ",
        "display": "Prompt Assembly Organ",
        "module_id": "AAIS-PAO-01",
        "order": 8,
        "parents": ["anti_drift_organ", "conversation_memory_organ"],
        "purpose": "Read-only prompt assembly and scaffold suppression posture.",
        "wraps": "src/prompt_assembly.py",
        "api": "GET /api/jarvis/prompt-assembly/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "output_integrity_organ",
        "display": "Output Integrity Organ",
        "module_id": "AAIS-OIO-01",
        "order": 9,
        "parents": ["prompt_assembly_organ", "anti_drift_organ"],
        "purpose": "Read-only output_completion and corrigibility finalization posture.",
        "wraps": "src/output_completion.py",
        "api": "GET /api/jarvis/output-integrity/status",
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

Status: pending — Alt-17 summon wave `{BATCH}`.

## 1. Purpose

{o['purpose']}

Wraps: [`{o['wraps']}`](../../{o['wraps']}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths
- No autonomous law or patch authority via organ API

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
- [JARVIS_PROTOCOL.md](../../contracts/JARVIS_PROTOCOL.md)

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

`concept → prototype → mvp` via `tools/governance/alt17_promote_mvp.py`.
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
                "docs/contracts/JARVIS_PROTOCOL.md",
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
            "notes": f"Alt-17 wave {o['order']}",
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

    print(f"[alt17-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
