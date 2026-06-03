"""Output Integrity Organ — output completion and corrigibility posture."""

from __future__ import annotations

from typing import Any

from src.corrigibility import default_corrigibility_state
from src.output_completion import TRUNCATION_NOTICE

MODULE_ID = "AAIS-OIO-01"
ORGAN_VERSION = "output_integrity_organ.v1"


def build_output_integrity_status() -> dict[str, Any]:
    state = default_corrigibility_state()
    summary = "completion=1;corrigibility=1;read_only=1"[:128]
    return {
        "output_integrity_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "truncation_notice_present": bool(TRUNCATION_NOTICE),
        "corrigibility_default_keys": sorted(state.keys()),
        "finalization_read_only": True,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
