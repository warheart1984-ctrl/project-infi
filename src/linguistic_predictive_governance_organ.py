"""Linguistic Predictive Governance Subsystem — Wave 12 predictive cycle posture."""

# Mythic: Linguistic Predictive Governance Organ
# Engineering: LinguisticPredictiveGovernanceEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LPG-01"
ORGAN_VERSION = "linguistic_predictive_governance_organ.v1"


def build_linguistic_predictive_governance_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_predictive_governance_engine.py"
    ).is_file()
    runner = (
        root / "tools" / "governance" / "run_linguistic_predictive_cycle.py"
    ).is_file()
    policy = (
        root / "governance" / "linguistic_predictive_governance_policy.v1.json"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "linguistic-predictive-gate:" in m_text
    cycle = "linguistic-predictive-cycle:" in m_text
    return {
        "linguistic_predictive_governance_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};runner={int(runner)};gate={int(gate)}"[:128],
        "predictive_engine_present": engine,
        "predictive_cycle_runner_present": runner,
        "predictive_policy_present": policy,
        "linguistic_predictive_gate_in_makefile": gate,
        "linguistic_predictive_cycle_in_makefile": cycle,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
