"""Wonder status surface for API and posture snapshots."""

from __future__ import annotations

from typing import Any

from src.otem_capability import authority_band, get_otem_capability_level
from src.wonder.gate import wonder_mode_for_level

WONDER_STATUS_MODULE_ID = "aais.wonder.status"


def wonder_status(level: int | None = None) -> dict[str, Any]:
    resolved = get_otem_capability_level() if level is None else int(level)
    mode = wonder_mode_for_level(resolved)
    return {
        "module_id": WONDER_STATUS_MODULE_ID,
        "wonder_mode": mode,
        "otem_level": resolved,
        "authority_band": authority_band(resolved),
        "contract": "docs/contracts/WONDER_CONTRACT.md",
        "schema": "schemas/wonder_gate.v1.json",
        "forbidden_categories": [
            "meta_constitutional_breach",
            "authority_usurpation",
            "immune_bypass_imagination",
            "ceiling_expansion_fantasy",
            "epistemic_unsafe_exploration",
        ],
    }
