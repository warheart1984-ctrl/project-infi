#!/usr/bin/env python3
"""One-shot bootstrap for Release 22 SSP concept artifacts (schemas, specs, genomes)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt22-summon-wave-2026-06"

ORGANS = [
    {
        "api": "GET /api/jarvis/naming-protocol/status",
        "display": "Naming Protocol Subsystem",
        "gene": "naming_protocol_organ",
        "module_id": "AAIS-NPR-01",
        "order": 1,
        "parents": ["module_governance_organ", "governance_layer_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only Codex/Cursor naming protocol lint posture (Wave 0).",
        "wraps": "tools/naming_protocol_lint.py",
    },
    {
        "api": "GET /api/jarvis/naming-genome/status",
        "display": "Naming Genome Subsystem",
        "gene": "naming_genome_organ",
        "module_id": "AAIS-NGN-01",
        "order": 2,
        "parents": ["naming_protocol_organ", "operator_cognition_coherence_fabric"],
        "proof_subdir": "platform",
        "purpose": "Read-only genome/alias/source linguistic cross-check posture.",
        "wraps": "tools/linguistic_genome_lib.py",
    },
    {
        "api": "GET /api/jarvis/linguistic-mutation/status",
        "display": "Linguistic Mutation Subsystem",
        "gene": "linguistic_mutation_organ",
        "module_id": "AAIS-LMU-01",
        "order": 3,
        "parents": ["naming_genome_organ", "module_governance_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only linguistic_layer MP-X mutation engine posture (Wave 5).",
        "wraps": "src/governance_organs/linguistic_mutation_engine.py",
    },
    {
        "api": "GET /api/jarvis/mythic-engineering-translator/status",
        "display": "Mythic Engineering Translator Subsystem",
        "gene": "mythic_engineering_translator_organ",
        "module_id": "AAIS-MET-01",
        "order": 4,
        "parents": ["naming_protocol_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only mythic→engineering translator posture (Wave 6).",
        "wraps": "tools/mythic_engineering_translator.py",
    },
    {
        "api": "GET /api/jarvis/linguistic-drift-predictor/status",
        "display": "Linguistic Drift Predictor Subsystem",
        "gene": "linguistic_drift_predictor_organ",
        "module_id": "AAIS-LDP-01",
        "order": 5,
        "parents": ["naming_genome_organ", "linguistic_mutation_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only hybrid linguistic drift scoring posture (Wave 8).",
        "wraps": "tools/linguistic_drift_predictor.py",
    },
    {
        "api": "GET /api/jarvis/linguistic-lineage-viz/status",
        "display": "Linguistic Lineage Viz Subsystem",
        "gene": "linguistic_lineage_viz_organ",
        "module_id": "AAIS-LLV-01",
        "order": 6,
        "parents": ["cisiv_operator_lineage_console", "naming_genome_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only lineage Mermaid export posture (Wave 7).",
        "wraps": "tools/linguistic_lineage_viz.py",
    },
    {
        "api": "GET /api/jarvis/linguistic-remediation/status",
        "display": "Linguistic Remediation Subsystem",
        "gene": "linguistic_remediation_organ",
        "module_id": "AAIS-LRM-01",
        "order": 7,
        "parents": ["linguistic_drift_predictor_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only drift remediation playbook posture (Wave 9).",
        "wraps": "src/governance_organs/linguistic_remediation_engine.py",
    },
    {
        "api": "GET /api/jarvis/linguistic-cascade/status",
        "display": "Linguistic Cascade Subsystem",
        "gene": "linguistic_cascade_organ",
        "module_id": "AAIS-LCA-01",
        "order": 8,
        "parents": ["linguistic_lineage_viz_organ", "linguistic_mutation_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only lineage cascade policy and ack posture (Wave 10).",
        "wraps": "src/governance_organs/linguistic_cascade_engine.py",
    },
    {
        "api": "GET /api/jarvis/meta-linguistic-governance/status",
        "display": "Meta-Linguistic Governance Subsystem",
        "gene": "meta_linguistic_governance_organ",
        "module_id": "AAIS-MLG-01",
        "order": 9,
        "parents": [
            "naming_protocol_organ",
            "naming_genome_organ",
            "linguistic_mutation_organ",
            "linguistic_remediation_organ",
            "linguistic_cascade_organ",
            "governance_layer_organ",
        ],
        "proof_subdir": "platform",
        "purpose": "Read-only meta-linguistic orchestration and registry posture.",
        "wraps": "src/governance_organs/linguistic_governance_engine.py",
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
    return f"""# {o['display']}

CISIV stage: **concept**

Status: pending — Release 22 (`{BATCH}`).

## 1. Purpose

{o['purpose']}

Wraps: [`{o['wraps']}`](../../{o['wraps']}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only subsystem surface; no mutation authority.

## 3. Non-Goals

- No usurpation of reasoning_executive_organ OODA authority
- No expansion of safety_envelope or capability bridge execute paths
- No autonomous law or patch authority via subsystem API
- No MP-X apply without existing mutation-path gates

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

Target proof packet: `docs/proof/{o['proof_subdir']}/{gene.upper()}_V1_PROOF.md`

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema + MVP plan |
| Structure | `src/{gene}.py` |
| Implementation | API route + gate |
| Verification | V1 proof + subsystem gate |

## 9. Related

- [AAIS_SSP_PROTOCOL.md](../../contracts/AAIS_SSP_PROTOCOL.md)
- [AAIS_META_LINGUISTIC_GOVERNANCE.md](../../contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md)
- [AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](../../contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md)

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

`concept → prototype → mvp` via `tools/governance/alt22_promote_mvp.py`.
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
                "docs/contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md",
                "docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md",
                "docs/runtime/AAIS_RUNTIME_GUIDE.md",
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
            "notes": f"Release 22 wave {o['order']}",
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


LINEAGE_CHILDREN: dict[str, list[str]] = {
    "module_governance_organ": ["naming_protocol_organ", "linguistic_mutation_organ"],
    "governance_layer_organ": [
        "naming_protocol_organ",
        "meta_linguistic_governance_organ",
    ],
    "naming_protocol_organ": [
        "naming_genome_organ",
        "mythic_engineering_translator_organ",
        "meta_linguistic_governance_organ",
    ],
    "operator_cognition_coherence_fabric": ["naming_genome_organ"],
    "naming_genome_organ": [
        "linguistic_mutation_organ",
        "linguistic_drift_predictor_organ",
        "linguistic_lineage_viz_organ",
        "meta_linguistic_governance_organ",
    ],
    "linguistic_mutation_organ": [
        "linguistic_drift_predictor_organ",
        "linguistic_cascade_organ",
        "meta_linguistic_governance_organ",
    ],
    "cisiv_operator_lineage_console": ["linguistic_lineage_viz_organ"],
    "linguistic_drift_predictor_organ": ["linguistic_remediation_organ"],
    "linguistic_lineage_viz_organ": ["linguistic_cascade_organ"],
    "linguistic_remediation_organ": ["meta_linguistic_governance_organ"],
    "linguistic_cascade_organ": ["meta_linguistic_governance_organ"],
}


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

    _sync_lineage_children(genomes)
    print(f"[alt22-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
