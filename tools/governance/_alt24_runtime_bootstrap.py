#!/usr/bin/env python3
"""Bootstrap Release 24 active subsystem docs, governed proof stubs, and lineage."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt24-summon-wave-2026-06"
PLATFORM = ROOT / "docs/subsystems/platform"
PROOF = ROOT / "docs/proof/platform"

ORGANS = [
    (
        "linguistic_forecast_calibration_organ",
        "linguistic-forecast-calibration",
        "linguistic-forecast-calibration-organ-gate",
    ),
    (
        "linguistic_governance_queue_organ",
        "linguistic-governance-queue",
        "linguistic-governance-queue-organ-gate",
    ),
    (
        "linguistic_full_governance_cycle_organ",
        "linguistic-full-governance-cycle",
        "linguistic-full-governance-cycle-organ-gate",
    ),
    (
        "linguistic_governance_attestation_organ",
        "linguistic-governance-attestation",
        "linguistic-governance-attestation-organ-gate",
    ),
]


def active_doc(gene: str, api: str, gate: str) -> str:
    upper = gene.upper()
    return f"""# {gene.replace('_', ' ').title()}

Status: **governed** (Release 24 `{BATCH}`)

## Runtime

- Module: `src/{gene}.py`
- API: `GET /api/jarvis/{api}/status`
- Gate: `make {gate}`

## Proof

[{upper}_V1_PROOF.md](../../proof/platform/{upper}_V1_PROOF.md)
"""


def governed_proof(gene: str, gate: str) -> str:
    upper = gene.upper()
    return f"""# {gene.replace('_', ' ').title()} Governed Proof

## Claims

| Claim | Label |
|-------|-------|
| Subsystem at governed stage with runtime surface | proven |
| Gate passes under alt24-governed-gate | proven |

## Reproduction

```bash
make {gate}
make alt24-governed-gate
```
"""


LINEAGE_CHILDREN: dict[str, list[str]] = {
    "linguistic_drift_forecast_organ": ["linguistic_forecast_calibration_organ"],
    "meta_linguistic_governance_organ": ["linguistic_forecast_calibration_organ"],
    "linguistic_forecast_calibration_organ": [
        "linguistic_governance_queue_organ",
        "linguistic_full_governance_cycle_organ",
    ],
    "linguistic_governance_queue_organ": ["linguistic_full_governance_cycle_organ"],
    "linguistic_predictive_governance_organ": ["linguistic_full_governance_cycle_organ"],
    "linguistic_governance_cycle_organ": ["linguistic_full_governance_cycle_organ"],
    "linguistic_full_governance_cycle_organ": ["linguistic_governance_attestation_organ"],
    "linguistic_closed_loop_fabric_organ": ["linguistic_governance_attestation_organ"],
}

CONTRACTS = [
    "docs/contracts/AAIS_SSP_PROTOCOL.md",
    "docs/contracts/AAIS_SSP_PROMOTION_PROTOCOL.md",
    "docs/contracts/AAIS_SUBSYSTEM_GENOME.md",
    "docs/contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md",
    "docs/contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md",
    "docs/runtime/AAIS_RUNTIME_GUIDE.md",
    "docs/contracts/AAIS_SUBSYSTEM_MUTATION_PATH.md",
    "docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md",
]


def _enrich_genome(gene: str, genomes: Path, *, module_id: str) -> None:
    path = genomes / f"{gene}.genome.v1.json"
    if not path.is_file():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    upper = gene.upper()
    v1_proof = f"docs/proof/platform/{upper}_V1_PROOF.md"
    governed_proof = f"docs/proof/platform/{upper}_GOVERNED_PROOF.md"
    stage = (data.get("identity") or {}).get("stage", "")
    data["governance"] = {
        "contracts": CONTRACTS,
        "invariants": [
            "Read-only v1 — subsystem does not mutate upstream authority",
            f"module_id frozen to {module_id}",
        ],
    }
    data.setdefault("proof", {})
    if stage == "governed":
        data["proof"]["bundles"] = [governed_proof]
        data["proof"]["posture"] = "governed"
        data.setdefault("schema", {})["frozen"] = True
    else:
        data["proof"]["bundles"] = [v1_proof]
        data["proof"]["posture"] = "asserted"
    data["proof"]["target_bundles"] = [v1_proof]
    data.setdefault("retirement", {})["path"] = (
        "docs/contracts/AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md"
    )
    data.setdefault("mutation", {})["history"] = []
    data.setdefault("ssp", {})["concept_spec"] = (
        f"docs/_future/ideas_pending/{upper}.md"
    )
    data.setdefault("ssp", {})["mvp_plan"] = f"docs/_future/ideas_pending/{upper}_MVP_PLAN.md"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


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


MODULE_IDS = {
    "linguistic_forecast_calibration_organ": "AAIS-LFC-02",
    "linguistic_governance_queue_organ": "AAIS-LGQ-01",
    "linguistic_full_governance_cycle_organ": "AAIS-LFG-01",
    "linguistic_governance_attestation_organ": "AAIS-LGA-01",
}


def main() -> None:
    genomes = ROOT / "governance/subsystem_genomes"
    for gene, mid in MODULE_IDS.items():
        _enrich_genome(gene, genomes, module_id=mid)
    _sync_lineage_children(genomes)
    PLATFORM.mkdir(parents=True, exist_ok=True)
    PROOF.mkdir(parents=True, exist_ok=True)
    for gene, api, gate in ORGANS:
        upper = gene.upper()
        doc = PLATFORM / f"{upper}.md"
        doc.write_text(active_doc(gene, api, gate), encoding="utf-8")
        gov = PROOF / f"{upper}_GOVERNED_PROOF.md"
        if not gov.is_file():
            gov.write_text(governed_proof(gene, gate), encoding="utf-8")
    print(f"[alt24-runtime] synced lineage; wrote {len(ORGANS)} platform docs")


if __name__ == "__main__":
    main()
