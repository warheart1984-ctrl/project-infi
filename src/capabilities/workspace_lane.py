"""Governed workspace-lane capability adapter for the service bridge."""

from __future__ import annotations

from typing import Any

from src.capability_module import AAISCapabilityModule

WORKSPACE_LANE_COMPONENT_ID = "jarvis.capability.workspace_lane"


class WorkspaceLaneCapability(AAISCapabilityModule):
    module_name = "workspace_lane"
    supported_actions = frozenset({"list_projects", "profile"})

    def __init__(self, *, workspace_tools: Any, profile_detector: Any) -> None:
        super().__init__(provider_name="aais_workspace")
        self._workspace_tools = workspace_tools
        self._profile_detector = profile_detector
        self.handlers = {
            "list_projects": self._handle_list_projects,
            "profile": self._handle_profile,
        }

    def _handle_list_projects(self, payload: dict[str, Any]) -> dict[str, Any]:
        limit = int(payload.get("limit") or 8)
        projects = self._workspace_tools.list_projects(limit=limit)
        return self._ok("list_projects", {"projects": projects})

    def _handle_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        profile = self._profile_detector(path_prefix=payload.get("path_prefix"))
        return self._ok("profile", {"workspace_profile": profile})
