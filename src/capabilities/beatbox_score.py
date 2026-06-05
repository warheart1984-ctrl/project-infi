"""Beatbox downstream lane capability adapter."""

# Engineering: BeatboxScoreEngine
from __future__ import annotations

from typing import Any

from src.capability_module import AAISCapabilityModule

BEATBOX_LANE_COMPONENT_ID = "jarvis.capability.beatbox_score"


class BeatboxScoreCapability(AAISCapabilityModule):
    module_name = "beatbox_score"
    supported_actions = frozenset({"score", "status"})

    def __init__(self) -> None:
        super().__init__(provider_name="aais_beatbox")
        self.handlers = {"score": self._handle_score, "status": self._handle_status}

    def _handle_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.beatbox_lane_organ import build_beatbox_lane_status

        return self._ok("status", {"lane": build_beatbox_lane_status(), "standalone_lane": True})

    def _handle_score(self, payload: dict[str, Any]) -> dict[str, Any]:
        timing = payload.get("timing") or {}
        return self._ok(
            "score",
            {
                "cue_plan": {"timing": timing, "status": "governed_posture"},
                "standalone_lane": True,
            },
        )
