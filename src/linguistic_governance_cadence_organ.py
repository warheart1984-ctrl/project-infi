"""Linguistic Governance Cadence Subsystem — SLA cadence policy posture."""

# Mythic: Linguistic Governance Cadence Organ
# Engineering: LinguisticGovernanceCadenceEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LCD-01"
ORGAN_VERSION = "linguistic_governance_cadence_organ.v1"


def build_linguistic_governance_cadence_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    policy = (
        root / "governance" / "linguistic_governance_cadence_policy.v1.json"
    ).is_file()
    att_gate = (
        root / "tools" / "governance" / "check_linguistic_attestation_gate.py"
    ).is_file()
    wo_gate = (
        root / "tools" / "governance" / "check_linguistic_work_order_gate.py"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    return {
        "linguistic_governance_cadence_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"policy={int(policy)};gates={int(att_gate and wo_gate)}"[:128],
        "cadence_policy_present": policy,
        "attestation_cadence_gate_present": att_gate,
        "work_order_cadence_gate_present": wo_gate,
        "linguistic_attestation_gate_in_makefile": (
            "linguistic-attestation-gate:" in m_text
        ),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
