"""Memory Path Governance Organ — board vs legacy memory path coverage."""

# Mythic: Memory Path Governance Organ
# Engineering: MemoryPathGovernanceEngine
from __future__ import annotations

from typing import Any

from src.jarvis_memory_board import build_default_memory_controller, build_memory_board_snapshot
from src.memory_path_registry import build_memory_path_registry_snapshot

MODULE_ID = "AAIS-MPG-01"
ORGAN_VERSION = "memory_path_governance_organ.v1"

BOARD_GOVERNED_PATHS = (
    "jarvis_memory_board.install",
    "jarvis_memory_board.snapshot",
    "memory_smith.curate",
    "memory_board_enforcer.read",
    "memory_board_enforcer.mutate",
    "knowledge_authority.snapshot",
    "api.jarvis_memory_routes",
    "jarvis_operator.memory_promotion",
    "mission_board.attach_memory",
)


def build_memory_path_governance_status() -> dict[str, Any]:
    """Report which memory paths are board-governed vs legacy."""
    controller = build_default_memory_controller()
    board = build_memory_board_snapshot(controller)
    slots = list(board.get("slots") or [])
    active_slots = [slot for slot in slots if slot.get("active", True)]
    installed = sum(1 for slot in active_slots if slot.get("installed"))
    total_slots = len(active_slots)
    registry = build_memory_path_registry_snapshot(
        board_slots_installed=installed,
        board_slots_total=total_slots,
    )
    all_paths_aligned = bool(registry.get("memory_paths_aligned"))
    coverage_ratio = float(registry.get("coverage_ratio") or 0.0)
    summary = (
        f"board_slots={installed}/{total_slots};"
        f"coverage={coverage_ratio:.2f};aligned={all_paths_aligned}"
    )[:128]
    return {
        "memory_path_governance_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "board_governed_paths": list(BOARD_GOVERNED_PATHS),
        "legacy_paths": list(registry.get("legacy_paths") or []),
        "board_slots_installed": installed,
        "board_slots_total": total_slots,
        "memory_paths_aligned": all_paths_aligned,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
