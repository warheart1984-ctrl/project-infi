"""Forge Contractor Organ — read-only isolated Forge contractor lane posture."""

# Mythic: Forge Contractor Organ
# Engineering: ForgeContractorEngine
from __future__ import annotations

from typing import Any

from src.forge_client import VALID_KINDS, forge_client

MODULE_ID = "AAIS-FCO-01"
ORGAN_VERSION = "forge_contractor_organ.v1"


def build_forge_contractor_status() -> dict[str, Any]:
    reachable = False
    health_claim = "asserted"
    health_error = ""
    try:
        health = forge_client.health()
        reachable = bool(health)
        health_claim = str(health.get("claim_label") or "asserted")
    except Exception as exc:
        health_error = str(exc)[:120]

    summary = (
        f"reachable={int(reachable)};proposal_only=1;base={forge_client.base_url}"
    )[:128]
    return {
        "forge_contractor_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "base_url": forge_client.base_url,
        "service_reachable": reachable,
        "valid_kinds": sorted(VALID_KINDS),
        "proposal_only": True,
        "auto_approve_allowed": False,
        "health_claim_label": health_claim,
        "health_error": health_error or None,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
