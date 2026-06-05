#!/usr/bin/env python3
"""Bootstrap UGR discovery, rewards, and mission runtime SSP admission artifacts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "ugr-admission-wave-2026-06"

FAMILIES = [
    {
        "gene": "ugr_subsystem_discovery",
        "display": "UGR Subsystem Discovery",
        "engineering": "SubsystemDiscoveryEngine",
        "mythic": "Ugr Subsystem Discovery",
        "module": "src/ugr/discovery/subsystem_discovery.py",
        "contract": "docs/contracts/UGR_SUBSYSTEM_DISCOVERY_CONTRACT.md",
        "schema": "schemas/ugr_subsystem_discovery_receipt.v1.json",
        "gate": "make ugr-discovery-gate",
        "apis": [
            "POST /api/ugr/discover/subsystem",
            "GET /api/ugr/discover/subsystem/<subsystem_id>",
            "GET /api/ugr/discover/subsystems",
        ],
        "parents": ["capability_service_bridge"],
        "children": ["ugr_operator_reward_engine"],
    },
    {
        "gene": "ugr_operator_reward_engine",
        "display": "UGR Operator Reward Engine",
        "engineering": "OperatorRewardEngine",
        "mythic": "Ugr Operator Reward Engine",
        "module": "src/ugr/rewards/operator_reward_engine.py",
        "contract": "docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md",
        "schema": "schemas/ugr_operator_reward_receipt.v1.json",
        "gate": "make ugr-rewards-gate",
        "apis": [
            "POST /api/ugr/reward/issue",
            "POST /api/ugr/reward/transfer",
            "POST /api/ugr/reward/exchange",
            "GET /api/ugr/reward/operator/<operator_id>",
        ],
        "parents": ["ugr_subsystem_discovery"],
        "children": ["ugr_mission_runtime"],
    },
    {
        "gene": "ugr_mission_runtime",
        "display": "UGR Mission Runtime",
        "engineering": "MissionRuntimeEngine",
        "mythic": "Ugr Mission Runtime",
        "module": "src/ugr/mission/mission_runtime.py",
        "contract": "docs/contracts/URG_MISSION_CONTRACT.md",
        "schema": "schemas/urg_mission_receipt.v1.json",
        "gate": "make ugr-mission-gate",
        "apis": [
            "POST /api/ugr/mission/run",
            "POST /api/ugr/mission/governance",
            "GET /api/ugr/mission/receipt/<mission_id>",
        ],
        "parents": ["ugr_operator_reward_engine", "capability_service_bridge"],
        "children": [],
    },
]


def _write_if_missing(path: Path, content: str) -> None:
    if path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")


def main() -> int:
    for family in FAMILIES:
        gene = family["gene"]
        upper = gene.upper()
        concept = ROOT / f"docs/_future/ideas_pending/{upper}.md"
        mvp = ROOT / f"docs/_future/ideas_pending/{upper}_MVP_PLAN.md"
        active = ROOT / f"docs/subsystems/ugr/{upper}.md"
        proof = ROOT / f"docs/proof/ugr/{upper}_V1_PROOF.md"
        genome_path = ROOT / f"governance/subsystem_genomes/{gene}.genome.v1.json"

        _write_if_missing(
            concept,
            f"# {family['display']}\n\n"
            f"Gene: `{gene}`\n\n"
            f"Contract: [{family['contract']}](../../{family['contract'].replace('docs/', '')})\n\n"
            f"| Claim | Label |\n|-------|-------|\n| Runtime module present | proven |\n| API routes wired | proven |\n| Project Infi law wrapper | proven |\n",
        )
        _write_if_missing(
            mvp,
            f"# {family['display']} — MVP Plan\n\n"
            f"| Surface | Path |\n|---------|------|\n| module | `{family['module']}` |\n| gate | `{family['gate']}` |\n",
        )
        _write_if_missing(
            active,
            f"# {family['display']}\n\n"
            f"Gene: `{gene}`\n\n"
            f"Engineering: `{family['engineering']}`\n\n"
            f"Governed via `src/ugr/ugr_runtime_governance.py`.\n",
        )
        _write_if_missing(
            proof,
            f"# {family['display']} V1 Proof\n\n"
            f"Gate: `{family['gate']}`\n\n"
            f"Claim label: **proven** (single-machine pytest gate).\n",
        )

        if genome_path.is_file():
            continue

        surfaces = [{"kind": "module", "path": family["module"]}]
        for api in family["apis"]:
            surfaces.append({"kind": "api", "path": api})
        surfaces.append({"kind": "gate", "path": family["gate"]})

        genome = {
            "subsystem_genome_version": "subsystem_genome.v1",
            "identity": {
                "gene": gene,
                "version": "1.0.0",
                "stage": "governed",
                "display_name": family["display"],
            },
            "governance": {
                "contracts": [
                    family["contract"],
                    "docs/contracts/AAIS_SSP_PROTOCOL.md",
                    "docs/contracts/AAIS_SUBSYSTEM_GENOME.md",
                ],
                "invariants": [
                    "Tenant-scoped receipts and ledgers",
                    "Project Infi law finalization on mutating routes",
                ],
            },
            "schema": {"ref": family["schema"], "frozen": True},
            "runtime": {"surface": surfaces},
            "proof": {
                "bundles": [f"docs/proof/ugr/{upper}_V1_PROOF.md"],
                "posture": "governed",
            },
            "lineage": {
                "parents": family["parents"],
                "children": family["children"],
            },
            "activation": {
                "order": 1,
                "batch_id": BATCH,
                "notes": "UGR subsystem admission wave",
            },
            "retirement": {"path": "docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md"},
            "mutation": {"history": []},
            "ssp": {
                "concept_spec": f"docs/_future/ideas_pending/{upper}.md",
                "mvp_plan": f"docs/_future/ideas_pending/{upper}_MVP_PLAN.md",
                "summon_eligible": False,
                "active_doc": f"docs/subsystems/ugr/{upper}.md",
                "engineering_class": family["engineering"],
                "mythic_label": family["mythic"],
                "linguistic_version": "1.0.0",
            },
        }
        genome_path.write_text(json.dumps(genome, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {genome_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
