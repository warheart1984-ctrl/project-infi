"""Linguistic Full Governance Cycle Subsystem — Wave 13–14 orchestration posture."""

# Mythic: Linguistic Full Governance Cycle Organ
# Engineering: LinguisticFullGovernanceCycleEngine
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LFG-01"
ORGAN_VERSION = "linguistic_full_governance_cycle_organ.v1"


def build_linguistic_full_governance_cycle_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_full_governance_cycle_engine.py"
    ).is_file()
    cycles_dir = (root / "governance" / "linguistic_full_governance_cycles").is_dir()
    last_passed = None
    reg_path = root / "governance" / "meta_linguistic_registry.v1.json"
    if reg_path.is_file():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        rel = reg.get("last_full_cycle_report")
        if rel and (root / rel).is_file():
            data = json.loads((root / rel).read_text(encoding="utf-8"))
            last_passed = data.get("passed")
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    return {
        "linguistic_full_governance_cycle_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": (
            f"engine={int(engine)};history={int(cycles_dir)};passed={last_passed}"
        )[:128],
        "full_cycle_engine_present": engine,
        "full_cycle_history_present": cycles_dir,
        "last_full_cycle_passed": last_passed,
        "linguistic_full_governance_cycle_in_makefile": (
            "linguistic-full-governance-cycle:" in m_text
        ),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
