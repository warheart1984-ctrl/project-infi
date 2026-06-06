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
    forge_eval_reachable = None
    live_health: dict[str, Any] = {}
    try:
        live_health = evolve_client.health() or {}
        reachable = bool(live_health)
        forge_eval_reachable = live_health.get("forge_eval_reachable")
    except Exception as exc:
        health_error = str(exc)[:120]

    summary = (
        f"reachable={int(reachable)};forge_eval={int(bool(forge_eval_reachable))};base={evolve_client.base_url}"
    )[:128]
    return {
        "evolve_engine_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "base_url": evolve_client.base_url,
        "service_reachable": reachable,
        "forge_eval_reachable": forge_eval_reachable,
        "valid_evaluation_modes": sorted(VALID_EVALUATION_MODES),
        "direct_patch_authority": False,
        "special_review_only": True,
        "health_error": health_error or None,
        "live_health": {k: v for k, v in live_health.items() if k in ("status", "forge_eval_reachable", "forge_eval_error")},
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
