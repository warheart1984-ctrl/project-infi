#!/usr/bin/env python3
"""One-shot bootstrap for Alt-10 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt10-summon-wave-2026-06"

ORGANS = [
    {
        "gene": "verification_gate_organ",
        "display": "Verification Gate Organ",
        "module_id": "AAIS-VG-01",
        "order": 1,
        "parents": ["mission_board", "jarvis_memory_board"],
        "purpose": "Formalize verification gate policy as read-only organ over mission/review flows.",
        "wraps": "src/verification_gate.py",
        "api": "GET /api/jarvis/verification-gate/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "memory_path_governance_organ",
        "display": "Memory Path Governance Organ",
        "module_id": "AAIS-MPG-01",
        "order": 2,
        "parents": ["jarvis_memory_board", "verification_gate_organ"],
        "purpose": "Report memory-board path coverage vs legacy conversation memory paths.",
        "wraps": "src/jarvis_memory_board.py",
        "api": "GET /api/jarvis/memory-path-governance/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "knowledge_authority_organ",
        "display": "Knowledge Authority Organ",
        "module_id": "AAIS-KA-01",
        "order": 3,
        "parents": ["memory_path_governance_organ", "operator_profile_organ"],
        "purpose": "Bounded read-only knowledge authority snapshot without flattening source truth.",
        "wraps": "src/knowledge_authority.py",
        "api": "GET /api/jarvis/knowledge-authority/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "scorpion_bridge_organ",
        "display": "Scorpion Bridge Organ",
        "module_id": "AAIS-SB-01",
        "order": 4,
        "parents": ["forensic_triangulation", "governed_direct_pipeline"],
        "purpose": "Read-only Scorpion drift/ledger snapshot; documents Jarvis bridge gap.",
        "wraps": "scorpion/scorpion.py",
        "api": "GET /api/jarvis/scorpion-bridge/status",
        "proof_subdir": "forensics",
    },
    {
        "gene": "mechanic_handoff_organ",
        "display": "Mechanic Handoff Organ",
        "module_id": "AAIS-MH-01",
        "order": 5,
        "parents": ["scorpion_bridge_organ", "capability_service_bridge"],
        "purpose": "Observe Mechanic chat enforcement handoff state without mutating cases.",
        "wraps": "mechanic/integration/chat_hook.py",
        "api": "GET /api/jarvis/mechanic-handoff/status",
        "proof_subdir": "forensics",
    },
    {
        "gene": "forensic_triangulation_organ",
        "display": "Forensic Triangulation Organ",
        "module_id": "AAIS-FT-01",
        "order": 6,
        "parents": ["mechanic_handoff_organ", "forensic_triangulation"],
        "purpose": "Organ shell over triangulation correlator; subordinate to forensic_triangulation genome.",
        "wraps": "triangulation/",
        "api": "GET /api/jarvis/forensic-triangulation/status",
        "proof_subdir": "forensics",
    },
    {
        "gene": "immune_observe_organ",
        "display": "Immune Observe Organ",
        "module_id": "AAIS-IO-01",
        "order": 7,
        "parents": ["realtime_event_cause_predictor_organ", "safety_envelope_organ"],
        "purpose": "Read-only immune observe_protocol_signal posture and snapshot.",
        "wraps": "src/immune_system.py",
        "api": "GET /api/jarvis/immune-observe/status",
        "proof_subdir": "nova",
    },
    {
        "gene": "policy_gate_organ",
        "display": "Policy Gate Organ",
        "module_id": "AAIS-PG2-01",
        "order": 8,
        "parents": ["immune_observe_organ", "phase_gate_organ"],
        "purpose": "Document blocked autonomous immune escalation; MP-X enrollment stub only.",
        "wraps": "docs/contracts/AAIS_IMMUNE_PROTOCOL.md",
        "api": "GET /api/jarvis/policy-gate/status",
        "proof_subdir": "nova",
    },
    {
        "gene": "predictor_immune_bridge_organ",
        "display": "Predictor Immune Bridge Organ",
        "module_id": "AAIS-PIB-01",
        "order": 9,
        "parents": ["policy_gate_organ", "realtime_event_cause_predictor_organ"],
        "purpose": "Attest Alt-9 predictor producer to immune observe path; observe-only.",
        "wraps": "src/realtime_event_cause_predictor_organ.py",
        "api": "GET /api/jarvis/predictor-immune-bridge/status",
        "proof_subdir": "nova",
    },
]


def schema_for(gene: str, module_id: str) -> dict:
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

Status: pending — Alt-10 summon wave `{BATCH}`.

## 1. Purpose

{o['purpose']}

Wraps: [`{o['wraps']}`](../../{o['wraps']}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only organ surface; no mutation authority.

## 3. Non-Goals

- No autonomous escalation or repo mutation
- No replacement of underlying governed subsystems

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

`concept → prototype → mvp` via `tools/governance/alt10_promote_mvp.py`.
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
            "notes": f"Alt-10 wave {o['order']}",
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
        schema = schema_for(gene, o["module_id"])
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

    print(f"[alt10-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
