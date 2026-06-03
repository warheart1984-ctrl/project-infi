"""ForgeEval Organ — read-only evaluator lane posture."""

# Mythic: Forge Eval Organ
# Engineering: ForgeEvalEngine
from __future__ import annotations

from typing import Any

from src.forge_eval_client import VALID_MODES, forge_eval_client

MODULE_ID = "AAIS-FEO-01"
ORGAN_VERSION = "forge_eval_organ.v1"


def build_forge_eval_status() -> dict[str, Any]:
    reachable = False
    health_error = ""
    try:
        health = forge_eval_client.health()
        reachable = bool(health)
    except Exception as exc:
        health_error = str(exc)[:120]

    summary = (
        f"reachable={int(reachable)};modes={len(VALID_MODES)};base={forge_eval_client.base_url}"
    )[:128]
    return {
        "forge_eval_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "base_url": forge_eval_client.base_url,
        "service_reachable": reachable,
        "valid_modes": sorted(VALID_MODES),
        "health_error": health_error or None,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
