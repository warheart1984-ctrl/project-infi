#!/usr/bin/env python3
"""One-shot bootstrap for Alt-12 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt12-summon-wave-2026-06"

ORGANS = [
    {
        "gene": "otem_bounded_organ",
        "display": "OTEM Bounded Organ",
        "module_id": "AAIS-OTEM-01",
        "order": 1,
        "parents": ["cognitive_bridge_organ", "safety_envelope_organ", "operator_profile_organ"],
        "purpose": "Read-only OTEM v5_frozen ceiling posture: proposal-only, no execution or workflow mutation.",
        "wraps": "src/otem_runtime.py",
        "api": "GET /api/jarvis/otem-bounded/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "direct_challenge_organ",
        "display": "Direct Challenge Organ",
        "module_id": "AAIS-DC-01",
        "order": 2,
        "parents": ["otem_bounded_organ", "operator_profile_organ"],
        "purpose": "Read-only direct challenge / relational lane severity posture.",
        "wraps": "src/direct_challenge_module.py",
        "api": "GET /api/jarvis/direct-challenge/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "orchestration_spine_organ",
        "display": "Orchestration Spine Organ",
        "module_id": "AAIS-OSP-01",
        "order": 3,
        "parents": ["direct_challenge_organ", "governed_direct_pipeline"],
        "purpose": "Read-only God Brain + V8 spine routing posture without granting new authority.",
        "wraps": "src/god_brain.py",
        "api": "GET /api/jarvis/orchestration-spine/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "operator_health_sentinel_organ",
        "display": "Operator Health Sentinel Organ",
        "module_id": "AAIS-OHSO-01",
        "order": 4,
        "parents": ["orchestration_spine_organ", "realtime_event_cause_predictor_organ"],
        "purpose": "Advisory-only operator burden snapshot from governed trace surfaces.",
        "wraps": "src/operator_health_sentinel.py",
        "api": "GET /api/jarvis/operator-health-sentinel/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "governed_realtime_lane_organ",
        "display": "Governed Realtime Lane Organ",
        "module_id": "AAIS-GRL-01",
        "order": 5,
        "parents": ["operator_health_sentinel_organ", "governed_direct_pipeline"],
        "purpose": "Read-only governed pipeline realtime producer lane posture.",
        "wraps": "src/governed_direct_pipeline.py",
        "api": "GET /api/jarvis/governed-realtime-lane/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "v8_runtime_organ",
        "display": "V8 Runtime Organ",
        "module_id": "AAIS-V8O-01",
        "order": 6,
        "parents": ["governed_realtime_lane_organ", "phase_gate_organ"],
        "purpose": "Read-only V8 event spine session-state visibility.",
        "wraps": "src/v8_runtime.py",
        "api": "GET /api/jarvis/v8-runtime/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "patch_apply_organ",
        "display": "Patch Apply Organ",
        "module_id": "AAIS-PAP-01",
        "order": 7,
        "parents": ["patch_verification_organ", "change_scope_organ"],
        "purpose": "Read-only patch apply engine gate posture; apply remains operator-gated.",
        "wraps": "src/patch_apply_engine.py",
        "api": "GET /api/jarvis/patch-apply/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "patch_execution_preview_organ",
        "display": "Patch Execution Preview Organ",
        "module_id": "AAIS-PEP-01",
        "order": 8,
        "parents": ["patch_apply_organ"],
        "purpose": "Read-only execution preview posture for patch lanes.",
        "wraps": "src/patch_execution_preview.py",
        "api": "GET /api/jarvis/patch-execution-preview/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "run_ledger_organ",
        "display": "Run Ledger Organ",
        "module_id": "AAIS-RLO-01",
        "order": 9,
        "parents": ["patch_execution_preview_organ", "patchforge_organ"],
        "purpose": "Read-only run ledger snapshot for repo mutation history posture.",
        "wraps": "src/run_ledger.py",
        "api": "GET /api/jarvis/run-ledger/status",
        "proof_subdir": "platform",
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

Status: pending — Alt-12 summon wave `{BATCH}`.

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

`concept → prototype → mvp` via `tools/governance/alt12_promote_mvp.py`.
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
            "notes": f"Alt-12 wave {o['order']}",
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

    print(f"[alt12-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
