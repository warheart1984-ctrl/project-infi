"""Linguistic Governance Day Subsystem — Wave 17 operator day orchestrator."""

# Mythic: Linguistic Governance Day Organ
# Engineering: LinguisticGovernanceDayEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LGD-01"
ORGAN_VERSION = "linguistic_governance_day_organ.v1"


def build_linguistic_governance_day_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    day_dir = root / "governance" / "linguistic_governance_days"
    count = len(list(day_dir.glob("*.v1.json"))) if day_dir.is_dir() else 0
    engine = (
        root / "src" / "governance_organs" / "linguistic_governance_day_engine.py"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    return {
        "linguistic_governance_day_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"days={count};engine={int(engine)}"[:128],
        "governance_day_dir_present": day_dir.is_dir(),
        "governance_day_artifact_count": count,
        "day_engine_present": engine,
        "linguistic_governance_day_in_makefile": (
            "linguistic-governance-day:" in m_text
        ),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
