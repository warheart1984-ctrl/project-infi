"""Evolve Engine Organ — read-only bounded mutation lane posture."""

# Mythic: Evolve Engine Organ
# Engineering: EvolveEngineEngine
from __future__ import annotations

from typing import Any

from src.evolve_client import VALID_EVALUATION_MODES, evolve_client

MODULE_ID = "AAIS-EEO-01"
ORGAN_VERSION = "evolve_engine_organ.v1"


def build_evolve_engine_status() -> dict[str, Any]:
    reachable = False
    health_error = ""
    try:
        health = evolve_client.health()
        reachable = bool(health)
    except Exception as exc:
        health_error = str(exc)[:120]

    summary = (
        f"reachable={int(reachable)};special_review=1;base={evolve_client.base_url}"
    )[:128]
    return {
        "evolve_engine_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "base_url": evolve_client.base_url,
        "service_reachable": reachable,
        "valid_evaluation_modes": sorted(VALID_EVALUATION_MODES),
        "direct_patch_authority": False,
        "special_review_only": True,
        "health_error": health_error or None,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
