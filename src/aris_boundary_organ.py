"""ARIS Boundary Organ — read-only embedded ARIS non-copy enforcement posture."""

# Mythic: Aris Boundary Organ
# Engineering: ArisBoundaryEngine
from __future__ import annotations

from typing import Any

from src.aris_integration import (
    ARIS_CONTRACT_VERSION,
    ARIS_RUNTIME_PROFILE,
)
from src.aris_service_client import evaluate_aris_admission

MODULE_ID = "AAIS-ARIS-01"
ORGAN_VERSION = "aris_boundary_organ.v1"


def build_aris_boundary_status(
    *,
    share_mode: str = "local_only",
) -> dict[str, Any]:
    """Bounded ARIS boundary snapshot for governance surfaces."""
    from src.aris_service_client import aris_standalone_enabled, build_aris_client_status

    enforcement = evaluate_aris_admission(details={"pattern_share_mode": share_mode})
    client = build_aris_client_status()
    clause = enforcement.get("non_copy_clause") or {}
    allowed = bool(clause.get("allowed"))
    standalone = aris_standalone_enabled()
    summary = (
        f"profile={ARIS_RUNTIME_PROFILE};share={clause.get('share_mode', 'local_only')};"
        f"allowed={allowed};standalone={standalone}"
    )[:128]
    return {
        "aris_boundary_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "aris_contract_version": ARIS_CONTRACT_VERSION,
        "runtime_profile": ARIS_RUNTIME_PROFILE,
        "standalone_service": standalone,
        "aris_mode": client.get("mode"),
        "share_mode": str(clause.get("share_mode") or "local_only")[:32],
        "non_copy_allowed": allowed,
        "non_copy_status": str(clause.get("status") or "enforced")[:32],
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
