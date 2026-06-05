"""Governed forge-lane capability adapter for PatchForge / forge routing."""

# Engineering: ForgeLaneEngine
from __future__ import annotations

from typing import Any

from src.capability_module import AAISCapabilityModule

FORGE_LANE_COMPONENT_ID = "jarvis.capability.forge_lane"


class ForgeLaneCapability(AAISCapabilityModule):
    module_name = "forge_lane"
    supported_actions = frozenset({"status", "propose"})

    def __init__(self, *, patchforge: Any) -> None:
        super().__init__(provider_name="aais_forge")
        self._patchforge = patchforge
        self.handlers = {
            "status": self._handle_status,
            "propose": self._handle_propose,
        }

    def _handle_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.patchforge_organ import build_patchforge_status

        return self._ok("status", {"patchforge": build_patchforge_status()})

    def _handle_propose(self, payload: dict[str, Any]) -> dict[str, Any]:
        problem = str(payload.get("problem") or payload.get("text") or "").strip()
        if not problem:
            return self._err("propose", "InputError", "problem text is required")
        if not hasattr(self._patchforge, "build_plan"):
            return self._err("propose", "ExecutionError", "patchforge unavailable")
        plan = self._patchforge.build_plan(problem)
        return self._ok("propose", {"plan": plan, "proposal_only": True})
