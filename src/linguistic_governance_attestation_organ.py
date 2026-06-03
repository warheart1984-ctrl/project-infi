"""Linguistic Governance Attestation Subsystem — Wave 14 attested closed-loop."""

# Mythic: Linguistic Governance Attestation Organ
# Engineering: LinguisticGovernanceAttestationEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LGA-01"
ORGAN_VERSION = "linguistic_governance_attestation_organ.v1"


def build_linguistic_governance_attestation_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_governance_attestation_engine.py"
    ).is_file()
    cadence = (
        root / "governance" / "linguistic_governance_cadence_policy.v1.json"
    ).is_file()
    att = (root / "governance" / "linguistic_governance_attestation.v1.json").is_file()
    score = 0
    if att:
        import json

        data = json.loads(
            (root / "governance" / "linguistic_governance_attestation.v1.json").read_text(
                encoding="utf-8"
            )
        )
        score = int(data.get("closed_loop_score", 0))
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    return {
        "linguistic_governance_attestation_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};att={int(att)};score={score}"[:128],
        "attestation_engine_present": engine,
        "cadence_policy_present": cadence,
        "attestation_report_present": att,
        "closed_loop_score": score,
        "linguistic_governance_attestation_in_makefile": (
            "linguistic-governance-attestation:" in m_text
        ),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
