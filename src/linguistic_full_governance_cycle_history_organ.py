"""Linguistic Full Governance Cycle History Subsystem — cycle artifact retention."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LFCH-01"
ORGAN_VERSION = "linguistic_full_governance_cycle_history_organ.v1"


def build_linguistic_full_governance_cycle_history_status(
    *, root: Path | None = None
) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    hist_dir = root / "governance" / "linguistic_full_governance_cycles"
    count = len(list(hist_dir.glob("*.v1.json"))) if hist_dir.is_dir() else 0
    engine = (
        root
        / "src"
        / "governance_organs"
        / "linguistic_full_governance_cycle_engine.py"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    return {
        "linguistic_full_governance_cycle_history_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"history={count};engine={int(engine)}"[:128],
        "full_cycle_history_dir_present": hist_dir.is_dir(),
        "full_cycle_history_artifact_count": count,
        "full_cycle_engine_present": engine,
        "linguistic_full_governance_cycle_in_makefile": (
            "linguistic-full-governance-cycle:" in m_text
        ),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
