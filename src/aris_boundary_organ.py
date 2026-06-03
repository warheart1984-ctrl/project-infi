"""ARIS Boundary Organ — read-only embedded ARIS non-copy enforcement posture."""

# Mythic: Aris Boundary Organ
# Engineering: ArisBoundaryEngine
from __future__ import annotations

from typing import Any

from src.aris_integration import (
    ARIS_CONTRACT_VERSION,
    ARIS_RUNTIME_PROFILE,
    build_aris_enforcement,
)

MODULE_ID = "AAIS-ARIS-01"
ORGAN_VERSION = "aris_boundary_organ.v1"


def build_aris_boundary_status(
    *,
    share_mode: str = "local_only",
) -> dict[str, Any]:
    """Bounded ARIS boundary snapshot for governance surfaces."""
    enforcement = build_aris_enforcement(details={"pattern_share_mode": share_mode})
    clause = enforcement.get("non_copy_clause") or {}
    allowed = bool(clause.get("allowed"))
    summary = (
        f"profile={ARIS_RUNTIME_PROFILE};share={clause.get('share_mode', 'local_only')};"
        f"allowed={allowed}"
    )[:128]
    return {
        "aris_boundary_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "aris_contract_version": ARIS_CONTRACT_VERSION,
        "runtime_profile": ARIS_RUNTIME_PROFILE,
        "standalone_service": False,
        "share_mode": str(clause.get("share_mode") or "local_only")[:32],
        "non_copy_allowed": allowed,
        "non_copy_status": str(clause.get("status") or "enforced")[:32],
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
