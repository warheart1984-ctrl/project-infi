"""Linguistic Remediation Subsystem — drift remediation playbook posture."""

# Mythic: Linguistic Remediation Organ
# Engineering: LinguisticRemediationEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LRM-01"
ORGAN_VERSION = "linguistic_remediation_organ.v1"


def build_linguistic_remediation_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_remediation_engine.py"
    ).is_file()
    rem_dir = root / "governance" / "linguistic_remediations"
    rem_count = len(list(rem_dir.glob("*.json"))) if rem_dir.is_dir() else 0
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "linguistic-remediation-gate:" in m_text
    return {
        "linguistic_remediation_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};playbooks={rem_count}"[:128],
        "linguistic_remediation_engine_present": engine,
        "remediation_playbook_count": rem_count,
        "linguistic_remediation_gate_in_makefile": gate,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
