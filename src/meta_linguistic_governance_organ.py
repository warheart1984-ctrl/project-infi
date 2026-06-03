"""Meta-Linguistic Governance Subsystem — orchestration and registry posture."""

# Mythic: Meta Linguistic Governance Organ
# Engineering: MetaLinguisticGovernanceEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-MLG-01"
ORGAN_VERSION = "meta_linguistic_governance_organ.v1"


def build_meta_linguistic_governance_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_governance_engine.py"
    ).is_file()
    registry = (root / "governance" / "meta_linguistic_registry.v1.json").is_file()
    contract = (
        root / "docs" / "contracts" / "AAIS_META_LINGUISTIC_GOVERNANCE.md"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "meta-linguistic-gate:" in m_text
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    route = "/api/jarvis/meta-linguistic-governance/status" in text
    return {
        "meta_linguistic_governance_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};registry={int(registry)};route={int(route)}"[:128],
        "linguistic_governance_engine_present": engine,
        "meta_linguistic_registry_present": registry,
        "meta_linguistic_contract_present": contract,
        "meta_linguistic_gate_in_makefile": gate,
        "status_route_present": route,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
