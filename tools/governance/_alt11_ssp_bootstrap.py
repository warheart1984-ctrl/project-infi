#!/usr/bin/env python3
"""One-shot bootstrap for Alt-11 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt11-summon-wave-2026-06"

ORGANS = [
    {
        "gene": "cognitive_bridge_organ",
        "display": "Cognitive Bridge Organ",
        "module_id": "AAIS-CB-01",
        "order": 1,
        "parents": ["safety_envelope_organ", "operator_profile_organ", "governed_direct_pipeline"],
        "purpose": "Read-only cognitive bridge ingress posture: packet shape, governance fingerprint, bridge decision class.",
        "wraps": "src/cognitive_bridge.py",
        "api": "GET /api/jarvis/cognitive-bridge/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "governed_event_chain_organ",
        "display": "Governed Event Chain Organ",
        "module_id": "AAIS-GEC-01",
        "order": 2,
        "parents": ["cognitive_bridge_organ", "phase_gate_organ", "realtime_event_cause_predictor_organ"],
        "purpose": "Read-only predictor→invariant→immune chain posture; observe-only at boundary.",
        "wraps": "src/governed_event_chain.py",
        "api": "GET /api/jarvis/governed-event-chain/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "tracing_spine_organ",
        "display": "Tracing Spine Organ",
        "module_id": "AAIS-TS-01",
        "order": 3,
        "parents": ["governed_event_chain_organ", "governed_direct_pipeline", "cognitive_bridge_organ"],
        "purpose": "Canonical governed trace stage visibility per AAIS_TRACING_PROTOCOL; missing-trace fail-closed flag.",
        "wraps": "docs/contracts/AAIS_TRACING_PROTOCOL.md",
        "api": "GET /api/jarvis/tracing-spine/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "mission_board_organ",
        "display": "Mission Board Organ",
        "module_id": "AAIS-MB-01",
        "order": 4,
        "parents": ["verification_gate_organ", "cognitive_bridge_organ"],
        "purpose": "Read-only mission board snapshot joined with verification gate posture.",
        "wraps": "src/mission_board.py",
        "api": "GET /api/jarvis/mission-board/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "aris_boundary_organ",
        "display": "ARIS Boundary Organ",
        "module_id": "AAIS-ARIS-01",
        "order": 5,
        "parents": ["mission_board_organ", "cognitive_bridge_organ"],
        "purpose": "Embedded ARIS profile: share-mode posture and non-copy enforcement snapshot.",
        "wraps": "src/aris_integration.py",
        "api": "GET /api/jarvis/aris-boundary/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "capability_module_organ",
        "display": "Capability Module Organ",
        "module_id": "AAIS-CM-01",
        "order": 6,
        "parents": ["capability_service_bridge", "phase_gate_organ", "aris_boundary_organ"],
        "purpose": "Capability module layer posture over governed service bridge; universal-bridge gap map.",
        "wraps": "src/capability_module.py",
        "api": "GET /api/jarvis/capability-module/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "patchforge_organ",
        "display": "Patchforge Organ",
        "module_id": "AAIS-PF-01",
        "order": 7,
        "parents": ["tracing_spine_organ", "capability_module_organ"],
        "purpose": "Read-only PatchForge proposal/preview-only attestation.",
        "wraps": "src/patchforge.py",
        "api": "GET /api/jarvis/patchforge/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "change_scope_organ",
        "display": "Change Scope Organ",
        "module_id": "AAIS-CS-01",
        "order": 8,
        "parents": ["patchforge_organ"],
        "purpose": "Read-only workspace impact snapshot from change scope analysis.",
        "wraps": "src/change_scope.py",
        "api": "GET /api/jarvis/change-scope/status",
        "proof_subdir": "platform",
    },
    {
        "gene": "patch_verification_organ",
        "display": "Patch Verification Organ",
        "module_id": "AAIS-PV-01",
        "order": 9,
        "parents": ["change_scope_organ", "patchforge_organ"],
        "purpose": "Verify/preview/apply gate posture for test oracle and patch apply engine.",
        "wraps": "src/test_oracle.py",
        "api": "GET /api/jarvis/patch-verification/status",
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

Status: pending — Alt-11 summon wave `{BATCH}`.

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
- [AAIS_TRACING_PROTOCOL.md](../../contracts/AAIS_TRACING_PROTOCOL.md)

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

`concept → prototype → mvp` via `tools/governance/alt11_promote_mvp.py`.
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
            "notes": f"Alt-11 wave {o['order']}",
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

    print(f"[alt11-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
