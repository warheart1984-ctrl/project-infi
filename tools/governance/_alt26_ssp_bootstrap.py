#!/usr/bin/env python3
"""One-shot bootstrap for Release 26 SSP concept artifacts (Wave 17 operational closure)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt26-summon-wave-2026-06"

CONTRACTS = [
    "docs/contracts/AAIS_SSP_PROTOCOL.md",
    "docs/contracts/AAIS_SSP_PROMOTION_PROTOCOL.md",
    "docs/contracts/AAIS_SUBSYSTEM_GENOME.md",
    "docs/contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md",
    "docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md",
    "docs/runtime/AAIS_RUNTIME_GUIDE.md",
]

ORGANS = [
    {
        "api": "GET /api/jarvis/linguistic-governance-day/status",
        "display": "Linguistic Governance Day Subsystem",
        "gene": "linguistic_governance_day_organ",
        "module_id": "AAIS-LGD-01",
        "order": 1,
        "parents": ["linguistic_governed_lifecycle_fabric_organ"],
        "proof_subdir": "platform",
        "purpose": "Read-only operator day orchestrator posture (Wave 17).",
        "wraps": "src/governance_organs/linguistic_governance_day_engine.py",
    },
    {
        "api": "GET /api/jarvis/linguistic-work-order-history/status",
        "display": "Linguistic Work Order History Subsystem",
        "gene": "linguistic_work_order_history_organ",
        "module_id": "AAIS-LWOH-01",
        "order": 2,
        "parents": [
            "linguistic_governance_work_order_organ",
            "linguistic_governed_lifecycle_fabric_organ",
        ],
        "proof_subdir": "platform",
        "purpose": "Read-only work-order snapshot retention posture.",
        "wraps": "governance/linguistic_work_order_snapshots/",
    },
    {
        "api": "GET /api/jarvis/linguistic-attestation-history/status",
        "display": "Linguistic Attestation History Subsystem",
        "gene": "linguistic_attestation_history_organ",
        "module_id": "AAIS-LAH-01",
        "order": 3,
        "parents": [
            "linguistic_governance_attestation_organ",
            "linguistic_governed_lifecycle_fabric_organ",
        ],
        "proof_subdir": "platform",
        "purpose": "Read-only attestation cycle history posture.",
        "wraps": "governance/linguistic_attestation_cycles/",
    },
]

LINEAGE_CHILDREN: dict[str, list[str]] = {
    "linguistic_governed_lifecycle_fabric_organ": [
        "linguistic_governance_day_organ",
        "linguistic_work_order_history_organ",
        "linguistic_attestation_history_organ",
    ],
    "linguistic_governance_work_order_organ": ["linguistic_work_order_history_organ"],
    "linguistic_governance_attestation_organ": ["linguistic_attestation_history_organ"],
}


def schema_for(gene: str) -> dict:
    version_field = f"{gene}_version"
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{gene}.v1",
        "title": f"{gene} v1",
        "type": "object",
        "required": [version_field, "module_id", "cisiv_stage", "claim_label"],
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

Status: pending — Release 26 (`{BATCH}`).

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

## 10. Activation Order

**Release:** `{BATCH}` — order **{o['order']}**

**Depends on:** {', '.join(f'`{p}`' for p in o['parents'])}
"""


def _gate_slug(gene: str) -> str:
    return gene.removesuffix("_organ").replace("_", "-")


def mvp_md(o: dict) -> str:
    gene = o["gene"]
    gate = _gate_slug(gene)
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

`concept → prototype → mvp` via `tools/governance/alt26_promote_mvp.py`.
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
            "contracts": CONTRACTS,
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
            "notes": f"Release 26 wave {o['order']}",
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


def _merge_genome(existing: dict, template: dict) -> dict:
    merged = dict(template)
    for key in ("identity", "runtime", "proof", "ssp", "lineage"):
        if key in existing:
            base = dict(merged.get(key) or {})
            overlay = dict(existing[key])
            base.update(overlay)
            merged[key] = base
    stage = (existing.get("identity") or {}).get("stage")
    if stage in {"mvp", "governed"}:
        merged.setdefault("identity", {})["stage"] = stage
        version = (existing.get("identity") or {}).get("version")
        if version:
            merged.setdefault("identity", {})["version"] = version
    if stage == "governed":
        merged.setdefault("proof", {})["posture"] = "governed"
        merged.setdefault("schema", {})["frozen"] = True
    elif stage == "mvp":
        merged.setdefault("proof", {})["posture"] = "asserted"
    return merged


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


def _proof_md(o: dict) -> str:
    gene = o["gene"]
    gate = _gate_slug(gene)
    return (
        f"# {o['display']} — V1 Proof\n\n"
        f"Release 26 — `{BATCH}`.\n\n"
        f"- Status API: `{o['api']}`\n"
        f"- Gate: `make {gate}-organ-gate`\n"
    )


def main() -> None:
    ideas = ROOT / "docs/_future/ideas_pending"
    schemas_dir = ROOT / "schemas"
    ideas_schemas = ideas / "schemas"
    genomes = ROOT / "governance/subsystem_genomes"
    proof_dir = ROOT / "docs/proof/platform"

    for o in ORGANS:
        gene = o["gene"]
        schema = schema_for(gene)
        for path in (
            schemas_dir / f"{gene}.v1.json",
            ideas_schemas / f"{gene}.v1.json",
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        (ideas / f"{gene.upper()}.md").write_text(concept_md(o), encoding="utf-8")
        (ideas / f"{gene.upper()}_MVP_PLAN.md").write_text(mvp_md(o), encoding="utf-8")
        genome_path = genomes / f"{gene}.genome.v1.json"
        template = genome_for(o)
        if genome_path.is_file():
            existing = json.loads(genome_path.read_text(encoding="utf-8"))
            genome_data = _merge_genome(existing, template)
        else:
            genome_data = template
        genome_path.write_text(json.dumps(genome_data, indent=2) + "\n", encoding="utf-8")
        proof = proof_dir / f"{gene.upper()}_V1_PROOF.md"
        proof.parent.mkdir(parents=True, exist_ok=True)
        proof.write_text(_proof_md(o), encoding="utf-8")

    _sync_lineage_children(genomes)
    print(f"[alt26-ssp] wrote {len(ORGANS)} concept bundles")


if __name__ == "__main__":
    main()
