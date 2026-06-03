"""Module Governance Organ — read-only module governance controller posture."""

# Mythic: Module Governance Organ
# Engineering: ModuleGovernanceEngine
from __future__ import annotations

from typing import Any

MODULE_ID = "AAIS-MGO-01"
ORGAN_VERSION = "module_governance_organ.v1"


def build_module_governance_status() -> dict[str, Any]:
    from src.module_entry_gate import build_module_entry_gate_status
    from src.module_governance import module_governance

    controller = module_governance
    status = "idle"
    try:
        report = controller.snapshot()
        status = str(report.get("controller_status") or report.get("status") or "idle")[:64]
    except Exception:
        status = "idle"
    entry_gate = build_module_entry_gate_status()
    coverage_ratio = float(entry_gate.get("entry_coverage_ratio") or 0.0)
    universal_entry = bool(entry_gate.get("universal_entry_coverage"))
    summary = (
        f"status={status};entry_cov={coverage_ratio:.2f};universal={int(universal_entry)}"
    )[:128]
    return {
        "module_governance_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "controller_status": status,
        "major_violation_disable_module": True,
        "universal_entry_coverage": universal_entry,
        "entry_coverage_ratio": coverage_ratio,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
