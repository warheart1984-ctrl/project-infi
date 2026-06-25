#!/usr/bin/env python3
"""One-shot bootstrap for Release 20 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt20-summon-wave-2026-06"

ORGANS = [
    {
        "api": "GET /api/jarvis/memory-smith/status",
        "display": "Memory Smith Subsystem",
        "gene": "memory_smith_organ",
        "module_id": "AAIS-MSM-01",
        "order": 1,
        "parents": ["jarvis_memory_board", "memory_path_governance_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only memory curation and review posture (Memory Smith).",
        "wraps": "src/memory_smith.py",
    },
    {
        "api": "GET /api/jarvis/operator-workspace/status",
        "display": "Operator Workspace Subsystem",
        "gene": "operator_workspace_organ",
        "module_id": "AAIS-OWS-01",
        "order": 2,
        "parents": ["capability_service_bridge", "jarvis_operator_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only Jarvis workspace API cluster posture (projects, search, symbols).",
        "wraps": "src/api.py",
    },
    {
        "api": "GET /api/jarvis/jarvis-runs/status",
        "display": "Jarvis Runs Subsystem",
        "gene": "jarvis_runs_organ",
        "module_id": "AAIS-JRN-01",
        "order": 3,
        "parents": ["run_ledger_organ", "run_ledger_binding_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only Jarvis runs ledger API posture.",
        "wraps": "src/api.py",
    },
    {
        "api": "GET /api/jarvis/state-hygiene/status",
        "display": "State Hygiene Subsystem",
        "gene": "state_hygiene_organ",
        "module_id": "AAIS-SHY-01",
        "order": 4,
        "parents": ["governance_layer_organ", "jarvis_operator_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only state hygiene and compaction posture.",
        "wraps": "src/state_hygiene.py",
    },
    {
        "api": "GET /api/jarvis/blueprint-posture/status",
        "display": "Blueprint Posture Subsystem",
        "gene": "blueprint_posture_organ",
        "module_id": "AAIS-BPP-01",
        "order": 5,
        "parents": ["project_infi_law_organ", "aais_ul_substrate_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only AAIS blueprint snapshot posture.",
        "wraps": "src/aais_blueprint.py",
    },
    {
        "api": "GET /api/jarvis/workflow-interfaces/status",
        "display": "Workflow Interfaces Subsystem",
        "gene": "workflow_interfaces_organ",
        "module_id": "AAIS-WIF-01",
        "order": 6,
        "parents": ["workflow_shell_organ", "workflow_runtime_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only workflow UI interfaces (builder, runs, approvals, templates).",
        "wraps": "frontend/src/pages/WorkflowBuilder.jsx",
    },
    {
        "api": "GET /api/jarvis/platform-console-interfaces/status",
        "display": "Platform Console Interfaces Subsystem",
        "gene": "platform_console_interfaces_organ",
        "module_id": "AAIS-PCI-01",
        "order": 7,
        "parents": ["api_gateway_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only platform console UI cluster posture.",
        "wraps": "frontend/src/pages/PlatformConsole.jsx",
    },
    {
        "api": "GET /api/jarvis/operator-console-interface/status",
        "display": "Operator Console Interface Subsystem",
        "gene": "operator_console_interface_organ",
        "module_id": "AAIS-OCI-01",
        "order": 8,
        "parents": ["jarvis_console_surface_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only Operator Console UI binding posture.",
        "wraps": "frontend/src/pages/OperatorConsole.jsx",
    },
    {
        "api": "GET /api/jarvis/nova-workspace-interface/status",
        "display": "Nova Workspace Interface Subsystem",
        "gene": "nova_workspace_interface_organ",
        "module_id": "AAIS-NWI-01",
        "order": 9,
        "parents": ["nova_landing_surface_organ", "nova_face_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only Nova and Jarvis workspace page interfaces.",
        "wraps": "frontend/src/pages/NovaPage.jsx",
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

Status: pending — Release 20 (`{BATCH}`).

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
- `src/{gene}.py` — status builder

## 6. Failsafe

Idle or missing upstream returns bounded snapshot with `claim_label` asserted.

## 7. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema covers required subsystem fields | `asserted` | Schema + this document |
| Status API returns snapshot | `none_yet` | Requires MVP |

Target proof packet: `docs/proof/{o['proof_subdir']}/{upper}_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/{gene}.py` |
| Implementation | API route + gate |
| Verification | V1 proof + subsystem gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [JARVIS_PROTOCOL.md](../../contracts/JARVIS_PROTOCOL.md)

## 10. Activation Order

**Release:** `{BATCH}` — order **{o['order']}**

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

Release: `{BATCH}`

## MVP Surface

| Kind | Path |
|------|------|
| module | `src/{gene}.py` |
| api | `{o['api']}` |
| gate | `make {gate}-organ-gate` |

## Proof

`docs/proof/{o['proof_subdir']}/{gene.upper()}_V1_PROOF.md`

## Promotion

`concept → prototype → mvp` via `tools/governance/alt20_promote_mvp.py`.
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
                "Read-only v1 — subsystem does not mutate upstream authority",
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
            "notes": f"Release 20 wave {o['order']}",
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

    print(f"[alt20-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
