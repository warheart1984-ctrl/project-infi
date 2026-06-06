"""Governed action-lane capability adapter for approval/action lifecycle tools."""

# Mythic: Action Lane
# Engineering: ActionLane
from __future__ import annotations

from typing import Any

from src.capability_module import AAISCapabilityModule

ACTION_LANE_COMPONENT_ID = "jarvis.capability.action_lane"


class ActionLaneCapability(AAISCapabilityModule):
    module_name = "action_lane"
    supported_actions = frozenset({"status", "list_pending"})

    def __init__(self, *, governance_layer: Any) -> None:
        super().__init__(provider_name="aais_action")
        self._governance = governance_layer
        self.handlers = {
            "status": self._handle_status,
            "list_pending": self._handle_list_pending,
        }

    def _handle_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot = {}
        if hasattr(self._governance, "build_posture_snapshot"):
            snapshot = self._governance.build_posture_snapshot()
        return self._ok("status", {"governance": snapshot})

    def _handle_list_pending(self, payload: dict[str, Any]) -> dict[str, Any]:
        pending: list[dict[str, Any]] = []
        if hasattr(self._governance, "list_pending_actions"):
            pending = list(self._governance.list_pending_actions() or [])
        return self._ok("list_pending", {"pending": pending})
