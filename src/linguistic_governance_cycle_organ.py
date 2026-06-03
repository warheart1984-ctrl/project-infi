"""Linguistic Governance Cycle Subsystem — Wave 11 self-optimizing cycle posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LGC-01"
ORGAN_VERSION = "linguistic_governance_cycle_organ.v1"


def build_linguistic_governance_cycle_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_governance_cycle_engine.py"
    ).is_file()
    runner = (
        root / "tools" / "governance" / "run_linguistic_governance_cycle.py"
    ).is_file()
    policy = (
        root / "governance" / "linguistic_governance_cycle_policy.v1.json"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "linguistic-governance-cycle-gate:" in m_text
    cycle = "linguistic-governance-cycle:" in m_text
    return {
        "linguistic_governance_cycle_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};runner={int(runner)};gate={int(gate)}"[:128],
        "governance_cycle_engine_present": engine,
        "governance_cycle_runner_present": runner,
        "governance_cycle_policy_present": policy,
        "linguistic_governance_cycle_gate_in_makefile": gate,
        "linguistic_governance_cycle_in_makefile": cycle,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
