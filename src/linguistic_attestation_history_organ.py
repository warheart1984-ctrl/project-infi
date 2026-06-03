"""Linguistic Attestation History Subsystem — attestation cycle retention."""

# Mythic: Linguistic Attestation History Organ
# Engineering: LinguisticAttestationHistoryEngine
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LAH-01"
ORGAN_VERSION = "linguistic_attestation_history_organ.v1"


def build_linguistic_attestation_history_status(
    *, root: Path | None = None
) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    from src.governance_organs.linguistic_governance_attestation_engine import (
        list_attestation_cycles,
    )

    cycles = list_attestation_cycles(root)
    cycle_dir = root / "governance" / "linguistic_attestation_cycles"
    return {
        "linguistic_attestation_history_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"cycles={len(cycles)}"[:128],
        "attestation_cycles_dir_present": cycle_dir.is_dir(),
        "attestation_cycle_count": len(cycles),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
