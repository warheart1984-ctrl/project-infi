"""AAIS UL Substrate Organ — envelope attachment posture."""

from __future__ import annotations

from typing import Any

from src.aais_ul_substrate import SUBSTRATE_CONTRACT_VERSION, SUBSTRATE_ID

MODULE_ID = "AAIS-ULS-01"
ORGAN_VERSION = "aais_ul_substrate_organ.v1"


def build_aais_ul_substrate_status() -> dict[str, Any]:
    summary = f"substrate={SUBSTRATE_ID};contract={SUBSTRATE_CONTRACT_VERSION};read_only=1"[:128]
    return {
        "aais_ul_substrate_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "substrate_id": SUBSTRATE_ID,
        "contract_version": SUBSTRATE_CONTRACT_VERSION,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
