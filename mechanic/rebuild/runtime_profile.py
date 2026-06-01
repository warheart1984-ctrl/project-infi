"""MECHANIC_RUNTIME_PROFILE.json builder."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

PROFILE_VERSION = "mechanic.runtime_profile.v1"


def build_runtime_profile(
    *,
    case_id: str,
    drifts: list[dict[str, Any]],
    genome: dict[str, Any],
) -> dict[str, Any]:
    codes = sorted({str(d.get("code") or "") for d in drifts})
    families = sorted({str(d.get("family") or "") for d in drifts if d.get("family")})
    model_paths = [
        str(n.get("source_path") or "")
        for n in genome.get("nodes") or []
        if str(n.get("type")) == "model_call"
    ]
    return {
        "profile_version": PROFILE_VERSION,
        "case_id": case_id,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "safety_state": "dry_run_only",
        "enforcement": {
            "allowed_action_set": ["read", "propose", "validate"],
            "blocked_modes": ["apply"],
            "require_audit_fields": ["trace_id", "case_id"],
            "cost_ceiling": {"max_model_calls_per_turn": 3},
        },
        "active_invariants": codes,
        "families_triggered": families,
        "monitored_paths": model_paths[:20],
        "claim_label": "asserted",
    }
