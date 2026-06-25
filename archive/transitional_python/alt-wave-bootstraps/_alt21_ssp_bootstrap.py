#!/usr/bin/env python3
"""One-shot bootstrap for Release 21 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt21-summon-wave-2026-06"

ORGANS = [
    {
        "api": "GET /api/jarvis/creative-core-runtime/status",
        "display": "Creative Core Runtime Subsystem",
        "gene": "creative_core_runtime_organ",
        "module_id": "AAIS-CCR-01",
        "order": 1,
        "parents": ["v8_runtime_organ", "phase_gate_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only bounded creative core runtime posture (shared wrapper).",
        "wraps": "src/creative_core_runtime.py",
    },
    {
        "api": "GET /api/jarvis/v9-core/status",
        "display": "V9 Core Subsystem",
        "gene": "v9_core_organ",
        "module_id": "AAIS-V9C-01",
        "order": 2,
        "parents": ["creative_core_runtime_organ", "capability_service_bridge"],
        "proof_subdir": "platform",
        "purpose": "Read-only V9 core lane posture; inspects POST /api/jarvis/v9-core.",
        "wraps": "src/v9_core.py",
    },
    {
        "api": "GET /api/jarvis/v9-runtime/status",
        "display": "V9 Runtime Subsystem",
        "gene": "v9_runtime_organ",
        "module_id": "AAIS-V9R-01",
        "order": 3,
        "parents": ["v9_core_organ", "creative_core_runtime_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only V9 runtime snapshot posture; inspects GET /api/jarvis/v9-runtime.",
        "wraps": "src/v9_runtime.py",
    },
    {
        "api": "GET /api/jarvis/v10-core/status",
        "display": "V10 Core Subsystem",
        "gene": "v10_core_organ",
        "module_id": "AAIS-V10C-01",
        "order": 4,
        "parents": ["creative_core_runtime_organ", "capability_service_bridge"],
        "proof_subdir": "platform",
        "purpose": "Read-only V10 core lane posture; inspects POST /api/jarvis/v10-core.",
        "wraps": "src/v10_core.py",
    },
    {
        "api": "GET /api/jarvis/v10-runtime/status",
        "display": "V10 Runtime Subsystem",
        "gene": "v10_runtime_organ",
        "module_id": "AAIS-V10R-01",
        "order": 5,
        "parents": ["v10_core_organ", "creative_core_runtime_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only V10 runtime snapshot posture; inspects GET /api/jarvis/v10-runtime.",
        "wraps": "src/v10_runtime.py",
    },
    {
        "api": "GET /api/jarvis/v10-action-engine/status",
        "display": "V10 Action Engine Subsystem",
        "gene": "v10_action_engine_organ",
        "module_id": "AAIS-V10A-01",
        "order": 6,
        "parents": ["v10_runtime_organ", "jarvis_operator_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only V10 action engine mission-step posture.",
        "wraps": "src/v10_action_engine.py",
    },
    {
        "api": "GET /api/jarvis/creative-capability-bridge/status",
        "display": "Creative Capability Bridge Subsystem",
        "gene": "creative_capability_bridge_organ",
        "module_id": "AAIS-CCB-01",
        "order": 7,
        "parents": ["capability_service_bridge", "v9_runtime_organ", "v10_runtime_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only capability bridge v9/v10 provider path posture.",
        "wraps": "src/capability_service_bridge.py",
    },
    {
        "api": "GET /api/jarvis/creative-operator-handoff/status",
        "display": "Creative Operator Handoff Subsystem",
        "gene": "creative_operator_handoff_organ",
        "module_id": "AAIS-COH-01",
        "order": 8,
        "parents": ["jarvis_operator_organ", "jarvis_reasoning_lane_organ", "adaptive_lane_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only Jarvis operator and model routing creative lane handoff posture.",
        "wraps": "src/jarvis_operator.py",
    },
    {
        "api": "GET /api/jarvis/creative-console-interface/status",
        "display": "Creative Console Interface Subsystem",
        "gene": "creative_console_interface_organ",
        "module_id": "AAIS-CCI-01",
        "order": 9,
        "parents": ["jarvis_console_surface_organ", "api_gateway_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only Jarvis Console and Dashboard v9/v10 UI binding posture.",
        "wraps": "frontend/src/pages/JarvisConsole.jsx",
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

Status: pending — Release 21 (`{BATCH}`).

## 1. Purpose

{o['purpose']}

Wraps: [`{o['wraps']}`](../../{o['wraps']}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only subsystem surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths beyond existing v9/v10 routes
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

`concept → prototype → mvp` via `tools/governance/alt21_promote_mvp.py`.
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
            "notes": f"Release 21 wave {o['order']}",
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

    print(f"[alt21-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
