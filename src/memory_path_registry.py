"""Registry of memory path families and board-governed alignment."""

from __future__ import annotations

from typing import Any

# Paths routed through MemoryBoardEnforcer (live runtime).
BOARD_GOVERNED_PATHS: tuple[str, ...] = (
    "jarvis_memory_board.install",
    "jarvis_memory_board.snapshot",
    "memory_smith.curate",
    "memory_board_enforcer.read",
    "memory_board_enforcer.mutate",
    "conversation_memory.write",
    "conversation_memory.session_metadata",
    "conversation_memory.read_filter",
    "mission_board.attach_memory",
    "knowledge_authority.snapshot",
    "api.jarvis_memory_routes",
    "jarvis_operator.memory_promotion",
    "dreamspace.reflection_write",
)

# Retired legacy paths — kept for audit only; must remain empty when aligned.
LEGACY_PATHS: tuple[str, ...] = ()

_ALIGNMENT_THRESHOLD = 1.0


def memory_paths_aligned(*, board_slots_installed: int, board_slots_total: int) -> bool:
    """True when active board slots are fully installed and no legacy bypass paths remain."""
    if board_slots_total <= 0:
        return False
    if LEGACY_PATHS:
        return False
    coverage = board_slots_installed / board_slots_total
    return coverage >= _ALIGNMENT_THRESHOLD


def build_memory_path_registry_snapshot(
    *,
    board_slots_installed: int = 0,
    board_slots_total: int = 0,
) -> dict[str, Any]:
    aligned = memory_paths_aligned(
        board_slots_installed=board_slots_installed,
        board_slots_total=board_slots_total,
    )
    return {
        "board_governed_paths": list(BOARD_GOVERNED_PATHS),
        "legacy_paths": [] if aligned else list(LEGACY_PATHS),
        "memory_paths_aligned": aligned,
        "coverage_ratio": (
            board_slots_installed / board_slots_total if board_slots_total else 0.0
        ),
    }
