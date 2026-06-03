"""Governed memory-lane capability adapter for the service bridge."""

from __future__ import annotations

from typing import Any

from src.capability_module import AAISCapabilityModule

MEMORY_LANE_COMPONENT_ID = "jarvis.capability.memory_lane"


class MemoryLaneCapability(AAISCapabilityModule):
    module_name = "memory_lane"
    supported_actions = frozenset({"list", "get", "snapshot"})

    def __init__(self, *, memory_enforcer: Any) -> None:
        super().__init__(provider_name="aais_memory")
        self._memory_enforcer = memory_enforcer
        self.handlers = {
            "list": self._handle_list,
            "get": self._handle_get,
            "snapshot": self._handle_snapshot,
        }

    def _handle_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        memories = self._memory_enforcer.list_memories(
            query=payload.get("query"),
            limit=int(payload.get("limit") or 6),
            active=bool(payload.get("active", True)),
            runtime_context=str(payload.get("runtime_context") or "operator_runtime"),
        )
        return self._ok("list", {"memories": memories})

    def _handle_get(self, payload: dict[str, Any]) -> dict[str, Any]:
        memory_id = str(payload.get("memory_id") or "").strip()
        if not memory_id:
            return self._err("get", "InputError", "memory_id is required")
        memory = self._memory_enforcer.get_memory(
            memory_id,
            runtime_context=str(payload.get("runtime_context") or "operator_runtime"),
        )
        return self._ok("get", {"memory": memory})

    def _handle_snapshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot = self._memory_enforcer.get_memory_board_snapshot(
            runtime_context=str(payload.get("runtime_context") or "operator_runtime"),
        )
        return self._ok("snapshot", {"board": snapshot})
