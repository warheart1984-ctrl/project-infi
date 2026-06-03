"""Memory Path Governance Organ — board vs legacy memory path coverage."""

# Mythic: Memory Path Governance Organ
# Engineering: MemoryPathGovernanceEngine
from __future__ import annotations

from typing import Any

from src.jarvis_memory_board import build_default_memory_controller, build_memory_board_snapshot

MODULE_ID = "AAIS-MPG-01"
ORGAN_VERSION = "memory_path_governance_organ.v1"

# Documented path families (read-only coverage map).
BOARD_GOVERNED_PATHS = (
    "jarvis_memory_board.install",
    "jarvis_memory_board.snapshot",
    "memory_smith.curate",
)
LEGACY_PATHS = (
    "conversation_memory.write",
    "conversation_memory.read_filter",
    "mission_board.attach_memory",
)


def build_memory_path_governance_status() -> dict[str, Any]:
    """Report which memory paths are board-governed vs legacy in v1."""
    controller = build_default_memory_controller()
    board = build_memory_board_snapshot(controller)
    slots = list(board.get("slots") or [])
    installed = sum(1 for slot in slots if slot.get("installed"))
    total_slots = len(slots)
    coverage_ratio = installed / total_slots if total_slots else 0.0
    all_paths_aligned = False  # deferred: not every memory write uses the board yet
    summary = (
        f"board_slots={installed}/{total_slots};"
        f"coverage={coverage_ratio:.2f};aligned={all_paths_aligned}"
    )[:128]
    return {
        "memory_path_governance_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "board_governed_paths": list(BOARD_GOVERNED_PATHS),
        "legacy_paths": list(LEGACY_PATHS),
        "board_slots_installed": installed,
        "board_slots_total": total_slots,
        "memory_paths_aligned": all_paths_aligned,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
