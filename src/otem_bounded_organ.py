"""OTEM Bounded Organ — read-only OTEM capability ceiling posture."""

# Mythic: Otem Bounded Organ
# Engineering: OtemBoundedEngine
from __future__ import annotations

from typing import Any

from src.otem_capability import capability_posture
from src.otem_runtime import get_frozen_otem_version

MODULE_ID = "AAIS-OTEM-01"
ORGAN_VERSION = "otem_bounded_organ.v1"


def build_otem_bounded_status() -> dict[str, Any]:
    version = get_frozen_otem_version()
    posture = capability_posture()
    summary = (
        f"otem={version};lvl={posture['capability_level']};"
        f"proposal_only=1;exec_via_approvals={int(posture['execution_via_workflow_approvals'])}"
    )[:128]
    return {
        "otem_bounded_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "otem_runtime_version": version,
        "otem_capability_level": posture["capability_level"],
        "otem_max_capability_level": posture["max_capability_level"],
        "max_plan_steps": posture["max_plan_steps"],
        "proposal_only": True,
        "execution_allowed": False,
        "execution_via_workflow_approvals": posture["execution_via_workflow_approvals"],
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
