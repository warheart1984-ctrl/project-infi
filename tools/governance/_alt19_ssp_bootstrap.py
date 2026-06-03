#!/usr/bin/env python3
"""One-shot bootstrap for Alt-19 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt19-summon-wave-2026-06"

ORGANS = [{'api': 'GET /api/jarvis/launcher/status',
  'display': 'Launcher Organ',
  'gene': 'launcher_organ',
  'module_id': 'AAIS-LCH-01',
  'order': 1,
  'parents': ['workflow_shell_organ', 'capability_service_bridge'],
  'proof_subdir': 'platform',
  'purpose': 'Read-only AAIS launcher package posture.',
  'wraps': 'aais/launcher.py'},
 {'api': 'GET /api/jarvis/aais-doctor/status',
  'display': 'AAIS Doctor Organ',
  'gene': 'aais_doctor_organ',
  'module_id': 'AAIS-DOC-01',
  'order': 2,
  'parents': ['launcher_organ'],
  'proof_subdir': 'platform',
  'purpose': 'Read-only aais doctor readiness posture.',
  'wraps': 'aais/__main__.py'},
 {'api': 'GET /api/jarvis/workflow-runtime/status',
  'display': 'Workflow Runtime Organ',
  'gene': 'workflow_runtime_organ',
  'module_id': 'AAIS-WRT-01',
  'order': 3,
  'parents': ['workflow_shell_organ', 'launcher_organ'],
  'proof_subdir': 'platform',
  'purpose': 'Read-only app/workflow_runtime posture (distinct from workflow_shell_organ).',
  'wraps': 'app/workflow_runtime.py'},
 {'api': 'GET /api/jarvis/jarvis-console-surface/status',
  'display': 'Jarvis Console Surface Organ',
  'gene': 'jarvis_console_surface_organ',
  'module_id': 'AAIS-JCS-01',
  'order': 4,
  'parents': ['jarvis_operator_organ'],
  'proof_subdir': 'platform',
  'purpose': 'Read-only Jarvis Console UI binding posture.',
  'wraps': 'frontend/src/pages/JarvisConsole.jsx'},
 {'api': 'GET /api/jarvis/memory-bank-surface/status',
  'display': 'Memory Bank Surface Organ',
  'gene': 'memory_bank_surface_organ',
  'module_id': 'AAIS-MBS-01',
  'order': 5,
  'parents': ['jarvis_memory_board', 'jarvis_console_surface_organ'],
  'proof_subdir': 'platform',
  'purpose': 'Read-only Memory Bank UI binding posture.',
  'wraps': 'frontend/src/pages/MemoryBank.jsx'},
 {'api': 'GET /api/jarvis/dashboard-surface/status',
  'display': 'Dashboard Surface Organ',
  'gene': 'dashboard_surface_organ',
  'module_id': 'AAIS-DBS-01',
  'order': 6,
  'parents': ['governance_layer_organ', 'jarvis_console_surface_organ'],
  'proof_subdir': 'platform',
  'purpose': 'Read-only Dashboard governance views posture.',
  'wraps': 'frontend/src/pages/Dashboard.jsx'},
 {'api': 'GET /api/jarvis/nova-landing-surface/status',
  'display': 'Nova Landing Surface Organ',
  'gene': 'nova_landing_surface_organ',
  'module_id': 'AAIS-NLS-01',
  'order': 7,
  'parents': ['nova_face_organ', 'jarvis_console_surface_organ'],
  'proof_subdir': 'platform',
  'purpose': 'Read-only Nova landing surface posture.',
  'wraps': 'frontend/src/pages/NovaLandingPage.jsx'},
 {'api': 'GET /api/jarvis/aais-composed-runtime/status',
  'display': 'AAIS Composed Runtime Organ',
  'gene': 'aais_composed_runtime_organ',
  'module_id': 'AAIS-ACR-01',
  'order': 8,
  'parents': ['jarvis_operator_organ', 'governance_layer_organ'],
  'proof_subdir': 'platform',
  'purpose': 'Read-only composed runtime posture.',
  'wraps': 'src/aais_composed_runtime.py'},
 {'api': 'GET /api/jarvis/api-gateway/status',
  'display': 'API Gateway Organ',
  'gene': 'api_gateway_organ',
  'module_id': 'AAIS-AGW-01',
  'order': 9,
  'parents': ['jarvis_operator_organ', 'capability_service_bridge'],
  'proof_subdir': 'platform',
  'purpose': 'Read-only bounded api.py ingress posture.',
  'wraps': 'src/api.py'}]


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

Status: pending — Alt-19 summon wave `{BATCH}`.

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

`concept → prototype → mvp` via `tools/governance/alt19_promote_mvp.py`.
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
            "notes": f"Alt-19 wave {o['order']}",
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

    print(f"[alt19-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
