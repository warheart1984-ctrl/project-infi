"""RLS status surface for API and posture snapshots."""

from __future__ import annotations

from typing import Any

from src.otem_capability import authority_band, get_otem_capability_level
from src.rls.quarantine import recent_quarantine_count, recent_quarantine_events
from src.rls.substrate import rls_mode_for_level

RLS_STATUS_MODULE_ID = "aais.rls.status"


def rls_status(level: int | None = None) -> dict[str, Any]:
    resolved = get_otem_capability_level() if level is None else int(level)
    mode = rls_mode_for_level(resolved)
    return {
        "module_id": RLS_STATUS_MODULE_ID,
        "rls_mode": mode,
        "otem_level": resolved,
        "authority_band": authority_band(resolved),
        "quarantine_count_recent": recent_quarantine_count(limit=100),
        "recent_quarantine": recent_quarantine_events(limit=5),
        "contract": "docs/contracts/RLS_CONTRACT.md",
        "schema": "schemas/reasoning_logic_substrate.v1.json",
    }
